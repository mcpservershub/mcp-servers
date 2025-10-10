"""Context management tools for spec-kit MCP server."""

import asyncio
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from .base import BaseTool
from ..models import ToolResponse, AIAssistant
from ..exceptions import FileSystemError, ValidationError, ScriptExecutionError
from ..utils.scripts import ScriptRunner
from ..utils.git_ops import GitOperations
from ..config import Settings

logger = logging.getLogger(__name__)


class UpdateAgentContextTool(BaseTool):
    """Update AI agent context files (CLAUDE.md, GEMINI.md, copilot-instructions.md)."""

    async def execute(
        self,
        agent_type: str,
        technologies: Optional[Dict[str, str]] = None,
        recent_changes: Optional[List[str]] = None
    ) -> ToolResponse:
        """Update agent context files."""
        try:
            # Validate inputs
            validated_inputs = await self.validate_inputs(
                agent_type=agent_type,
                technologies=technologies or {},
                recent_changes=recent_changes or []
            )

            agent_type_enum = validated_inputs["agent_type"]
            technologies = validated_inputs["technologies"]
            recent_changes = validated_inputs["recent_changes"]

            # Check if scripts are available
            if not self.settings.scripts_path or not self.settings.scripts_path.exists():
                # Fallback to manual update
                return await self._manual_update_context(agent_type_enum, technologies, recent_changes)

            # Use spec-kit scripts
            script_runner = ScriptRunner(self.settings.scripts_path, self.settings.script_timeout)

            # Prepare script arguments
            script_args = [
                "--agent", agent_type_enum.value,
                "--json"
            ]

            if technologies:
                for tech, version in technologies.items():
                    script_args.extend(["--tech", f"{tech}:{version}"])

            if recent_changes:
                for change in recent_changes:
                    script_args.extend(["--change", change])

            # Run context update script
            result = await script_runner.run_script(
                "update-agent-context.sh",
                args=script_args,
                json_output=True,
                cwd=self.settings.repo_path
            )

            context_files = result.get("context_files", [])
            updated_sections = result.get("updated_sections", [])
            project_info = result.get("project_info", {})

            if not context_files:
                raise ScriptExecutionError(
                    "Script did not return expected output",
                    details={"result": result}
                )

            return self.create_success_response(
                message=f"Updated {agent_type_enum.value} context files",
                data={
                    "agent_type": agent_type_enum.value,
                    "context_files": context_files,
                    "updated_sections": updated_sections,
                    "project_info": project_info,
                    "technologies": technologies,
                    "recent_changes": recent_changes
                },
                artifacts=[Path(f) for f in context_files]
            )

        except Exception as e:
            logger.error(f"Failed to update context using scripts: {e}")
            # Try manual fallback
            return await self._manual_update_context(
                AIAssistant(agent_type) if isinstance(agent_type, str) else agent_type,
                technologies or {},
                recent_changes or []
            )

    async def validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize inputs."""
        agent_type = kwargs.get("agent_type", "").strip()
        technologies = kwargs.get("technologies", {})
        recent_changes = kwargs.get("recent_changes", [])

        if not agent_type:
            raise ValidationError("agent_type is required")

        # Validate agent_type
        try:
            agent_type_enum = AIAssistant(agent_type)
        except ValueError:
            valid_types = [t.value for t in AIAssistant]
            raise ValidationError(
                f"Invalid agent_type: {agent_type}",
                suggestions=[f"Use one of: {', '.join(valid_types)}"]
            )

        # Validate technologies
        if not isinstance(technologies, dict):
            raise ValidationError("technologies must be a dictionary")

        # Validate recent_changes
        if not isinstance(recent_changes, list):
            raise ValidationError("recent_changes must be a list")

        # Limit recent_changes to 10 items
        if len(recent_changes) > 10:
            recent_changes = recent_changes[:10]

        return {
            "agent_type": agent_type_enum,
            "technologies": technologies,
            "recent_changes": recent_changes
        }

    async def _manual_update_context(
        self,
        agent_type: AIAssistant,
        technologies: Dict[str, str],
        recent_changes: List[str]
    ) -> ToolResponse:
        """Manually update context without scripts."""
        # Analyze project to gather context
        project_info = await self._analyze_project()

        # Update context files based on agent type
        updated_files = []
        if agent_type == AIAssistant.CLAUDE:
            claude_file = await self._update_claude_context(project_info, technologies, recent_changes)
            updated_files.append(claude_file)
        elif agent_type == AIAssistant.GEMINI:
            gemini_file = await self._update_gemini_context(project_info, technologies, recent_changes)
            updated_files.append(gemini_file)
        elif agent_type == AIAssistant.COPILOT:
            copilot_file = await self._update_copilot_context(project_info, technologies, recent_changes)
            updated_files.append(copilot_file)

        # Also update the general agent context file
        general_file = await self._update_general_context(project_info, technologies, recent_changes)
        updated_files.append(general_file)

        return self.create_success_response(
            message=f"Updated {agent_type.value} context files",
            data={
                "agent_type": agent_type.value,
                "context_files": [str(f) for f in updated_files],
                "updated_sections": ["project_overview", "technologies", "recent_changes", "coding_standards"],
                "project_info": project_info,
                "technologies": technologies,
                "recent_changes": recent_changes
            },
            artifacts=updated_files
        )

    async def _analyze_project(self) -> Dict[str, Any]:
        """Analyze the project to gather context information."""
        project_info = {
            "name": self.settings.repo_path.name,
            "type": "unknown",
            "languages": [],
            "frameworks": [],
            "structure": {},
            "features": [],
            "testing_setup": {},
            "ci_cd": {}
        }

        # Analyze project structure
        project_info["structure"] = await self._analyze_structure()

        # Detect languages and frameworks
        project_info["languages"], project_info["frameworks"] = await self._detect_tech_stack()

        # Detect project type
        project_info["type"] = await self._detect_project_type(project_info["structure"])

        # Analyze features from specs directory
        project_info["features"] = await self._analyze_features()

        # Analyze testing setup
        project_info["testing_setup"] = await self._analyze_testing_setup()

        # Analyze CI/CD setup
        project_info["ci_cd"] = await self._analyze_ci_cd_setup()

        return project_info

    async def _analyze_structure(self) -> Dict[str, Any]:
        """Analyze project directory structure."""
        structure = {
            "directories": [],
            "config_files": [],
            "documentation": [],
            "source_dirs": []
        }

        repo_path = self.settings.repo_path

        # Common directories to look for
        common_dirs = [
            "src", "lib", "app", "components", "services", "utils", "models",
            "tests", "test", "__tests__", "spec", "specs",
            "docs", "documentation", "README",
            "config", "configuration", "settings",
            "scripts", "bin", "tools",
            "assets", "static", "public",
            "db", "database", "migrations"
        ]

        for dir_name in common_dirs:
            dir_path = repo_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                structure["directories"].append(dir_name)
                if dir_name in ["src", "lib", "app", "components", "services"]:
                    structure["source_dirs"].append(dir_name)

        # Common config files
        config_files = [
            "package.json", "requirements.txt", "Pipfile", "pyproject.toml", "setup.py",
            "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".gitignore", ".env", ".env.example",
            "Makefile", "justfile", "tsconfig.json", "webpack.config.js"
        ]

        for config_file in config_files:
            config_path = repo_path / config_file
            if config_path.exists():
                structure["config_files"].append(config_file)

        # Documentation files
        doc_files = ["README.md", "README.rst", "README.txt", "CHANGELOG.md", "CONTRIBUTING.md"]
        for doc_file in doc_files:
            doc_path = repo_path / doc_file
            if doc_path.exists():
                structure["documentation"].append(doc_file)

        return structure

    async def _detect_tech_stack(self) -> tuple[List[str], List[str]]:
        """Detect programming languages and frameworks."""
        languages = []
        frameworks = []

        repo_path = self.settings.repo_path

        # Language detection based on files
        language_indicators = {
            "Python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "JavaScript": ["package.json", "yarn.lock", "package-lock.json"],
            "TypeScript": ["tsconfig.json", "package.json"],
            "Rust": ["Cargo.toml", "Cargo.lock"],
            "Go": ["go.mod", "go.sum"],
            "Java": ["pom.xml", "build.gradle", "gradle.properties"],
            "C#": ["*.csproj", "*.sln"],
            "Ruby": ["Gemfile", "Gemfile.lock"]
        }

        for language, indicators in language_indicators.items():
            for indicator in indicators:
                if (repo_path / indicator).exists():
                    if language not in languages:
                        languages.append(language)
                    break

        # Framework detection
        if (repo_path / "package.json").exists():
            try:
                import json
                package_json = json.loads((repo_path / "package.json").read_text())
                dependencies = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}

                framework_indicators = {
                    "React": ["react", "@types/react"],
                    "Vue": ["vue", "@vue/cli"],
                    "Angular": ["@angular/core", "@angular/cli"],
                    "Express": ["express"],
                    "Next.js": ["next"],
                    "Nuxt": ["nuxt"],
                    "Svelte": ["svelte"]
                }

                for framework, deps in framework_indicators.items():
                    if any(dep in dependencies for dep in deps):
                        frameworks.append(framework)
            except Exception:
                pass

        if (repo_path / "requirements.txt").exists():
            try:
                requirements = (repo_path / "requirements.txt").read_text()
                python_frameworks = {
                    "Django": ["django", "Django"],
                    "Flask": ["flask", "Flask"],
                    "FastAPI": ["fastapi", "FastAPI"],
                    "Tornado": ["tornado"],
                    "Pyramid": ["pyramid"]
                }

                for framework, indicators in python_frameworks.items():
                    if any(indicator in requirements for indicator in indicators):
                        frameworks.append(framework)
            except Exception:
                pass

        return languages, frameworks

    async def _detect_project_type(self, structure: Dict[str, Any]) -> str:
        """Detect project type based on structure."""
        directories = structure.get("directories", [])
        config_files = structure.get("config_files", [])

        # Web application indicators
        if any(d in directories for d in ["public", "static", "assets"]):
            return "web_application"

        # API/Backend indicators
        if any(d in directories for d in ["api", "routes", "controllers", "endpoints"]):
            return "api_service"

        # Library indicators
        if "setup.py" in config_files or "pyproject.toml" in config_files:
            return "python_library"

        if "package.json" in config_files:
            return "npm_package"

        # CLI tool indicators
        if "bin" in directories or "scripts" in directories:
            return "cli_tool"

        # Microservice indicators
        if "Dockerfile" in config_files:
            return "microservice"

        return "application"

    async def _analyze_features(self) -> List[Dict[str, str]]:
        """Analyze features from specs directory."""
        features = []
        specs_dir = self.settings.repo_path / "specs"

        if specs_dir.exists():
            for feature_dir in specs_dir.iterdir():
                if feature_dir.is_dir() and not feature_dir.name.startswith("."):
                    feature_info = {
                        "name": feature_dir.name,
                        "status": "unknown"
                    }

                    # Check for spec.md
                    spec_file = feature_dir / "spec.md"
                    if spec_file.exists():
                        feature_info["status"] = "specified"

                    # Check for plan.md
                    plan_file = feature_dir / "plan.md"
                    if plan_file.exists():
                        feature_info["status"] = "planned"

                    # Check for tasks.md
                    tasks_file = feature_dir / "tasks.md"
                    if tasks_file.exists():
                        feature_info["status"] = "in_progress"
                        # Could analyze task completion here

                    features.append(feature_info)

        return features

    async def _analyze_testing_setup(self) -> Dict[str, Any]:
        """Analyze testing setup."""
        testing = {
            "frameworks": [],
            "test_dirs": [],
            "config_files": []
        }

        repo_path = self.settings.repo_path

        # Test directories
        test_dirs = ["tests", "test", "__tests__", "spec"]
        for test_dir in test_dirs:
            if (repo_path / test_dir).exists():
                testing["test_dirs"].append(test_dir)

        # Testing config files
        test_configs = ["pytest.ini", "jest.config.js", "karma.conf.js", ".coveragerc"]
        for config in test_configs:
            if (repo_path / config).exists():
                testing["config_files"].append(config)

        # Detect testing frameworks from dependencies
        if (repo_path / "package.json").exists():
            try:
                import json
                package_json = json.loads((repo_path / "package.json").read_text())
                dependencies = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}

                js_test_frameworks = ["jest", "mocha", "jasmine", "cypress", "playwright"]
                for framework in js_test_frameworks:
                    if framework in dependencies:
                        testing["frameworks"].append(framework)
            except Exception:
                pass

        if (repo_path / "requirements.txt").exists():
            try:
                requirements = (repo_path / "requirements.txt").read_text()
                python_test_frameworks = ["pytest", "unittest", "nose", "testify"]
                for framework in python_test_frameworks:
                    if framework in requirements:
                        testing["frameworks"].append(framework)
            except Exception:
                pass

        return testing

    async def _analyze_ci_cd_setup(self) -> Dict[str, Any]:
        """Analyze CI/CD setup."""
        ci_cd = {
            "platforms": [],
            "config_files": [],
            "deployment": []
        }

        repo_path = self.settings.repo_path

        # CI/CD config files
        ci_configs = {
            "GitHub Actions": [".github/workflows"],
            "GitLab CI": [".gitlab-ci.yml"],
            "Travis CI": [".travis.yml"],
            "CircleCI": [".circleci/config.yml"],
            "Jenkins": ["Jenkinsfile"],
            "Azure Pipelines": ["azure-pipelines.yml"]
        }

        for platform, configs in ci_configs.items():
            for config in configs:
                if (repo_path / config).exists():
                    ci_cd["platforms"].append(platform)
                    ci_cd["config_files"].append(config)

        # Deployment indicators
        deployment_files = ["Dockerfile", "docker-compose.yml", "k8s", "kubernetes"]
        for deploy_file in deployment_files:
            if (repo_path / deploy_file).exists():
                ci_cd["deployment"].append(deploy_file)

        return ci_cd

    async def _update_claude_context(
        self,
        project_info: Dict[str, Any],
        technologies: Dict[str, str],
        recent_changes: List[str]
    ) -> Path:
        """Update Claude-specific context file."""
        context_file = self.settings.repo_path / "CLAUDE.md"
        content = self._generate_claude_content(project_info, technologies, recent_changes)
        context_file.write_text(content)
        return context_file

    async def _update_gemini_context(
        self,
        project_info: Dict[str, Any],
        technologies: Dict[str, str],
        recent_changes: List[str]
    ) -> Path:
        """Update Gemini-specific context file."""
        context_file = self.settings.repo_path / "GEMINI.md"
        content = self._generate_gemini_content(project_info, technologies, recent_changes)
        context_file.write_text(content)
        return context_file

    async def _update_copilot_context(
        self,
        project_info: Dict[str, Any],
        technologies: Dict[str, str],
        recent_changes: List[str]
    ) -> Path:
        """Update GitHub Copilot context file."""
        context_file = self.settings.repo_path / "copilot-instructions.md"
        content = self._generate_copilot_content(project_info, technologies, recent_changes)
        context_file.write_text(content)
        return context_file

    async def _update_general_context(
        self,
        project_info: Dict[str, Any],
        technologies: Dict[str, str],
        recent_changes: List[str]
    ) -> Path:
        """Update general agent context file."""
        context_file = self.settings.repo_path / "AI_CONTEXT.md"
        content = self._generate_general_content(project_info, technologies, recent_changes)
        context_file.write_text(content)
        return context_file

    def _generate_claude_content(
        self,
        project_info: Dict[str, Any],
        technologies: Dict[str, str],
        recent_changes: List[str]
    ) -> str:
        """Generate Claude-specific context content."""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Claude Context: {project_info['name']}

**Last Updated**: {date}
**Project Type**: {project_info['type'].replace('_', ' ').title()}

## Project Overview

This is a {project_info['type'].replace('_', ' ')} built with {', '.join(project_info['languages'])}.

### Architecture
- **Languages**: {', '.join(project_info['languages']) if project_info['languages'] else 'Not detected'}
- **Frameworks**: {', '.join(project_info['frameworks']) if project_info['frameworks'] else 'None detected'}
- **Project Structure**: {project_info['type'].replace('_', ' ')}

### Key Directories
{self._format_directories(project_info['structure'])}

## Current Technologies

{self._format_technologies(technologies, project_info)}

## Features Status

{self._format_features(project_info['features'])}

## Testing Setup

{self._format_testing(project_info['testing_setup'])}

## Recent Changes

{self._format_recent_changes(recent_changes)}

## Claude-Specific Guidelines

### Code Style Preferences
- Follow established patterns in the codebase
- Prioritize readability and maintainability
- Use type hints when available
- Follow the spec-kit methodology for feature development

### Development Workflow
1. **Specification First**: Always start with clear specifications
2. **Test-Driven Development**: Write tests before implementation
3. **Incremental Development**: Break down features into small, manageable tasks
4. **Constitution Compliance**: Ensure simplicity and avoid unnecessary complexity

### Response Format
- Provide clear, actionable code suggestions
- Include explanations for architectural decisions
- Suggest improvements when appropriate
- Reference relevant files and line numbers when possible

### Communication Style
- Be precise and technical when discussing implementation details
- Provide context for decisions
- Ask clarifying questions when requirements are ambiguous
- Offer multiple approaches when there are trade-offs

## File Organization

{self._format_file_organization(project_info['structure'])}

## Development Notes

- This project uses spec-kit methodology for feature development
- Features are developed in branches and documented in the `specs/` directory
- Each feature follows: specification → planning → tasks → implementation
- Constitution compliance is enforced for simplicity and maintainability
"""
        return content

    def _generate_gemini_content(
        self,
        project_info: Dict[str, Any],
        technologies: Dict[str, str],
        recent_changes: List[str]
    ) -> str:
        """Generate Gemini-specific context content."""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Gemini Context: {project_info['name']}

