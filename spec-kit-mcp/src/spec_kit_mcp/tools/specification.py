"""Specification tools for spec-kit MCP server."""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import re

from .base import BaseTool
from ..models import ToolResponse, SpecifyRequest
from ..exceptions import FileSystemError, ValidationError, ScriptExecutionError
from ..utils.scripts import ScriptRunner
from ..utils.git_ops import GitOperations
from ..utils.templates import TemplateProcessor
from ..utils.validation import InputValidator
from ..config import Settings

logger = logging.getLogger(__name__)


class CreateSpecificationTool(BaseTool):
    """Create a new feature specification."""

    async def execute(
        self,
        feature_description: str,
        mark_clarifications: bool = True
    ) -> ToolResponse:
        """Create a new feature specification and branch."""
        # Validate inputs
        request = SpecifyRequest(
            feature_description=feature_description,
            mark_clarifications=mark_clarifications
        )

        # Check if scripts are available
        if not self.settings.scripts_path or not self.settings.scripts_path.exists():
            # Fallback to manual creation
            return await self._manual_create_specification(request)

        try:
            # Use spec-kit scripts
            script_runner = ScriptRunner(self.settings.scripts_path, self.settings.script_timeout)

            # Run create-new-feature.sh script
            result = await script_runner.run_script(
                "create-new-feature.sh",
                args=[request.feature_description],
                json_output=True,
                cwd=self.settings.repo_path
            )

            branch_name = result.get("BRANCH_NAME")
            spec_file = result.get("SPEC_FILE")

            if not branch_name or not spec_file:
                raise ScriptExecutionError(
                    "Script did not return expected output",
                    details={"result": result}
                )

            spec_path = Path(spec_file)

            # Process the template with feature description
            if self.settings.templates_path:
                template_processor = TemplateProcessor(self.settings.templates_path)
                template_processor.process_spec_template(
                    feature_description=request.feature_description,
                    branch_name=branch_name,
                    output_path=spec_path
                )

            # Add clarification markers if requested
            if mark_clarifications:
                await self._add_clarification_markers(spec_path, request.feature_description)

            return self.create_success_response(
                message=f"Created specification for branch {branch_name}",
                data={
                    "branch_name": branch_name,
                    "spec_file": str(spec_path),
                    "feature_number": branch_name.split('-')[0]
                },
                artifacts=[spec_path]
            )

        except Exception as e:
            logger.error(f"Failed to create specification: {e}")
            # Try manual fallback
            return await self._manual_create_specification(request)

    async def _manual_create_specification(self, request: SpecifyRequest) -> ToolResponse:
        """Manually create specification without scripts."""
        git_ops = GitOperations(self.settings.repo_path)

        # Get next feature number
        feature_number = await git_ops.get_next_feature_number()
        feature_num_str = f"{feature_number:03d}"

        # Create branch name from description
        branch_name = self._create_branch_name(feature_num_str, request.feature_description)

        # Create and checkout branch
        await git_ops.create_branch(branch_name)

        # Create specs directory
        specs_dir = self.settings.repo_path / "specs" / branch_name
        specs_dir.mkdir(parents=True, exist_ok=True)

        # Create spec file
        spec_path = specs_dir / "spec.md"

        # Process template if available
        if self.settings.templates_path:
            template_processor = TemplateProcessor(self.settings.templates_path)
            template_processor.process_spec_template(
                feature_description=request.feature_description,
                branch_name=branch_name,
                output_path=spec_path
            )
        else:
            # Create basic spec file
            spec_content = self._create_basic_spec(
                branch_name,
                request.feature_description
            )
            spec_path.write_text(spec_content)

        # Add clarification markers if requested
        if request.mark_clarifications:
            await self._add_clarification_markers(spec_path, request.feature_description)

        return self.create_success_response(
            message=f"Created specification for branch {branch_name}",
            data={
                "branch_name": branch_name,
                "spec_file": str(spec_path),
                "feature_number": feature_num_str
            },
            artifacts=[spec_path]
        )

    def _create_branch_name(self, feature_num: str, description: str) -> str:
        """Create branch name from description."""
        # Extract meaningful words
        words = re.findall(r'\b[a-z]+\b', description.lower())
        # Take first 3-4 significant words
        significant_words = [w for w in words if len(w) > 3][:3]
        if not significant_words:
            significant_words = words[:3]

        feature_name = '-'.join(significant_words) if significant_words else "feature"
        return f"{feature_num}-{feature_name}"

    def _create_basic_spec(self, branch_name: str, description: str) -> str:
        """Create basic specification content."""
        from datetime import datetime

        feature_name = branch_name.split('-', 1)[1] if '-' in branch_name else branch_name
        feature_name = feature_name.replace('-', ' ').title()

        return f"""# Feature Specification: {feature_name}

**Feature Branch**: `{branch_name}`
**Created**: {datetime.now().strftime("%Y-%m-%d")}
**Status**: Draft
**Input**: User description: "{description}"

## User Scenarios & Testing

### Primary User Story
{description}

### Acceptance Scenarios
1. **Given** [initial state], **When** [action], **Then** [expected outcome]

### Edge Cases
- What happens when [boundary condition]?
- How does system handle [error scenario]?

## Requirements

### Functional Requirements
- **FR-001**: System MUST [NEEDS CLARIFICATION: specific capability]
- **FR-002**: System MUST [NEEDS CLARIFICATION: specific capability]

### Key Entities
- **[Entity 1]**: [NEEDS CLARIFICATION: What it represents]

## Review & Acceptance Checklist

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
"""

    async def _add_clarification_markers(self, spec_path: Path, description: str) -> None:
        """Add [NEEDS CLARIFICATION] markers to ambiguous parts."""
        # This would analyze the description and add markers
        # For now, we'll leave the basic markers from the template
        pass


