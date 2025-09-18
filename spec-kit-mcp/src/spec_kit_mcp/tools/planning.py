"""Planning tools for spec-kit MCP server."""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from .base import BaseTool
from ..models import ToolResponse
from ..exceptions import FileSystemError, ValidationError, ScriptExecutionError, TemplateProcessingError
from ..utils.scripts import ScriptRunner
from ..utils.templates import TemplateProcessor
from ..utils.git_ops import GitOperations
from ..config import Settings

logger = logging.getLogger(__name__)


class CreatePlanTool(BaseTool):
    """Create a technical implementation plan for a feature."""

    async def execute(
        self,
        tech_stack: str,
        language: str,
        framework: str,
        storage: Optional[str] = None,
        project_type: str = "single"
    ) -> ToolResponse:
        """Create a technical implementation plan."""
        # Validate inputs
        validated_inputs = await self.validate_inputs(
            tech_stack=tech_stack,
            language=language,
            framework=framework,
            storage=storage,
            project_type=project_type
        )

        # Check if scripts are available
        if not self.settings.scripts_path or not self.settings.scripts_path.exists():
            # Fallback to manual creation
            return await self._manual_create_plan(**validated_inputs)

        try:
            # Use spec-kit scripts
            script_runner = ScriptRunner(self.settings.scripts_path, self.settings.script_timeout)

            # Run setup-plan.sh script to get feature paths
            result = await script_runner.run_script(
                "setup-plan.sh",
                args=["--json"],
                json_output=True,
                cwd=self.settings.repo_path
            )

            feature_spec = result.get("FEATURE_SPEC")
            impl_plan = result.get("IMPL_PLAN")
            specs_dir = result.get("SPECS_DIR")
            branch_name = result.get("BRANCH")

            if not all([feature_spec, impl_plan, specs_dir, branch_name]):
                raise ScriptExecutionError(
                    "Script did not return expected output",
                    details={"result": result}
                )

            # Convert paths to Path objects
            feature_spec_path = Path(feature_spec)
            impl_plan_path = Path(impl_plan)
            specs_dir_path = Path(specs_dir)

            # Validate that the spec file exists
            if not feature_spec_path.exists():
                raise ValidationError(
                    f"Feature specification not found: {feature_spec_path}",
                    suggestions=["Run create_specification first to create the spec file"]
                )

            # Process the plan template
            created_files = await self._process_plan_template(
                branch_name=branch_name,
                feature_spec_path=feature_spec_path,
                impl_plan_path=impl_plan_path,
                specs_dir_path=specs_dir_path,
                **validated_inputs
            )

            return self.create_success_response(
                message=f"Created implementation plan for {branch_name}",
                data={
                    "branch_name": branch_name,
                    "impl_plan": str(impl_plan_path),
                    "created_files": created_files,
                    "specs_dir": str(specs_dir_path)
                },
                artifacts=[Path(f) for f in created_files]
            )

        except Exception as e:
            logger.error(f"Failed to create plan using scripts: {e}")
            # Try manual fallback
            return await self._manual_create_plan(**validated_inputs)

    async def validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize planning inputs."""
        tech_stack = kwargs.get("tech_stack", "").strip()
        language = kwargs.get("language", "").strip()
        framework = kwargs.get("framework", "").strip()
        storage = kwargs.get("storage")
        project_type = kwargs.get("project_type", "single")

        if not tech_stack:
            raise ValidationError("tech_stack is required")
        if not language:
            raise ValidationError("language is required")
        if not framework:
            raise ValidationError("framework is required")
        if project_type not in ["single", "web", "mobile"]:
            raise ValidationError(
                f"Invalid project_type: {project_type}",
                suggestions=["Use 'single', 'web', or 'mobile'"]
            )

        return {
            "tech_stack": tech_stack,
            "language": language,
            "framework": framework,
            "storage": storage.strip() if storage else None,
            "project_type": project_type
        }

    async def _manual_create_plan(self, **kwargs) -> ToolResponse:
        """Manually create implementation plan without scripts."""
        # Get current branch
        git_ops = GitOperations(self.settings.repo_path)
        branch_name = await git_ops.get_current_branch()

        if not branch_name or branch_name == "main" or branch_name == "master":
            raise ValidationError(
                "Not on a feature branch",
                suggestions=["Create a feature branch first using create_specification"]
            )

        # Get feature directory and paths
        specs_dir_path = self.settings.repo_path / "specs" / branch_name
        feature_spec_path = specs_dir_path / "spec.md"
        impl_plan_path = specs_dir_path / "plan.md"

        # Validate that the spec file exists
        if not feature_spec_path.exists():
            raise ValidationError(
                f"Feature specification not found: {feature_spec_path}",
                suggestions=["Run create_specification first to create the spec file"]
            )

        # Create specs directory if it doesn't exist
        specs_dir_path.mkdir(parents=True, exist_ok=True)

        # Process the plan template
        created_files = await self._process_plan_template(
            branch_name=branch_name,
            feature_spec_path=feature_spec_path,
            impl_plan_path=impl_plan_path,
            specs_dir_path=specs_dir_path,
            **kwargs
        )

        return self.create_success_response(
            message=f"Created implementation plan for {branch_name}",
            data={
                "branch_name": branch_name,
                "impl_plan": str(impl_plan_path),
                "created_files": created_files,
                "specs_dir": str(specs_dir_path)
            },
            artifacts=[Path(f) for f in created_files]
        )

    async def _process_plan_template(
        self,
        branch_name: str,
        feature_spec_path: Path,
        impl_plan_path: Path,
        specs_dir_path: Path,
        tech_stack: str,
        language: str,
        framework: str,
        storage: Optional[str],
        project_type: str
    ) -> List[str]:
        """Process the plan template and create all required files."""
        created_files = []

        # Process plan template with template processor if available
        if self.settings.templates_path and self.settings.templates_path.exists():
            template_processor = TemplateProcessor(self.settings.templates_path)

            if template_processor.template_exists("plan-template.md"):
                template_processor.process_plan_template(
                    branch_name=branch_name,
                    tech_stack=tech_stack,
                    language=language,
                    framework=framework,
                    storage=storage,
                    project_type=project_type,
                    output_path=impl_plan_path
                )
                created_files.append(str(impl_plan_path))
            else:
                # Create basic plan file
                plan_content = self._create_basic_plan(
                    branch_name=branch_name,
                    feature_spec_path=feature_spec_path,
                    tech_stack=tech_stack,
                    language=language,
                    framework=framework,
                    storage=storage,
                    project_type=project_type
                )
                impl_plan_path.write_text(plan_content)
                created_files.append(str(impl_plan_path))
        else:
            # Create basic plan file without templates
            plan_content = self._create_basic_plan(
                branch_name=branch_name,
                feature_spec_path=feature_spec_path,
                tech_stack=tech_stack,
                language=language,
                framework=framework,
                storage=storage,
                project_type=project_type
            )
            impl_plan_path.write_text(plan_content)
            created_files.append(str(impl_plan_path))

        # Create additional required files
        additional_files = await self._create_additional_files(
            specs_dir_path, branch_name, feature_spec_path
        )
        created_files.extend(additional_files)

        return created_files

    def _create_basic_plan(
        self,
        branch_name: str,
        feature_spec_path: Path,
        tech_stack: str,
        language: str,
        framework: str,
        storage: Optional[str],
        project_type: str
    ) -> str:
        """Create basic plan content without template processing."""
        feature_name = self._extract_feature_name(branch_name)
        date = datetime.now().strftime("%Y-%m-%d")

        return f"""# Implementation Plan: {feature_name}