**Last Updated**: {date}
**Project Type**: {project_info['type'].replace('_', ' ').title()}

## Project Summary

A {project_info['type'].replace('_', ' ')} implementation using {', '.join(project_info['languages'])}.

## Technical Stack

### Core Technologies
{self._format_technologies(technologies, project_info)}

### Project Structure
{self._format_project_structure_gemini(project_info['structure'])}

## Development Context

### Active Features
{self._format_features_gemini(project_info['features'])}

### Testing Framework
{self._format_testing_gemini(project_info['testing_setup'])}

### Recent Updates
{self._format_recent_changes_gemini(recent_changes)}

## Gemini-Specific Instructions

### Code Generation Guidelines
- **Clarity First**: Generate clear, well-documented code
- **Best Practices**: Follow language-specific best practices
- **Error Handling**: Include comprehensive error handling
- **Performance**: Consider performance implications

### Analysis Approach
- **Comprehensive Review**: Analyze code holistically
- **Pattern Recognition**: Identify existing patterns and maintain consistency
- **Optimization Suggestions**: Propose performance and maintainability improvements
- **Security Considerations**: Highlight potential security issues

### Communication Style
- **Structured Responses**: Use clear headings and bullet points
- **Code Examples**: Provide concrete examples with explanations
- **Alternative Solutions**: Present multiple approaches when applicable
- **Reasoning**: Explain the rationale behind suggestions