class ValidateSpecificationTool(BaseTool):
    """Validate a specification against the review checklist."""

    async def execute(self, spec_path: str) -> ToolResponse:
        """Validate specification completeness."""
        path = self.validate_path(Path(spec_path), must_exist=True)

        if not path.name == "spec.md":
            raise ValidationError(
                "Invalid specification file",
                details={"path": str(path)},
                suggestions=["Provide path to spec.md file"]
            )

        content = path.read_text()

        # Validation checks
        validation_results = {
            "has_user_scenarios": "## User Scenarios" in content,
            "has_requirements": "## Requirements" in content,
            "has_functional_requirements": "### Functional Requirements" in content,
            "has_acceptance_scenarios": "### Acceptance Scenarios" in content,
            "has_clarifications": "[NEEDS CLARIFICATION" in content,
            "has_implementation_details": any(
                keyword in content.lower()
                for keyword in ["python", "javascript", "api", "database", "framework"]
            ),
            "checklist_items": len(re.findall(r'- \[[ x]\]', content))
        }

        issues = []
        warnings = []

        # Check for issues
        if not validation_results["has_user_scenarios"]:
            issues.append("Missing User Scenarios section")

        if not validation_results["has_requirements"]:
            issues.append("Missing Requirements section")

        if not validation_results["has_functional_requirements"]:
            issues.append("Missing Functional Requirements")

        if not validation_results["has_acceptance_scenarios"]:
            issues.append("Missing Acceptance Scenarios")

        # Check for warnings
        if validation_results["has_clarifications"]:
            count = content.count("[NEEDS CLARIFICATION")
            warnings.append(f"Contains {count} clarification markers")

        if validation_results["has_implementation_details"]:
            warnings.append("May contain implementation details (check for tech stack mentions)")

        if validation_results["checklist_items"] == 0:
            warnings.append("No checklist items found")

        is_valid = len(issues) == 0

        return self.create_success_response(
            message="Specification validation complete",
            data={
                "valid": is_valid,
                "issues": issues,
                "warnings": warnings,
                "validation_results": validation_results,
                "spec_path": str(path)
            }
        )


# Export tool functions
async def create_specification(
    feature_description: str,
    mark_clarifications: bool = True,
    settings = None
) -> ToolResponse:
    """Create a new feature specification."""
    tool = CreateSpecificationTool(settings)
    return await tool.execute(
        feature_description=feature_description,
        mark_clarifications=mark_clarifications
    )


async def validate_specification(
    spec_path: str,
    settings = None
) -> ToolResponse:
    """Validate a specification."""
    tool = ValidateSpecificationTool(settings)
    return await tool.execute(spec_path=spec_path)