**Branch**: `{branch_name}` | **Date**: {date} | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `{feature_spec_path}`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {{path}}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context ({project_type})
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```
**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context
**Language/Version**: {language}
**Primary Dependencies**: {framework}
**Storage**: {storage or 'N/A'}
**Testing**: [NEEDS CLARIFICATION]
**Target Platform**: [NEEDS CLARIFICATION]
**Project Type**: {project_type}
**Performance Goals**: [NEEDS CLARIFICATION]
**Constraints**: [NEEDS CLARIFICATION]
**Scale/Scope**: [NEEDS CLARIFICATION]

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: [#] (max 3 - e.g., api, cli, tests)
- Using framework directly? (no wrapper classes)
- Single data model? (no DTOs unless serialization differs)
- Avoiding patterns? (no Repository/UoW without proven need)

**Architecture**:
- EVERY feature as library? (no direct app code)
- Libraries listed: [name + purpose for each]
- CLI per library: [commands with --help/--version/--format]
- Library docs: llms.txt format planned?

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? (test MUST fail first)
- Git commits show tests before implementation?
- Order: Contract→Integration→E2E→Unit strictly followed?
- Real dependencies used? (actual DBs, not mocks)
- Integration tests for: new libraries, contract changes, shared schemas?
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included?
- Frontend logs → backend? (unified stream)
- Error context sufficient?

**Versioning**:
- Version number assigned? (MAJOR.MINOR.BUILD)
- BUILD increments on every change?
- Breaking changes handled? (parallel tests, migration plan)

## Project Structure
### Documentation (this feature)
```
specs/{branch_name}/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/
```

## Phase 0: Research
See [research.md](research.md) for technical research and clarifications.

## Phase 1: Design
- Data model: [data-model.md](data-model.md)
- API contracts: [contracts/](contracts/)
- Quick start guide: [quickstart.md](quickstart.md)

## Phase 2: Task Planning
Tasks will be generated by the /tasks command based on this plan.
"""

    async def _create_additional_files(
        self,
        specs_dir_path: Path,
        branch_name: str,
        feature_spec_path: Path
    ) -> List[str]:
        """Create additional required files for the implementation plan."""
        created_files = []
        feature_name = self._extract_feature_name(branch_name)

        # Create research.md
        research_path = specs_dir_path / "research.md"
        research_content = f"""# Research: {feature_name}

## Technical Investigation

### Requirements Analysis
[Analyze the feature specification and identify technical requirements]

### Technology Stack Research
[Research specific implementation approaches for the chosen tech stack]

### Architecture Considerations
[Document architectural decisions and trade-offs]

### Dependencies and Libraries
[Research required dependencies and their implications]

### Performance and Scalability
[Research performance requirements and scalability considerations]

### Security Considerations
[Identify security requirements and best practices]

### Testing Strategy
[Define testing approach and requirements]

## Clarifications Needed
[List any remaining clarifications needed before implementation]

## Recommendations
[Provide implementation recommendations based on research]
"""
        research_path.write_text(research_content)
        created_files.append(str(research_path))

        # Create data-model.md
        data_model_path = specs_dir_path / "data-model.md"
        data_model_content = f"""# Data Model: {feature_name}

## Overview
[High-level description of the data model]

## Entities

### [Entity Name]
[Description of the entity and its purpose]

**Properties**:
- `property_name`: type - description

**Relationships**:
- [Describe relationships to other entities]

**Constraints**:
- [List validation rules and constraints]

## Data Flow
[Describe how data flows through the system]

## Persistence
[Describe how data is stored and retrieved]

## API Schema
[Define the API schema for data exchange]

## Validation Rules
[Define data validation requirements]
"""
        data_model_path.write_text(data_model_content)
        created_files.append(str(data_model_path))

        # Create contracts directory
        contracts_dir = specs_dir_path / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)

        # Create a sample contract file
        api_contract_path = contracts_dir / "api.md"
        api_contract_content = f"""# API Contract: {feature_name}

## Overview
[Description of the API contract]

## Endpoints

### [HTTP Method] /path/to/endpoint
[Description of the endpoint]

**Request**:
```json
{{
  "example": "request"
}}
```

**Response**:
```json
{{
  "example": "response"
}}
```

**Error Responses**:
- 400 Bad Request: [description]
- 404 Not Found: [description]
- 500 Internal Server Error: [description]

## Authentication
[Describe authentication requirements]

## Rate Limiting
[Describe rate limiting policies]

## Versioning
[Describe API versioning strategy]
"""
        api_contract_path.write_text(api_contract_content)
        created_files.append(str(api_contract_path))

        # Create quickstart.md
        quickstart_path = specs_dir_path / "quickstart.md"
        quickstart_content = f"""# Quick Start: {feature_name}

## Prerequisites
[List prerequisites for development and usage]

## Installation
[Step-by-step installation instructions]

```bash
# Example installation commands
```

## Configuration
[Configuration steps and options]

## Basic Usage
[Basic usage examples]

```bash
# Example usage commands
```

## Development Setup
[Development environment setup]

```bash
# Development setup commands
```

## Testing
[How to run tests]

```bash
# Test commands
```

## Troubleshooting
[Common issues and solutions]

## Next Steps
[What to do after basic setup]
"""
        quickstart_path.write_text(quickstart_content)
        created_files.append(str(quickstart_path))

        return created_files

    def _extract_feature_name(self, branch_name: str) -> str:
        """Extract feature name from branch name."""
        # Remove number prefix (e.g., "001-my-feature" -> "My Feature")
        parts = branch_name.split('-', 1)
        if len(parts) > 1:
            return parts[1].replace('-', ' ').title()
        return branch_name.replace('-', ' ').title()


# Export tool functions
async def create_plan(
    tech_stack: str,
    language: str,
    framework: str,
    storage: Optional[str] = None,
    project_type: str = "single",
    settings: Settings = None
) -> ToolResponse:
    """Create technical implementation plan."""
    tool = CreatePlanTool(settings)
    return await tool.execute(
        tech_stack=tech_stack,
        language=language,
        framework=framework,
        storage=storage,
        project_type=project_type
    )


class ConductResearchTool(BaseTool):
    """Conduct targeted technical research on specific topics."""

    async def execute(
        self,
        topics: List[str],
        context: str
    ) -> ToolResponse:
        """Conduct technical research."""
        try:
            # Validate inputs
            validated_inputs = await self.validate_inputs(
                topics=topics,
                context=context
            )

            topics = validated_inputs["topics"]
            context = validated_inputs["context"]

            # Check if scripts are available
            if not self.settings.scripts_path or not self.settings.scripts_path.exists():
                # Fallback to manual research
                return await self._manual_conduct_research(topics, context)

            # Use spec-kit scripts
            script_runner = ScriptRunner(self.settings.scripts_path, self.settings.script_timeout)

            # Prepare script arguments
            script_args = ["--context", context, "--json"]
            for topic in topics:
                script_args.extend(["--topic", topic])

            # Run research script
            result = await script_runner.run_script(
                "conduct-research.sh",
                args=script_args,
                json_output=True,
                cwd=self.settings.repo_path
            )

            research_file = result.get("research_file")
            topics_researched = result.get("topics_researched", [])
            recommendations = result.get("recommendations", [])
            clarifications_needed = result.get("clarifications_needed", [])

            if not research_file:
                raise ScriptExecutionError(
                    "Script did not return expected output",
                    details={"result": result}
                )

            return self.create_success_response(
                message=f"Research completed on {len(topics_researched)} topics",
                data={
                    "research_file": research_file,
                    "topics_researched": topics_researched,
                    "recommendations": recommendations,
                    "clarifications_needed": clarifications_needed,
                    "context": context
                },
                artifacts=[Path(research_file)]
            )

        except Exception as e:
            logger.error(f"Failed to conduct research using scripts: {e}")
            # Try manual fallback
            return await self._manual_conduct_research(topics, context)

    async def validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize inputs."""
        topics = kwargs.get("topics", [])
        context = kwargs.get("context", "").strip()

        if not topics:
            raise ValidationError("topics list cannot be empty")
        if not context:
            raise ValidationError("context is required")

        # Clean and validate topics
        cleaned_topics = [topic.strip() for topic in topics if topic.strip()]
        if not cleaned_topics:
            raise ValidationError("At least one valid topic is required")

        # Limit topics to 10
        if len(cleaned_topics) > 10:
            cleaned_topics = cleaned_topics[:10]

        if len(context) < 10:
            raise ValidationError("context must be at least 10 characters")
        if len(context) > 1000:
            raise ValidationError("context must be at most 1000 characters")

        return {
            "topics": cleaned_topics,
            "context": context
        }

    async def _manual_conduct_research(
        self,
        topics: List[str],
        context: str
    ) -> ToolResponse:
        """Manually conduct research without scripts."""
        # Get current branch and feature directory
        git_ops = GitOperations(self.settings.repo_path)
        branch_name = await git_ops.get_current_branch()

        if not branch_name or branch_name in ["main", "master"]:
            raise ValidationError(
                "Not on a feature branch",
                suggestions=["Switch to a feature branch first"]
            )

        feature_dir = self.get_feature_dir(branch_name)
        feature_dir.mkdir(parents=True, exist_ok=True)

        # Read existing specification if available
        spec_file = self.get_spec_file(branch_name)
        spec_content = ""
        if spec_file.exists():
            spec_content = spec_file.read_text()

        # Conduct research for each topic
        research_results = await self._research_topics(topics, context, spec_content)

        # Create or update research.md file
        research_file = await self._create_research_file(
            feature_dir,
            branch_name,
            topics,
            context,
            research_results
        )

        # Extract recommendations and clarifications
        recommendations = self._extract_recommendations(research_results)
        clarifications_needed = self._extract_clarifications(research_results)

        return self.create_success_response(
            message=f"Research completed on {len(topics)} topics",
            data={
                "research_file": str(research_file),
                "topics_researched": topics,
                "recommendations": recommendations,
                "clarifications_needed": clarifications_needed,
                "context": context
            },
            artifacts=[research_file]
        )

    async def _research_topics(
        self,
        topics: List[str],
        context: str,
        spec_content: str
    ) -> List[Dict[str, Any]]:
        """Research each topic and gather information."""
        research_results = []

        for topic in topics:
            result = await self._research_single_topic(topic, context, spec_content)
            research_results.append(result)

        return research_results

    async def _research_single_topic(
        self,
        topic: str,
        context: str,
        spec_content: str
    ) -> Dict[str, Any]:
        """Research a single topic."""
        # This is a framework for research - in a real implementation,
        # this could integrate with external APIs, documentation databases, etc.

        research_result = {
            "topic": topic,
            "findings": [],
            "recommendations": [],
            "clarifications_needed": [],
            "resources": [],
            "implementation_notes": []
        }

        # Analyze topic based on common technical research areas
        topic_lower = topic.lower()

        if any(keyword in topic_lower for keyword in ["performance", "optimization", "speed", "latency"]):
            research_result.update(self._research_performance_topic(topic, context))
        elif any(keyword in topic_lower for keyword in ["security", "auth", "authentication", "authorization"]):
            research_result.update(self._research_security_topic(topic, context))
        elif any(keyword in topic_lower for keyword in ["database", "storage", "persistence", "data model"]):
            research_result.update(self._research_database_topic(topic, context))
        elif any(keyword in topic_lower for keyword in ["api", "endpoint", "rest", "graphql", "grpc"]):
            research_result.update(self._research_api_topic(topic, context))
        elif any(keyword in topic_lower for keyword in ["testing", "test", "quality", "coverage"]):
            research_result.update(self._research_testing_topic(topic, context))
        elif any(keyword in topic_lower for keyword in ["deployment", "deploy", "ci", "cd", "devops"]):
            research_result.update(self._research_deployment_topic(topic, context))
        elif any(keyword in topic_lower for keyword in ["architecture", "design", "pattern", "structure"]):
            research_result.update(self._research_architecture_topic(topic, context))
        else:
            research_result.update(self._research_general_topic(topic, context))

        return research_result

    def _research_performance_topic(self, topic: str, context: str) -> Dict[str, Any]:
        """Research performance-related topics."""
        return {
            "findings": [
                "Performance considerations vary by technology stack and scale",
                "Benchmarking should be done with realistic data and usage patterns",
                "Early optimization should be avoided until performance requirements are clear"
            ],
            "recommendations": [
                "Define specific performance requirements (e.g., response time < 200ms)",
                "Implement performance monitoring from the start",
                "Use profiling tools appropriate for the technology stack",
                "Consider caching strategies for frequently accessed data"
            ],
            "clarifications_needed": [
                "What are the specific performance requirements?",
                "What is the expected user load and data volume?",
                "Are there any performance constraints from existing systems?"
            ],
            "resources": [
                "Performance testing frameworks for the chosen technology",
                "Monitoring and observability tools",
                "Load testing tools (Apache Bench, k6, JMeter)"
            ],
            "implementation_notes": [
                "Set up performance testing in CI/CD pipeline",
                "Implement structured logging for performance metrics",
                "Consider database indexing strategies",
                "Plan for horizontal scaling if needed"
            ]
        }

    def _research_security_topic(self, topic: str, context: str) -> Dict[str, Any]:
        """Research security-related topics."""
        return {
            "findings": [
                "Security must be considered at every layer of the application",
                "Authentication and authorization are distinct concerns",
                "Input validation and sanitization are critical",
                "Security by design is more effective than retrofitting"
            ],
            "recommendations": [
                "Follow OWASP guidelines for web application security",
                "Implement proper input validation and sanitization",
                "Use established authentication libraries rather than custom solutions",
                "Implement proper error handling to avoid information leakage",
                "Regular security audits and dependency scanning"
            ],
            "clarifications_needed": [
                "What authentication method will be used (JWT, OAuth, etc.)?",
                "Are there specific compliance requirements (GDPR, HIPAA, etc.)?",
                "What sensitive data needs protection?",
                "Are there existing security policies to follow?"
            ],
            "resources": [
                "OWASP Top 10 security risks",
                "Security-focused linting tools",
                "Dependency vulnerability scanners",
                "Authentication libraries for the chosen stack"
            ],
            "implementation_notes": [
                "Never store passwords in plain text",
                "Use HTTPS for all communications",
                "Implement proper session management",
                "Regular security dependency updates"
            ]
        }

    def _research_database_topic(self, topic: str, context: str) -> Dict[str, Any]:
        """Research database-related topics."""
        return {
            "findings": [
                "Database choice depends on data structure and access patterns",
                "ACID properties are important for transactional consistency",
                "Database migrations should be reversible and tested",
                "Connection pooling improves performance and resource usage"
            ],
            "recommendations": [
                "Choose database technology based on data requirements, not popularity",
                "Design database schema with normalization principles",
                "Implement proper indexing strategy",
                "Plan for database migrations and versioning",
                "Consider backup and disaster recovery strategies"
            ],
            "clarifications_needed": [
                "What type of data will be stored (relational, document, graph)?",
                "What are the consistency requirements?",
                "What is the expected data volume and growth rate?",
                "Are there any existing database constraints?"
            ],
            "resources": [
                "Database-specific ORMs or query builders",
                "Migration tools for the chosen database",
                "Database monitoring and performance tools",
                "Backup and recovery solutions"
            ],
            "implementation_notes": [
                "Use parameterized queries to prevent SQL injection",
                "Implement proper error handling for database operations",
                "Consider read replicas for scaling read operations",
                "Plan for database connection limits"
            ]
        }

    def _research_api_topic(self, topic: str, context: str) -> Dict[str, Any]:
        """Research API-related topics."""
        return {
            "findings": [
                "API design should follow RESTful principles or GraphQL best practices",
                "Consistent error handling and status codes improve developer experience",
                "API versioning strategy should be planned from the beginning",
                "Rate limiting prevents abuse and ensures fair usage"
            ],
            "recommendations": [
                "Design APIs with clear, consistent naming conventions",
                "Implement comprehensive input validation",
                "Provide clear error messages with appropriate HTTP status codes",
                "Document APIs with examples and clear descriptions",
                "Implement rate limiting and authentication"
            ],
            "clarifications_needed": [
                "What API style is preferred (REST, GraphQL, gRPC)?",
                "Who are the intended API consumers?",
                "What are the performance requirements for API responses?",
                "Are there existing API standards to follow?"
            ],
            "resources": [
                "OpenAPI/Swagger for REST API documentation",
                "GraphQL schema definition tools",
                "API testing frameworks (Postman, Insomnia)",
                "Rate limiting middleware"
            ],
            "implementation_notes": [
                "Use HTTP status codes correctly",
                "Implement consistent error response format",
                "Consider API pagination for large datasets",
                "Plan for API versioning strategy"
            ]
        }

    def _research_testing_topic(self, topic: str, context: str) -> Dict[str, Any]:
        """Research testing-related topics."""
        return {
            "findings": [
                "Test-driven development improves code quality and design",
                "Different types of tests serve different purposes",
                "Test coverage metrics should guide but not replace good judgment",
                "Automated testing in CI/CD prevents regressions"
            ],
            "recommendations": [
                "Implement TDD approach: Red-Green-Refactor cycle",
                "Write tests in order: Contract → Integration → E2E → Unit",
                "Use real dependencies in integration tests when possible",
                "Implement automated testing in CI/CD pipeline",
                "Focus on testing behavior, not implementation details"
            ],
            "clarifications_needed": [
                "What testing frameworks are preferred for the technology stack?",
                "What level of test coverage is required?",
                "Are there existing testing standards or practices to follow?",
                "What types of tests are most critical for this feature?"
            ],
            "resources": [
                "Testing frameworks for the chosen technology stack",
                "Test data generation tools",
                "Code coverage tools",
                "CI/CD integration for automated testing"
            ],
            "implementation_notes": [
                "Tests must fail before implementation (RED phase)",
                "Keep tests simple and focused",
                "Use descriptive test names that explain the scenario",
                "Mock external dependencies appropriately"
            ]
        }

    def _research_deployment_topic(self, topic: str, context: str) -> Dict[str, Any]:
        """Research deployment-related topics."""
        return {
            "findings": [
                "Automated deployment reduces human error and increases reliability",
                "Infrastructure as Code enables reproducible deployments",
                "Rolling deployments minimize downtime",
                "Environment parity reduces deployment-related issues"
            ],
            "recommendations": [
                "Implement CI/CD pipeline for automated deployments",
                "Use containerization for consistent deployment environments",
                "Implement proper environment configuration management",
                "Plan for rollback strategies in case of deployment issues",
                "Monitor deployments and application health"
            ],
            "clarifications_needed": [
                "What deployment environments are needed (dev, staging, prod)?",
                "What are the deployment frequency requirements?",
                "Are there existing deployment tools or platforms to use?",
                "What are the downtime tolerance requirements?"
            ],
            "resources": [
                "CI/CD platforms (GitHub Actions, GitLab CI, Jenkins)",
                "Containerization tools (Docker, Podman)",
                "Infrastructure as Code tools (Terraform, CloudFormation)",
                "Monitoring and alerting tools"
            ],
            "implementation_notes": [
                "Separate build and deployment processes",
                "Use environment variables for configuration",
                "Implement health checks for deployed services",
                "Plan for database migrations in deployment process"
            ]
        }

    def _research_architecture_topic(self, topic: str, context: str) -> Dict[str, Any]:
        """Research architecture-related topics."""
        return {
            "findings": [
                "Simple architectures are easier to understand and maintain",
                "Premature abstraction can lead to unnecessary complexity",
                "Architecture should support the business requirements",
                "Monolithic architectures are often simpler to start with"
            ],
            "recommendations": [
                "Start with simple architecture and evolve as needed",
                "Follow separation of concerns principles",
                "Avoid over-engineering and unnecessary patterns",
                "Document architectural decisions and their rationale",
                "Consider maintainability and team expertise"
            ],
            "clarifications_needed": [
                "What are the scalability requirements?",
                "What is the team's expertise and preferences?",
                "Are there existing architectural constraints?",
                "What are the performance and reliability requirements?"
            ],
            "resources": [
                "Architecture documentation templates",
                "Design pattern references",
                "Code organization best practices",
                "Architecture review processes"
            ],
            "implementation_notes": [
                "Keep it simple initially",
                "Document key architectural decisions",
                "Plan for future changes but don't over-engineer",
                "Consider team skills and maintenance requirements"
            ]
        }

    def _research_general_topic(self, topic: str, context: str) -> Dict[str, Any]:
        """Research general or unrecognized topics."""
        return {
            "findings": [
                f"Research needed for topic: {topic}",
                "Consider breaking down complex topics into smaller, specific areas",
                "Look for established best practices and standards"
            ],
            "recommendations": [
                f"Define specific research questions for {topic}",
                "Consult relevant documentation and community resources",
                "Consider expert consultation if topic is critical",
                "Prototype or spike solutions to validate approaches"
            ],
            "clarifications_needed": [
                f"What specific aspects of {topic} need research?",
                "What are the success criteria for this topic?",
                "Are there any constraints or requirements?"
            ],
            "resources": [
                "Official documentation for relevant technologies",
                "Community forums and discussion boards",
                "Technical blogs and case studies",
                "Open source examples and implementations"
            ],
            "implementation_notes": [
                "Start with small experiments or prototypes",
                "Document findings and decisions",
                "Validate assumptions with stakeholders",
                "Consider impact on overall project timeline"
            ]
        }

    async def _create_research_file(
        self,
        feature_dir: Path,
        branch_name: str,
        topics: List[str],
        context: str,
        research_results: List[Dict[str, Any]]
    ) -> Path:
        """Create or update research.md file."""
        research_file = feature_dir / "research.md"
        feature_name = self._extract_feature_name(branch_name)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Research: {feature_name}

**Date**: {date}
**Context**: {context}
**Topics Researched**: {len(topics)}

## Research Summary

This document contains technical research findings for the {feature_name} feature.
The research was conducted to inform implementation decisions and identify potential challenges.

## Context

{context}

## Research Topics

"""

        for i, result in enumerate(research_results, 1):
            topic = result["topic"]
            content += f"""### {i}. {topic}

#### Key Findings
{self._format_list_items(result['findings'])}

#### Recommendations
{self._format_list_items(result['recommendations'])}

#### Clarifications Needed
{self._format_list_items(result['clarifications_needed'])}

#### Resources
{self._format_list_items(result['resources'])}

#### Implementation Notes
{self._format_list_items(result['implementation_notes'])}

---

"""

        # Add overall summary
        all_recommendations = []
        all_clarifications = []
        for result in research_results:
            all_recommendations.extend(result['recommendations'])
            all_clarifications.extend(result['clarifications_needed'])

        content += f"""## Overall Summary

### Key Recommendations
{self._format_list_items(list(set(all_recommendations)))}

### Critical Clarifications Needed
{self._format_list_items(list(set(all_clarifications)))}

### Next Steps

1. **Address Clarifications**: Resolve all identified clarifications before proceeding
2. **Technical Validation**: Validate key technical assumptions through prototypes if needed
3. **Architecture Decisions**: Document architectural decisions based on research findings
4. **Implementation Planning**: Incorporate research findings into the implementation plan

### Research Status

- [ ] All clarifications resolved
- [ ] Technical assumptions validated
- [ ] Architecture decisions documented
- [ ] Implementation plan updated

## Notes

- This research document should be updated as new information becomes available
- Consider consulting with domain experts for complex or critical topics
- Validate research findings through practical implementation when possible
"""

        research_file.write_text(content)
        return research_file

    def _format_list_items(self, items: List[str]) -> str:
        """Format list items for markdown."""
        if not items:
            return "- None identified"
        return "\n".join([f"- {item}" for item in items])

    def _extract_recommendations(self, research_results: List[Dict[str, Any]]) -> List[str]:
        """Extract all recommendations from research results."""
        all_recommendations = []
        for result in research_results:
            all_recommendations.extend(result.get('recommendations', []))
        return list(set(all_recommendations))  # Remove duplicates

    def _extract_clarifications(self, research_results: List[Dict[str, Any]]) -> List[str]:
        """Extract all clarifications needed from research results."""
        all_clarifications = []
        for result in research_results:
            all_clarifications.extend(result.get('clarifications_needed', []))
        return list(set(all_clarifications))  # Remove duplicates

    def _extract_feature_name(self, branch_name: str) -> str:
        """Extract feature name from branch name."""
        parts = branch_name.split('-', 1)
        if len(parts) > 1:
            return parts[1].replace('-', ' ').title()
        return branch_name.replace('-', ' ').title()


async def conduct_research(
    topics: List[str],
    context: str,
    settings: Settings = None
) -> ToolResponse:
    """Conduct technical research."""
    tool = ConductResearchTool(settings)
    return await tool.execute(
        topics=topics,
        context=context
    )