### Development Methodology

This project follows the spec-kit methodology:

1. **Specification Phase**: Clear requirements definition
2. **Planning Phase**: Technical implementation planning
3. **Task Generation**: Breakdown into executable tasks
4. **Implementation**: TDD-based development
5. **Constitution Compliance**: Simplicity and quality enforcement

## File Structure Reference

{self._format_file_structure_reference(project_info['structure'])}

## Quality Standards

- **Simplicity**: Prefer simple solutions over complex ones
- **Testability**: All code should be easily testable
- **Documentation**: Code should be self-documenting
- **Maintainability**: Consider long-term maintenance implications
"""
        return content

    def _generate_copilot_content(
        self,
        project_info: Dict[str, Any],
        technologies: Dict[str, str],
        recent_changes: List[str]
    ) -> str:
        """Generate GitHub Copilot context content."""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# GitHub Copilot Instructions: {project_info['name']}

**Updated**: {date}

## Project Context

**Type**: {project_info['type'].replace('_', ' ').title()}
**Languages**: {', '.join(project_info['languages'])}
**Frameworks**: {', '.join(project_info['frameworks'])}

## Code Generation Rules

### Language-Specific Guidelines

{self._generate_language_guidelines(project_info['languages'])}

### Framework Conventions

{self._generate_framework_conventions(project_info['frameworks'])}

### File Organization

{self._format_file_org_copilot(project_info['structure'])}

## Code Style Standards

### General Principles
- Follow existing code patterns in the repository
- Prioritize readability over brevity
- Include appropriate error handling
- Add meaningful comments for complex logic

### Naming Conventions
{self._generate_naming_conventions(project_info['languages'])}

### Testing Guidelines
- Write tests for all new functions/methods
- Follow the existing test structure in `{', '.join(project_info['testing_setup']['test_dirs'])}`
- Use descriptive test names that explain the scenario

## Feature Development Workflow

1. **Check specs directory** for feature documentation
2. **Follow TDD approach** - tests before implementation
3. **Maintain simplicity** - avoid over-engineering
4. **Update documentation** as needed

## Common Patterns

{self._generate_common_patterns(project_info)}

## Recent Context

{self._format_recent_changes_copilot(recent_changes)}

## Avoid These Patterns

- Over-complicated abstractions
- Unnecessary design patterns without clear benefits
- Breaking existing conventions without good reason
- Skipping tests or error handling

## Preferred Libraries/Tools

{self._format_preferred_tools(technologies, project_info)}
"""
        return content

    def _generate_general_content(
        self,
        project_info: Dict[str, Any],
        technologies: Dict[str, str],
        recent_changes: List[str]
    ) -> str:
        """Generate general AI agent context content."""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# AI Agent Context: {project_info['name']}

