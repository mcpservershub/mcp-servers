"""Task management tools for spec-kit MCP server."""

import asyncio
import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from .base import BaseTool
from ..models import ToolResponse, TaskStatus
from ..exceptions import FileSystemError, ValidationError, ScriptExecutionError, TemplateProcessingError
from ..utils.scripts import ScriptRunner
from ..utils.templates import TemplateProcessor
from ..utils.git_ops import GitOperations
from ..config import Settings

logger = logging.getLogger(__name__)


class GenerateTasksTool(BaseTool):
    """Generate executable tasks from design documents."""

    async def execute(
        self,
        include_parallel_markers: bool = True,
        enforce_tdd: bool = True
    ) -> ToolResponse:
        """Generate executable tasks from design documents."""
        try:
            # Check if scripts are available
            if not self.settings.scripts_path or not self.settings.scripts_path.exists():
                # Fallback to manual creation
                return await self._manual_generate_tasks(include_parallel_markers, enforce_tdd)

            # Use spec-kit scripts
            script_runner = ScriptRunner(self.settings.scripts_path, self.settings.script_timeout)

            # Run check-task-prerequisites.sh script to get feature directory and available docs
            result = await script_runner.run_script(
                "check-task-prerequisites.sh",
                args=["--json"],
                json_output=True,
                cwd=self.settings.repo_path
            )

            feature_dir = result.get("FEATURE_DIR")
            available_docs = result.get("AVAILABLE_DOCS", [])

            if not feature_dir:
                raise ScriptExecutionError(
                    "Script did not return expected output",
                    details={"result": result}
                )

            feature_dir_path = Path(feature_dir)

            # Generate tasks based on available documents
            created_files = await self._generate_tasks_from_docs(
                feature_dir_path=feature_dir_path,
                available_docs=available_docs,
                include_parallel_markers=include_parallel_markers,
                enforce_tdd=enforce_tdd
            )

            return self.create_success_response(
                message=f"Generated tasks for feature in {feature_dir_path.name}",
                data={
                    "feature_dir": str(feature_dir_path),
                    "available_docs": available_docs,
                    "tasks_file": str(feature_dir_path / "tasks.md"),
                    "created_files": created_files
                },
                artifacts=[Path(f) for f in created_files]
            )

        except Exception as e:
            logger.error(f"Failed to generate tasks using scripts: {e}")
            # Try manual fallback
            return await self._manual_generate_tasks(include_parallel_markers, enforce_tdd)

    async def _manual_generate_tasks(
        self,
        include_parallel_markers: bool,
        enforce_tdd: bool
    ) -> ToolResponse:
        """Manually generate tasks without scripts."""
        git_ops = GitOperations(self.settings.repo_path)
        branch_name = await git_ops.get_current_branch()

        if not branch_name or branch_name in ["main", "master"]:
            raise ValidationError(
                "Not on a feature branch",
                suggestions=["Create a feature branch first using create_specification"]
            )

        # Get feature directory and validate plan exists
        feature_dir_path = self.get_feature_dir(branch_name)
        plan_file = self.get_plan_file(branch_name)

        if not plan_file.exists():
            raise ValidationError(
                f"Implementation plan not found: {plan_file}",
                suggestions=["Run create_plan first to create the implementation plan"]
            )

        # Check for available documents
        available_docs = []
        doc_files = {
            "research.md": feature_dir_path / "research.md",
            "data-model.md": feature_dir_path / "data-model.md",
            "quickstart.md": feature_dir_path / "quickstart.md"
        }

        for doc_name, doc_path in doc_files.items():
            if doc_path.exists():
                available_docs.append(doc_name)

        # Check for contracts directory
        contracts_dir = feature_dir_path / "contracts"
        if contracts_dir.exists() and any(contracts_dir.iterdir()):
            available_docs.append("contracts/")

        # Generate tasks based on available documents
        created_files = await self._generate_tasks_from_docs(
            feature_dir_path=feature_dir_path,
            available_docs=available_docs,
            include_parallel_markers=include_parallel_markers,
            enforce_tdd=enforce_tdd
        )

        return self.create_success_response(
            message=f"Generated tasks for feature {branch_name}",
            data={
                "feature_dir": str(feature_dir_path),
                "available_docs": available_docs,
                "tasks_file": str(feature_dir_path / "tasks.md"),
                "created_files": created_files
            },
            artifacts=[Path(f) for f in created_files]
        )

    async def _generate_tasks_from_docs(
        self,
        feature_dir_path: Path,
        available_docs: List[str],
        include_parallel_markers: bool,
        enforce_tdd: bool
    ) -> List[str]:
        """Generate tasks based on available design documents."""
        # Read plan.md to understand tech stack and structure
        plan_file = feature_dir_path / "plan.md"
        plan_content = plan_file.read_text()

        # Extract tech stack information from plan
        tech_info = self._extract_tech_info(plan_content)

        # Read available documents and extract task requirements
        docs_content = await self._read_available_docs(feature_dir_path, available_docs)

        # Generate tasks based on documents
        tasks_data = self._generate_task_data(
            docs_content=docs_content,
            tech_info=tech_info,
            include_parallel_markers=include_parallel_markers,
            enforce_tdd=enforce_tdd
        )

        # Create tasks.md file
        tasks_file = feature_dir_path / "tasks.md"

        # Use template processor if available
        if self.settings.templates_path and self.settings.templates_path.exists():
            template_processor = TemplateProcessor(self.settings.templates_path)

            if template_processor.template_exists("tasks-template.md"):
                template_processor.process_tasks_template(
                    branch_name=feature_dir_path.name,
                    tasks_data=tasks_data,
                    output_path=tasks_file
                )
            else:
                # Create basic tasks file
                tasks_content = self._create_basic_tasks(
                    feature_name=self._extract_feature_name(feature_dir_path.name),
                    tasks_data=tasks_data
                )
                tasks_file.write_text(tasks_content)
        else:
            # Create basic tasks file without templates
            tasks_content = self._create_basic_tasks(
                feature_name=self._extract_feature_name(feature_dir_path.name),
                tasks_data=tasks_data
            )
            tasks_file.write_text(tasks_content)

        return [str(tasks_file)]

    def _extract_tech_info(self, plan_content: str) -> Dict[str, Any]:
        """Extract technical information from plan.md."""
        tech_info = {
            "language": "python",  # default
            "framework": "unknown",
            "storage": None,
            "project_type": "single"
        }

        # Extract language
        language_match = re.search(r'\*\*Language/Version\*\*:\s*([^\n]+)', plan_content)
        if language_match:
            tech_info["language"] = language_match.group(1).strip().lower()

        # Extract framework
        framework_match = re.search(r'\*\*Primary Dependencies\*\*:\s*([^\n]+)', plan_content)
        if framework_match:
            tech_info["framework"] = framework_match.group(1).strip()

        # Extract storage
        storage_match = re.search(r'\*\*Storage\*\*:\s*([^\n]+)', plan_content)
        if storage_match and "N/A" not in storage_match.group(1):
            tech_info["storage"] = storage_match.group(1).strip()

        # Extract project type
        project_match = re.search(r'\*\*Project Type\*\*:\s*([^\n]+)', plan_content)
        if project_match:
            tech_info["project_type"] = project_match.group(1).strip().lower()

        return tech_info

    async def _read_available_docs(self, feature_dir_path: Path, available_docs: List[str]) -> Dict[str, str]:
        """Read content from available design documents."""
        docs_content = {}

        for doc in available_docs:
            if doc.endswith("/"):
                # Handle directories like contracts/
                doc_dir = feature_dir_path / doc.rstrip("/")
                if doc_dir.exists():
                    contracts = []
                    for contract_file in doc_dir.glob("*.md"):
                        contracts.append({
                            "file": contract_file.name,
                            "content": contract_file.read_text()
                        })
                    docs_content[doc] = contracts
            else:
                # Handle individual files
                doc_file = feature_dir_path / doc
                if doc_file.exists():
                    docs_content[doc] = doc_file.read_text()

        return docs_content

    def _generate_task_data(
        self,
        docs_content: Dict[str, Any],
        tech_info: Dict[str, Any],
        include_parallel_markers: bool,
        enforce_tdd: bool
    ) -> Dict[str, Any]:
        """Generate task data from documents and tech info."""
        tasks = []
        task_counter = 1

        # Phase 1: Setup tasks
        setup_tasks = self._generate_setup_tasks(tech_info, task_counter)
        tasks.extend(setup_tasks)
        task_counter += len(setup_tasks)

        # Phase 2: Test tasks (TDD enforcement)
        if enforce_tdd:
            test_tasks = self._generate_test_tasks(docs_content, task_counter, include_parallel_markers)
            tasks.extend(test_tasks)
            task_counter += len(test_tasks)

        # Phase 3: Core implementation tasks
        core_tasks = self._generate_core_tasks(docs_content, tech_info, task_counter, include_parallel_markers)
        tasks.extend(core_tasks)
        task_counter += len(core_tasks)

        # Phase 4: Integration tasks
        integration_tasks = self._generate_integration_tasks(tech_info, task_counter)
        tasks.extend(integration_tasks)
        task_counter += len(integration_tasks)

        # Phase 5: Polish tasks
        polish_tasks = self._generate_polish_tasks(task_counter, include_parallel_markers)
        tasks.extend(polish_tasks)

        return {
            "tasks": tasks,
            "tech_info": tech_info,
            "enforce_tdd": enforce_tdd,
            "include_parallel_markers": include_parallel_markers,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

    def _generate_setup_tasks(self, tech_info: Dict[str, Any], start_counter: int) -> List[Dict[str, Any]]:
        """Generate setup tasks."""
        tasks = []
        counter = start_counter

        tasks.append({
            "id": f"T{counter:03d}",
            "description": "Create project structure per implementation plan",
            "parallel": False,
            "phase": "Setup"
        })
        counter += 1

        language = tech_info.get("language", "python")
        framework = tech_info.get("framework", "unknown")

        tasks.append({
            "id": f"T{counter:03d}",
            "description": f"Initialize {language} project with {framework} dependencies",
            "parallel": False,
            "phase": "Setup"
        })
        counter += 1

        tasks.append({
            "id": f"T{counter:03d}",
            "description": "Configure linting and formatting tools",
            "parallel": True,
            "phase": "Setup"
        })

        return tasks

    def _generate_test_tasks(self, docs_content: Dict[str, Any], start_counter: int, include_parallel: bool) -> List[Dict[str, Any]]:
        """Generate test tasks from contracts and quickstart scenarios."""
        tasks = []
        counter = start_counter

        # Generate contract tests
        if "contracts/" in docs_content:
            contracts = docs_content["contracts/"]
            for contract in contracts:
                contract_name = contract["file"].replace(".md", "")
                tasks.append({
                    "id": f"T{counter:03d}",
                    "description": f"Contract test for {contract_name} in tests/contract/test_{contract_name}.py",
                    "parallel": include_parallel,
                    "phase": "Tests"
                })
                counter += 1

        # Generate integration tests from quickstart scenarios
        if "quickstart.md" in docs_content:
            quickstart_content = docs_content["quickstart.md"]
            scenarios = self._extract_test_scenarios(quickstart_content)
            for scenario in scenarios:
                tasks.append({
                    "id": f"T{counter:03d}",
                    "description": f"Integration test {scenario} in tests/integration/test_{scenario.lower().replace(' ', '_')}.py",
                    "parallel": include_parallel,
                    "phase": "Tests"
                })
                counter += 1

        return tasks

    def _generate_core_tasks(self, docs_content: Dict[str, Any], tech_info: Dict[str, Any], start_counter: int, include_parallel: bool) -> List[Dict[str, Any]]:
        """Generate core implementation tasks."""
        tasks = []
        counter = start_counter

        # Generate model tasks from data-model.md
        if "data-model.md" in docs_content:
            data_model_content = docs_content["data-model.md"]
            entities = self._extract_entities(data_model_content)
            for entity in entities:
                tasks.append({
                    "id": f"T{counter:03d}",
                    "description": f"{entity} model in src/models/{entity.lower()}.py",
                    "parallel": include_parallel,
                    "phase": "Core"
                })
                counter += 1

                # Add service for each entity
                tasks.append({
                    "id": f"T{counter:03d}",
                    "description": f"{entity}Service CRUD in src/services/{entity.lower()}_service.py",
                    "parallel": include_parallel,
                    "phase": "Core"
                })
                counter += 1

        # Generate endpoint tasks from contracts
        if "contracts/" in docs_content:
            contracts = docs_content["contracts/"]
            for contract in contracts:
                endpoints = self._extract_endpoints(contract["content"])
                for endpoint in endpoints:
                    tasks.append({
                        "id": f"T{counter:03d}",
                        "description": f"{endpoint['method']} {endpoint['path']} endpoint",
                        "parallel": False,  # Endpoints might depend on each other
                        "phase": "Core"
                    })
                    counter += 1

        return tasks

    def _generate_integration_tasks(self, tech_info: Dict[str, Any], start_counter: int) -> List[Dict[str, Any]]:
        """Generate integration tasks."""
        tasks = []
        counter = start_counter

        if tech_info.get("storage"):
            tasks.append({
                "id": f"T{counter:03d}",
                "description": "Connect services to database",
                "parallel": False,
                "phase": "Integration"
            })
            counter += 1

        # Add common integration tasks
        integration_items = [
            "Auth middleware",
            "Request/response logging",
            "Error handling and logging"
        ]

        for item in integration_items:
            tasks.append({
                "id": f"T{counter:03d}",
                "description": item,
                "parallel": False,
                "phase": "Integration"
            })
            counter += 1

        return tasks

    def _generate_polish_tasks(self, start_counter: int, include_parallel: bool) -> List[Dict[str, Any]]:
        """Generate polish tasks."""
        tasks = []
        counter = start_counter

        polish_items = [
            ("Unit tests for validation in tests/unit/test_validation.py", True),
            ("Performance tests (<200ms)", False),
            ("Update documentation", True),
            ("Remove code duplication", False),
            ("Run manual testing scenarios", False)
        ]

        for description, can_be_parallel in polish_items:
            tasks.append({
                "id": f"T{counter:03d}",
                "description": description,
                "parallel": include_parallel and can_be_parallel,
                "phase": "Polish"
            })
            counter += 1

        return tasks

    def _extract_test_scenarios(self, quickstart_content: str) -> List[str]:
        """Extract test scenarios from quickstart.md."""
        scenarios = []

        # Look for common test scenario patterns
        scenario_patterns = [
            r'##\s*([^\n]+)\s*[Ss]cenario',
            r'###\s*([^\n]+)\s*[Tt]est',
            r'\*\*([^*]+)\*\*.*test'
        ]

        for pattern in scenario_patterns:
            matches = re.findall(pattern, quickstart_content, re.IGNORECASE)
            scenarios.extend([match.strip() for match in matches])

        # Default scenarios if none found
        if not scenarios:
            scenarios = ["basic usage", "error handling"]

        return scenarios[:5]  # Limit to 5 scenarios

    def _extract_entities(self, data_model_content: str) -> List[str]:
        """Extract entity names from data-model.md."""
        entities = []

        # Look for entity headers
        entity_patterns = [
            r'###\s*([^\n]+)\s*[Ee]ntity',
            r'###\s*([A-Z][a-zA-Z]+)\s*$',
            r'##\s*([A-Z][a-zA-Z]+)\s*$'
        ]

        for pattern in entity_patterns:
            matches = re.findall(pattern, data_model_content)
            entities.extend([match.strip() for match in matches if match.strip()])

        # Clean up entity names
        cleaned_entities = []
        for entity in entities:
            # Remove "Entity" suffix and clean up
            clean_name = re.sub(r'\s+Entity$', '', entity, flags=re.IGNORECASE)
            clean_name = re.sub(r'[^a-zA-Z]', '', clean_name)
            if clean_name and clean_name[0].isupper():
                cleaned_entities.append(clean_name)

        # Default entity if none found
        if not cleaned_entities:
            cleaned_entities = ["User"]

        return list(set(cleaned_entities))  # Remove duplicates

    def _extract_endpoints(self, contract_content: str) -> List[Dict[str, str]]:
        """Extract API endpoints from contract content."""
        endpoints = []

        # Look for HTTP method and path patterns
        endpoint_patterns = [
            r'###\s*(GET|POST|PUT|DELETE|PATCH)\s+([^\n]+)',
            r'\*\*(GET|POST|PUT|DELETE|PATCH)\*\*\s+([^\n]+)'
        ]

        for pattern in endpoint_patterns:
            matches = re.findall(pattern, contract_content, re.IGNORECASE)
            for method, path in matches:
                endpoints.append({
                    "method": method.upper(),
                    "path": path.strip()
                })

        return endpoints

    def _create_basic_tasks(self, feature_name: str, tasks_data: Dict[str, Any]) -> str:
        """Create basic tasks content without template processing."""
        date = tasks_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        tasks = tasks_data.get("tasks", [])

        content = f"""# Tasks: {feature_name}
**Date**: {date}
**Input**: Design documents from feature directory

## Execution Flow
```
1. Load plan.md from feature directory
2. Load optional design documents (data-model.md, contracts/, research.md, quickstart.md)
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, endpoints
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially
6. Execute in dependency order
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

"""

        # Group tasks by phase
        phases = {}
        for task in tasks:
            phase = task.get("phase", "Other")
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(task)

        # Add tasks by phase
        phase_order = ["Setup", "Tests", "Core", "Integration", "Polish"]

        for phase in phase_order:
            if phase in phases:
                phase_num = phase_order.index(phase) + 1
                content += f"\n## Phase 3.{phase_num}: {phase}\n"

                if phase == "Tests" and tasks_data.get("enforce_tdd"):
                    content += "**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**\n"

                for task in phases[phase]:
                    parallel_marker = "[P] " if task.get("parallel") and tasks_data.get("include_parallel_markers") else ""
                    content += f"- [ ] {task['id']} {parallel_marker}{task['description']}\n"

        # Add dependencies section
        content += "\n## Dependencies\n"
        if tasks_data.get("enforce_tdd"):
            content += "- Tests before implementation (TDD enforcement)\n"
        content += "- Setup before all other phases\n"
        content += "- Core before Integration\n"
        content += "- Integration before Polish\n"

        # Add parallel execution example
        if tasks_data.get("include_parallel_markers"):
            parallel_tasks = [task for task in tasks if task.get("parallel")]
            if parallel_tasks:
                content += "\n## Parallel Example\n```\n"
                for task in parallel_tasks[:3]:  # Show first 3 parallel tasks
                    content += f'Task: "{task["description"]}"\n'
                content += "```\n"

        content += "\n## Notes\n"
        content += "- [P] tasks = different files, no dependencies\n"
        if tasks_data.get("enforce_tdd"):
            content += "- Verify tests fail before implementing\n"
        content += "- Commit after each task\n"
        content += "- Avoid: vague tasks, same file conflicts\n"

        return content

    def _extract_feature_name(self, branch_name: str) -> str:
        """Extract feature name from branch name."""
        # Remove number prefix (e.g., "001-my-feature" -> "My Feature")
        parts = branch_name.split('-', 1)
        if len(parts) > 1:
            return parts[1].replace('-', ' ').title()
        return branch_name.replace('-', ' ').title()


class UpdateTaskStatusTool(BaseTool):
    """Update task status in tasks.md file."""

    async def execute(
        self,
        task_id: str,
        status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ToolResponse:
        """Update task status."""
        # Validate task_id format
        if not re.match(r'^T\d{3}$', task_id):
            raise ValidationError(
                f"Invalid task_id format: {task_id}",
                suggestions=["Use format like T001, T002, etc."]
            )

        # Validate status if provided
        if status and status not in [s.value for s in TaskStatus]:
            raise ValidationError(
                f"Invalid status: {status}",
                suggestions=[f"Use one of: {', '.join([s.value for s in TaskStatus])}"]
            )

        # Get current branch and tasks file
        git_ops = GitOperations(self.settings.repo_path)
        branch_name = await git_ops.get_current_branch()

        if not branch_name or branch_name in ["main", "master"]:
            raise ValidationError(
                "Not on a feature branch",
                suggestions=["Switch to a feature branch first"]
            )

        tasks_file = self.get_tasks_file(branch_name)

        if not tasks_file.exists():
            raise ValidationError(
                f"Tasks file not found: {tasks_file}",
                suggestions=["Run generate_tasks first to create tasks.md"]
            )

        # Read current tasks content
        tasks_content = tasks_file.read_text()

        # Find and update the task
        updated_content, task_found = self._update_task_in_content(
            tasks_content, task_id, status, notes
        )

        if not task_found:
            raise ValidationError(
                f"Task {task_id} not found in tasks.md",
                suggestions=["Check the task ID and try again"]
            )

        # Write updated content
        tasks_file.write_text(updated_content)

        # Calculate progress
        progress = self._calculate_progress(updated_content)

        return self.create_success_response(
            message=f"Updated task {task_id} status",
            data={
                "task_id": task_id,
                "status": status,
                "notes": notes,
                "tasks_file": str(tasks_file),
                "progress": progress
            },
            artifacts=[tasks_file]
        )

    def _update_task_in_content(
        self,
        content: str,
        task_id: str,
        status: Optional[str],
        notes: Optional[str]
    ) -> tuple[str, bool]:
        """Update task in content and return updated content and whether task was found."""
        lines = content.split('\n')
        task_found = False

        for i, line in enumerate(lines):
            # Look for task line pattern: - [ ] T001 [P] Description
            task_pattern = rf'- \[ \] {re.escape(task_id)}(\s+\[P\])?\s+(.+)'
            match = re.match(task_pattern, line.strip())

            if match:
                task_found = True
                parallel_marker = match.group(1) or ""
                description = match.group(2)

                # Update status
                if status:
                    if status == TaskStatus.COMPLETED:
                        checkbox = "[x]"
                    elif status == TaskStatus.IN_PROGRESS:
                        checkbox = "[~]"  # Custom marker for in-progress
                    elif status == TaskStatus.BLOCKED:
                        checkbox = "[!]"  # Custom marker for blocked
                    else:
                        checkbox = "[ ]"

                    lines[i] = f"- {checkbox} {task_id}{parallel_marker} {description}"

                # Add notes if provided
                if notes:
                    # Look for existing notes line
                    notes_line_index = i + 1
                    while notes_line_index < len(lines) and lines[notes_line_index].strip().startswith("  "):
                        if "Note:" in lines[notes_line_index]:
                            lines[notes_line_index] = f"  Note: {notes}"
                            break
                        notes_line_index += 1
                    else:
                        # Add new notes line
                        lines.insert(i + 1, f"  Note: {notes}")

                break

        return '\n'.join(lines), task_found

    def _calculate_progress(self, content: str) -> Dict[str, Any]:
        """Calculate task completion progress."""
        # Count different task statuses
        completed = len(re.findall(r'- \[x\] T\d{3}', content))
        in_progress = len(re.findall(r'- \[~\] T\d{3}', content))
        blocked = len(re.findall(r'- \[!\] T\d{3}', content))
        pending = len(re.findall(r'- \[ \] T\d{3}', content))

        total = completed + in_progress + blocked + pending

        if total == 0:
            percentage = 0
        else:
            percentage = round((completed / total) * 100, 1)

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "blocked": blocked,
            "pending": pending,
            "percentage_complete": percentage
        }


# Export tool functions
async def generate_tasks(
    include_parallel_markers: bool = True,
    enforce_tdd: bool = True,
    settings: Settings = None
) -> ToolResponse:
    """Generate executable tasks from design documents."""
    tool = GenerateTasksTool(settings)
    return await tool.execute(
        include_parallel_markers=include_parallel_markers,
        enforce_tdd=enforce_tdd
    )


async def update_task_status(
    task_id: str,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    settings: Settings = None
) -> ToolResponse:
    """Update task status in tasks.md file."""
    tool = UpdateTaskStatusTool(settings)
    return await tool.execute(
        task_id=task_id,
        status=status,
        notes=notes
    )