**Last Updated**: {date}
**Project Type**: {project_info['type'].replace('_', ' ').title()}

## Project Overview

{project_info['name']} is a {project_info['type'].replace('_', ' ')} built with:

- **Primary Languages**: {', '.join(project_info['languages']) if project_info['languages'] else 'Not detected'}
- **Frameworks**: {', '.join(project_info['frameworks']) if project_info['frameworks'] else 'None detected'}
- **Architecture**: {project_info['type'].replace('_', ' ').title()}

## Technology Stack

{self._format_complete_tech_stack(technologies, project_info)}

## Project Structure

{self._format_complete_structure(project_info['structure'])}

## Development Methodology

This project follows the **spec-kit methodology**:

### Phase 1: Specification
- Features are specified in `specs/<feature-name>/spec.md`
- Requirements are clearly defined with acceptance criteria
- Clarifications are marked for resolution

### Phase 2: Planning
- Technical implementation plans in `specs/<feature-name>/plan.md`
- Architecture decisions are documented
- Technology choices are justified

### Phase 3: Task Generation
- Executable tasks are generated in `specs/<feature-name>/tasks.md`
- Tasks follow TDD principles
- Parallel execution is marked where possible

### Phase 4: Implementation
- Test-driven development is enforced
- Constitution compliance is maintained
- Regular progress tracking

## Constitution Principles

### Simplicity
- Maximum 3 projects per feature
- Use frameworks directly (no wrapper classes)
- Avoid unnecessary patterns (Repository/UoW without proven need)

### Architecture
- Every feature as a library
- CLI interfaces for all libraries
- Documentation in llms.txt format

### Testing (Non-Negotiable)
- RED-GREEN-Refactor cycle enforced
- Tests MUST fail before implementation
- Order: Contract → Integration → E2E → Unit
- Real dependencies (no mocks unless necessary)

### Observability
- Structured logging included
- Error context provided
- Monitoring considerations

### Versioning
- Version numbers assigned (MAJOR.MINOR.BUILD)
- BUILD increments on every change
- Breaking changes planned carefully

## Active Features

{self._format_features_detailed(project_info['features'])}

## Testing Configuration

{self._format_testing_detailed(project_info['testing_setup'])}

## CI/CD Setup

{self._format_ci_cd_detailed(project_info['ci_cd'])}

## Recent Changes

{self._format_recent_changes_detailed(recent_changes)}

## Code Guidelines

### Quality Standards
- Readable and maintainable code
- Comprehensive error handling
- Appropriate logging and monitoring
- Clear documentation and comments

### Development Practices
- Feature branch workflow
- Test-driven development
- Code review requirements
- Constitution compliance checks

### File Organization Best Practices
{self._format_best_practices(project_info['structure'])}

## Support Resources

- **Specifications**: `specs/` directory contains all feature documentation
- **Testing**: Follow patterns in `{', '.join(project_info['testing_setup']['test_dirs'])}`
- **Configuration**: Key config files: {', '.join(project_info['structure']['config_files'])}
- **Documentation**: {', '.join(project_info['structure']['documentation'])}
"""
        return content

    # Helper formatting methods
    def _format_directories(self, structure: Dict[str, Any]) -> str:
        """Format directory structure for display."""
        directories = structure.get("directories", [])
        if not directories:
            return "- No specific directories detected"
        return "\n".join([f"- `{d}/`" for d in directories])

    def _format_technologies(self, technologies: Dict[str, str], project_info: Dict[str, Any]) -> str:
        """Format technology information."""
        content = ""
        if technologies:
            content += "### Specified Technologies\n"
            for tech, version in technologies.items():
                content += f"- **{tech}**: {version}\n"
            content += "\n"

        content += "### Detected Technologies\n"
        for lang in project_info['languages']:
            content += f"- **Language**: {lang}\n"
        for framework in project_info['frameworks']:
            content += f"- **Framework**: {framework}\n"

        return content or "- No technologies specified or detected"

    def _format_features(self, features: List[Dict[str, str]]) -> str:
        """Format features information."""
        if not features:
            return "- No features found in specs directory"

        content = ""
        for feature in features:
            status_emoji = {
                "specified": "📝",
                "planned": "📋",
                "in_progress": "🔄",
                "unknown": "❓"
            }.get(feature['status'], "❓")
            content += f"- {status_emoji} **{feature['name']}** ({feature['status']})\n"
        return content

    def _format_testing(self, testing_setup: Dict[str, Any]) -> str:
        """Format testing setup information."""
        content = ""
        if testing_setup.get('frameworks'):
            content += f"- **Frameworks**: {', '.join(testing_setup['frameworks'])}\n"
        if testing_setup.get('test_dirs'):
            content += f"- **Test Directories**: {', '.join(testing_setup['test_dirs'])}\n"
        if testing_setup.get('config_files'):
            content += f"- **Config Files**: {', '.join(testing_setup['config_files'])}\n"
        return content or "- No testing setup detected"

    def _format_recent_changes(self, recent_changes: List[str]) -> str:
        """Format recent changes information."""
        if not recent_changes:
            return "- No recent changes specified"
        return "\n".join([f"- {change}" for change in recent_changes])

    def _format_file_organization(self, structure: Dict[str, Any]) -> str:
        """Format file organization information."""
        content = "### Source Directories\n"
        source_dirs = structure.get("source_dirs", [])
        if source_dirs:
            content += "\n".join([f"- `{d}/` - Main source code" for d in source_dirs])
        else:
            content += "- Source organization not clearly detected"

        content += "\n\n### Configuration\n"
        config_files = structure.get("config_files", [])
        if config_files:
            content += "\n".join([f"- `{f}` - Configuration file" for f in config_files[:5]])
            if len(config_files) > 5:
                content += f"\n- ... and {len(config_files) - 5} more"
        else:
            content += "- No configuration files detected"

        return content

    # Additional helper methods for specific agent formats
    def _format_features_gemini(self, features: List[Dict[str, str]]) -> str:
        return self._format_features(features)

    def _format_testing_gemini(self, testing_setup: Dict[str, Any]) -> str:
        return self._format_testing(testing_setup)

    def _format_recent_changes_gemini(self, recent_changes: List[str]) -> str:
        return self._format_recent_changes(recent_changes)

    def _format_recent_changes_copilot(self, recent_changes: List[str]) -> str:
        return self._format_recent_changes(recent_changes)

    def _format_recent_changes_detailed(self, recent_changes: List[str]) -> str:
        return self._format_recent_changes(recent_changes)

    def _format_project_structure_gemini(self, structure: Dict[str, Any]) -> str:
        return self._format_directories(structure)

    def _format_file_structure_reference(self, structure: Dict[str, Any]) -> str:
        return self._format_file_organization(structure)

    def _format_file_org_copilot(self, structure: Dict[str, Any]) -> str:
        return self._format_directories(structure)

    def _format_complete_tech_stack(self, technologies: Dict[str, str], project_info: Dict[str, Any]) -> str:
        return self._format_technologies(technologies, project_info)

    def _format_complete_structure(self, structure: Dict[str, Any]) -> str:
        return self._format_file_organization(structure)

    def _format_features_detailed(self, features: List[Dict[str, str]]) -> str:
        return self._format_features(features)

    def _format_testing_detailed(self, testing_setup: Dict[str, Any]) -> str:
        return self._format_testing(testing_setup)

    def _format_ci_cd_detailed(self, ci_cd: Dict[str, Any]) -> str:
        content = ""
        if ci_cd.get('platforms'):
            content += f"- **Platforms**: {', '.join(ci_cd['platforms'])}\n"
        if ci_cd.get('config_files'):
            content += f"- **Config Files**: {', '.join(ci_cd['config_files'])}\n"
        if ci_cd.get('deployment'):
            content += f"- **Deployment**: {', '.join(ci_cd['deployment'])}\n"
        return content or "- No CI/CD setup detected"

    def _format_best_practices(self, structure: Dict[str, Any]) -> str:
        return self._format_file_organization(structure)

    def _generate_language_guidelines(self, languages: List[str]) -> str:
        guidelines = ""
        for lang in languages:
            if lang.lower() == "python":
                guidelines += "#### Python\n- Follow PEP 8 style guide\n- Use type hints\n- Prefer f-strings for formatting\n\n"
            elif lang.lower() == "javascript":
                guidelines += "#### JavaScript\n- Use const/let instead of var\n- Prefer arrow functions\n- Use async/await for promises\n\n"
            elif lang.lower() == "typescript":
                guidelines += "#### TypeScript\n- Use strict type checking\n- Define interfaces for complex types\n- Prefer explicit return types\n\n"
        return guidelines or "- Follow general best practices for the detected languages"

    def _generate_framework_conventions(self, frameworks: List[str]) -> str:
        conventions = ""
        for framework in frameworks:
            if framework.lower() == "react":
                conventions += "#### React\n- Use functional components with hooks\n- Follow component naming conventions\n- Organize by feature, not by file type\n\n"
            elif framework.lower() == "django":
                conventions += "#### Django\n- Follow Django conventions\n- Use class-based views where appropriate\n- Keep models simple and focused\n\n"
        return conventions or "- Follow framework-specific best practices"

    def _generate_naming_conventions(self, languages: List[str]) -> str:
        conventions = ""
        for lang in languages:
            if lang.lower() == "python":
                conventions += "#### Python\n- snake_case for variables and functions\n- PascalCase for classes\n- UPPER_CASE for constants\n\n"
            elif lang.lower() in ["javascript", "typescript"]:
                conventions += "#### JavaScript/TypeScript\n- camelCase for variables and functions\n- PascalCase for classes and components\n- UPPER_CASE for constants\n\n"
        return conventions or "- Follow language-specific naming conventions"

    def _generate_common_patterns(self, project_info: Dict[str, Any]) -> str:
        return f"""### Error Handling
- Use try/catch blocks appropriately
- Log errors with context
- Return meaningful error messages

### Code Organization
- Group related functionality
- Keep functions focused and small
- Use descriptive names

### Documentation
- Comment complex logic
- Use docstrings for functions/classes
- Keep README updated"""

    def _format_preferred_tools(self, technologies: Dict[str, str], project_info: Dict[str, Any]) -> str:
        content = ""
        if technologies:
            for tech, version in technologies.items():
                content += f"- **{tech}** (version {version})\n"

        # Add detected frameworks
        for framework in project_info['frameworks']:
            content += f"- **{framework}** (detected framework)\n"

        return content or "- Use tools consistent with the existing codebase"


# Export tool functions
async def update_agent_context(
    agent_type: str,
    technologies: Optional[Dict[str, str]] = None,
    recent_changes: Optional[List[str]] = None,
    settings: Settings = None
) -> ToolResponse:
    """Update agent context files."""
    tool = UpdateAgentContextTool(settings)
    return await tool.execute(
        agent_type=agent_type,
        technologies=technologies,
        recent_changes=recent_changes
    )