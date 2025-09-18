"""Constitution and compliance tools for spec-kit MCP server."""

import asyncio
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from .base import BaseTool
from ..models import ToolResponse, ConstitutionCheckType
from ..exceptions import FileSystemError, ValidationError, ScriptExecutionError
from ..utils.scripts import ScriptRunner
from ..utils.git_ops import GitOperations
from ..config import Settings

logger = logging.getLogger(__name__)


class CheckConstitutionTool(BaseTool):
    """Check plans/implementations against constitutional requirements."""

    async def execute(
        self,
        check_type: str,
        artifact_path: str
    ) -> ToolResponse:
        """Check constitutional compliance."""
        try:
            # Validate inputs
            validated_inputs = await self.validate_inputs(
                check_type=check_type,
                artifact_path=artifact_path
            )

            check_type_enum = validated_inputs["check_type"]
            artifact_path_obj = validated_inputs["artifact_path"]

            # Check if scripts are available
            if not self.settings.scripts_path or not self.settings.scripts_path.exists():
                # Fallback to manual check
                return await self._manual_check_constitution(check_type_enum, artifact_path_obj)

            # Use spec-kit scripts
            script_runner = ScriptRunner(self.settings.scripts_path, self.settings.script_timeout)

            # Run constitution check script
            result = await script_runner.run_script(
                "check-constitution.sh",
                args=["--type", check_type, "--artifact", str(artifact_path_obj), "--json"],
                json_output=True,
                cwd=self.settings.repo_path
            )

            violations = result.get("violations", [])
            compliance_score = result.get("compliance_score", 0)
            recommendations = result.get("recommendations", [])

            # Create compliance report
            report_path = await self._create_compliance_report(
                check_type_enum,
                artifact_path_obj,
                violations,
                compliance_score,
                recommendations
            )

            return self.create_success_response(
                message=f"Constitution check completed for {check_type}",
                data={
                    "check_type": check_type,
                    "artifact_path": str(artifact_path_obj),
                    "violations": violations,
                    "compliance_score": compliance_score,
                    "recommendations": recommendations,
                    "report_path": str(report_path)
                },
                artifacts=[report_path]
            )

        except Exception as e:
            logger.error(f"Failed to check constitution using scripts: {e}")
            # Try manual fallback
            return await self._manual_check_constitution(
                ConstitutionCheckType(check_type),
                Path(artifact_path)
            )

    async def validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize inputs."""
        check_type = kwargs.get("check_type", "").strip()
        artifact_path = kwargs.get("artifact_path", "").strip()

        if not check_type:
            raise ValidationError("check_type is required")
        if not artifact_path:
            raise ValidationError("artifact_path is required")

        # Validate check_type
        try:
            check_type_enum = ConstitutionCheckType(check_type)
        except ValueError:
            valid_types = [t.value for t in ConstitutionCheckType]
            raise ValidationError(
                f"Invalid check_type: {check_type}",
                suggestions=[f"Use one of: {', '.join(valid_types)}"]
            )

        # Validate and resolve artifact path
        artifact_path_obj = Path(artifact_path)
        if not artifact_path_obj.is_absolute():
            artifact_path_obj = self.settings.repo_path / artifact_path

        artifact_path_obj = self.validate_path(artifact_path_obj, must_exist=True)

        return {
            "check_type": check_type_enum,
            "artifact_path": artifact_path_obj
        }

    async def _manual_check_constitution(
        self,
        check_type: ConstitutionCheckType,
        artifact_path: Path
    ) -> ToolResponse:
        """Manually check constitution without scripts."""
        # Read the artifact content
        try:
            content = artifact_path.read_text()
        except Exception as e:
            raise FileSystemError(
                f"Failed to read artifact: {artifact_path}",
                details={"path": str(artifact_path), "error": str(e)}
            )

        # Perform constitution check based on type
        violations = []
        recommendations = []
        compliance_score = 100  # Start with perfect score and deduct

        if check_type == ConstitutionCheckType.SIMPLICITY:
            violations, recommendations, compliance_score = self._check_simplicity(content)
        elif check_type == ConstitutionCheckType.ARCHITECTURE:
            violations, recommendations, compliance_score = self._check_architecture(content)
        elif check_type == ConstitutionCheckType.TESTING:
            violations, recommendations, compliance_score = self._check_testing(content)
        elif check_type == ConstitutionCheckType.OBSERVABILITY:
            violations, recommendations, compliance_score = self._check_observability(content)
        elif check_type == ConstitutionCheckType.VERSIONING:
            violations, recommendations, compliance_score = self._check_versioning(content)

        # Create compliance report
        report_path = await self._create_compliance_report(
            check_type,
            artifact_path,
            violations,
            compliance_score,
            recommendations
        )

        return self.create_success_response(
            message=f"Constitution check completed for {check_type.value}",
            data={
                "check_type": check_type.value,
                "artifact_path": str(artifact_path),
                "violations": violations,
                "compliance_score": compliance_score,
                "recommendations": recommendations,
                "report_path": str(report_path)
            },
            artifacts=[report_path]
        )

    def _check_simplicity(self, content: str) -> tuple[List[Dict], List[str], int]:
        """Check simplicity violations."""
        violations = []
        recommendations = []
        score = 100

        # Check for maximum 3 projects
        project_count = len(re.findall(r'###\s*Project\s*\d+', content))
        if project_count > 3:
            violations.append({
                "rule": "Maximum 3 projects",
                "violation": f"Found {project_count} projects",
                "severity": "high"
            })
            recommendations.append("Consolidate projects to maximum 3")
            score -= 20

        # Check for framework usage patterns
        if re.search(r'wrapper\s+class', content, re.IGNORECASE):
            violations.append({
                "rule": "Direct framework usage",
                "violation": "Wrapper classes detected",
                "severity": "medium"
            })
            recommendations.append("Use framework directly without wrapper classes")
            score -= 15

        # Check for unnecessary patterns
        patterns = ["Repository", "Unit of Work", "UoW"]
        for pattern in patterns:
            if re.search(pattern, content):
                violations.append({
                    "rule": "Avoid unnecessary patterns",
                    "violation": f"{pattern} pattern detected",
                    "severity": "medium"
                })
                recommendations.append(f"Remove {pattern} pattern unless proven necessary")
                score -= 10

        return violations, recommendations, max(0, score)

    def _check_architecture(self, content: str) -> tuple[List[Dict], List[str], int]:
        """Check architecture violations."""
        violations = []
        recommendations = []
        score = 100

        # Check for library structure
        if not re.search(r'library', content, re.IGNORECASE):
            violations.append({
                "rule": "Every feature as library",
                "violation": "No library structure mentioned",
                "severity": "high"
            })
            recommendations.append("Structure feature as a library")
            score -= 25

        # Check for CLI presence
        if not re.search(r'CLI|command.?line', content, re.IGNORECASE):
            violations.append({
                "rule": "CLI per library",
                "violation": "No CLI mentioned",
                "severity": "medium"
            })
            recommendations.append("Add CLI interface for the library")
            score -= 15

        # Check for documentation format
        if not re.search(r'llms\.txt', content):
            violations.append({
                "rule": "llms.txt format documentation",
                "violation": "llms.txt format not mentioned",
                "severity": "low"
            })
            recommendations.append("Plan documentation in llms.txt format")
            score -= 10

        return violations, recommendations, max(0, score)

    def _check_testing(self, content: str) -> tuple[List[Dict], List[str], int]:
        """Check testing violations."""
        violations = []
        recommendations = []
        score = 100

        # Check for TDD enforcement
        if not re.search(r'RED.?GREEN.?Refactor|test.?first', content, re.IGNORECASE):
            violations.append({
                "rule": "RED-GREEN-Refactor cycle",
                "violation": "TDD cycle not mentioned",
                "severity": "critical"
            })
            recommendations.append("Enforce RED-GREEN-Refactor TDD cycle")
            score -= 30

        # Check for test order
        test_order = ["Contract", "Integration", "E2E", "Unit"]
        content_lower = content.lower()
        for test_type in test_order:
            if test_type.lower() not in content_lower:
                violations.append({
                    "rule": "Complete test coverage",
                    "violation": f"{test_type} tests not mentioned",
                    "severity": "medium"
                })
                recommendations.append(f"Include {test_type} tests in the plan")
                score -= 10

        # Check for real dependencies
        if re.search(r'mock|stub|fake', content, re.IGNORECASE):
            violations.append({
                "rule": "Real dependencies in tests",
                "violation": "Mocking detected",
                "severity": "medium"
            })
            recommendations.append("Use real dependencies (actual DBs, not mocks)")
            score -= 15

        return violations, recommendations, max(0, score)

    def _check_observability(self, content: str) -> tuple[List[Dict], List[str], int]:
        """Check observability violations."""
        violations = []
        recommendations = []
        score = 100

        # Check for structured logging
        if not re.search(r'structured\s+log', content, re.IGNORECASE):
            violations.append({
                "rule": "Structured logging",
                "violation": "Structured logging not mentioned",
                "severity": "medium"
            })
            recommendations.append("Include structured logging")
            score -= 20

        # Check for error context
        if not re.search(r'error\s+context', content, re.IGNORECASE):
            violations.append({
                "rule": "Error context",
                "violation": "Error context not mentioned",
                "severity": "medium"
            })
            recommendations.append("Ensure sufficient error context")
            score -= 15

        return violations, recommendations, max(0, score)

    def _check_versioning(self, content: str) -> tuple[List[Dict], List[str], int]:
        """Check versioning violations."""
        violations = []
        recommendations = []
        score = 100

        # Check for version number
        if not re.search(r'version|v\d+\.\d+\.\d+', content, re.IGNORECASE):
            violations.append({
                "rule": "Version number assignment",
                "violation": "No version number mentioned",
                "severity": "medium"
            })
            recommendations.append("Assign version number (MAJOR.MINOR.BUILD)")
            score -= 20

        # Check for build increment
        if not re.search(r'BUILD\s+increment', content, re.IGNORECASE):
            violations.append({
                "rule": "BUILD increment strategy",
                "violation": "BUILD increment strategy not mentioned",
                "severity": "low"
            })
            recommendations.append("Plan BUILD increment on every change")
            score -= 10

        return violations, recommendations, max(0, score)

    async def _create_compliance_report(
        self,
        check_type: ConstitutionCheckType,
        artifact_path: Path,
        violations: List[Dict],
        compliance_score: int,
        recommendations: List[str]
    ) -> Path:
        """Create compliance report."""
        # Get feature directory
        git_ops = GitOperations(self.settings.repo_path)
        branch_name = await git_ops.get_current_branch()
        feature_dir = self.get_feature_dir(branch_name)

        # Create compliance reports directory
        reports_dir = feature_dir / "compliance"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Create report file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"{check_type.value}_check_{timestamp}.md"

        # Generate report content
        report_content = self._generate_report_content(
            check_type,
            artifact_path,
            violations,
            compliance_score,
            recommendations
        )

        report_file.write_text(report_content)
        return report_file

    def _generate_report_content(
        self,
        check_type: ConstitutionCheckType,
        artifact_path: Path,
        violations: List[Dict],
        compliance_score: int,
        recommendations: List[str]
    ) -> str:
        """Generate compliance report content."""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "PASS" if compliance_score >= 80 else "FAIL" if compliance_score < 50 else "WARNING"

        content = f"""# Constitution Check Report: {check_type.value.title()}

**Date**: {date}
**Artifact**: `{artifact_path.name}`
**Score**: {compliance_score}/100
**Status**: {status}

## Summary
Constitution compliance check for {check_type.value} requirements.

## Violations Found
"""

        if violations:
            for i, violation in enumerate(violations, 1):
                content += f"""
### {i}. {violation['rule']}
**Severity**: {violation['severity'].upper()}
**Issue**: {violation['violation']}
"""
        else:
            content += "\nNo violations found."

        content += "\n\n## Recommendations"
        if recommendations:
            for rec in recommendations:
                content += f"\n- {rec}"
        else:
            content += "\nNo recommendations."

        content += f"""

## Compliance Score Breakdown
- Score: {compliance_score}/100
- Status: {status}
- Threshold: 80+ (Pass), 50-79 (Warning), <50 (Fail)

## Next Steps
"""

        if compliance_score < 50:
            content += "- **CRITICAL**: Address all violations before proceeding"
        elif compliance_score < 80:
            content += "- Address medium and high severity violations"
        else:
            content += "- Constitution requirements satisfied"

        content += f"""
- Review recommendations for improvements
- Re-run check after making changes

## Constitution Rules Reference
### {check_type.value.title()} Requirements
"""

        # Add specific rules reference based on check type
        if check_type == ConstitutionCheckType.SIMPLICITY:
            content += """
- Maximum 3 projects per feature
- Use framework directly (no wrapper classes)
- Single data model (no DTOs unless serialization differs)
- Avoid patterns (Repository/UoW) without proven need
"""
        elif check_type == ConstitutionCheckType.ARCHITECTURE:
            content += """
- Every feature as library
- CLI per library with --help/--version/--format
- Library documentation in llms.txt format
- Clear separation of concerns
"""
        elif check_type == ConstitutionCheckType.TESTING:
            content += """
- RED-GREEN-Refactor cycle enforced
- Tests MUST fail first before implementation
- Order: Contract → Integration → E2E → Unit
- Real dependencies used (actual DBs, not mocks)
- Integration tests for new libraries and contract changes
"""
        elif check_type == ConstitutionCheckType.OBSERVABILITY:
            content += """
- Structured logging included
- Frontend logs flow to backend (unified stream)
- Sufficient error context provided
- Monitoring and alerting planned
"""
        elif check_type == ConstitutionCheckType.VERSIONING:
            content += """
- Version number assigned (MAJOR.MINOR.BUILD)
- BUILD increments on every change
- Breaking changes handled with parallel tests
- Migration plan for breaking changes
"""

        return content


class TrackComplexityTool(BaseTool):
    """Track and justify necessary complexity violations."""

    async def execute(
        self,
        violation: str,
        justification: str,
        alternatives_rejected: str
    ) -> ToolResponse:
        """Track complexity violations."""
        try:
            # Validate inputs
            validated_inputs = await self.validate_inputs(
                violation=violation,
                justification=justification,
                alternatives_rejected=alternatives_rejected
            )

            # Get current feature directory
            git_ops = GitOperations(self.settings.repo_path)
            branch_name = await git_ops.get_current_branch()

            if not branch_name or branch_name in ["main", "master"]:
                raise ValidationError(
                    "Not on a feature branch",
                    suggestions=["Switch to a feature branch first"]
                )

            feature_dir = self.get_feature_dir(branch_name)

            # Create or update complexity tracking file
            tracking_file = await self._create_complexity_tracking(
                feature_dir,
                validated_inputs["violation"],
                validated_inputs["justification"],
                validated_inputs["alternatives_rejected"]
            )

            return self.create_success_response(
                message="Complexity violation tracked",
                data={
                    "violation": validated_inputs["violation"],
                    "justification": validated_inputs["justification"],
                    "alternatives_rejected": validated_inputs["alternatives_rejected"],
                    "tracking_file": str(tracking_file),
                    "feature_dir": str(feature_dir)
                },
                artifacts=[tracking_file]
            )

        except Exception as e:
            logger.error(f"Failed to track complexity: {e}")
            return self.create_error_response(
                message=f"Failed to track complexity: {str(e)}",
                error_type="ComplexityTrackingError",
                details={"error": str(e)}
            )

    async def validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize inputs."""
        violation = kwargs.get("violation", "").strip()
        justification = kwargs.get("justification", "").strip()
        alternatives_rejected = kwargs.get("alternatives_rejected", "").strip()

        if not violation:
            raise ValidationError("violation is required")
        if not justification:
            raise ValidationError("justification is required")
        if not alternatives_rejected:
            raise ValidationError("alternatives_rejected is required")

        if len(violation) < 5:
            raise ValidationError("violation must be at least 5 characters")
        if len(justification) < 10:
            raise ValidationError("justification must be at least 10 characters")
        if len(alternatives_rejected) < 10:
            raise ValidationError("alternatives_rejected must be at least 10 characters")

        return {
            "violation": violation,
            "justification": justification,
            "alternatives_rejected": alternatives_rejected
        }

    async def _create_complexity_tracking(
        self,
        feature_dir: Path,
        violation: str,
        justification: str,
        alternatives_rejected: str
    ) -> Path:
        """Create or update complexity tracking file."""
        tracking_file = feature_dir / "complexity_tracking.md"

        # Check if file exists
        if tracking_file.exists():
            # Append to existing file
            content = tracking_file.read_text()
            # Add new violation
            violation_count = len(re.findall(r'^## Violation \d+', content, re.MULTILINE)) + 1
        else:
            # Create new file
            violation_count = 1
            content = self._create_tracking_header(feature_dir.name)

        # Add new violation entry
        new_entry = self._create_violation_entry(
            violation_count, violation, justification, alternatives_rejected
        )

        content += new_entry
        tracking_file.write_text(content)

        return tracking_file

    def _create_tracking_header(self, feature_name: str) -> str:
        """Create tracking file header."""
        date = datetime.now().strftime("%Y-%m-%d")
        return f"""# Complexity Tracking: {feature_name}

**Date**: {date}
**Purpose**: Track and justify necessary complexity violations

## Overview
This document tracks cases where the feature necessarily violates simplicity principles. Each violation must be:
1. Clearly documented
2. Thoroughly justified
3. Show that simpler alternatives were considered and rejected

"""

    def _create_violation_entry(
        self,
        violation_count: int,
        violation: str,
        justification: str,
        alternatives_rejected: str
    ) -> str:
        """Create violation entry."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
## Violation {violation_count}
**Timestamp**: {timestamp}
**Violation**: {violation}

### Justification
{justification}

### Alternatives Rejected
{alternatives_rejected}

### Review Status
- [ ] Justified complexity
- [ ] Simpler alternatives exhausted
- [ ] Benefits outweigh complexity cost
- [ ] Documentation updated

---

"""


# Export tool functions
async def check_constitution(
    check_type: str,
    artifact_path: str,
    settings: Settings = None
) -> ToolResponse:
    """Check constitutional compliance."""
    tool = CheckConstitutionTool(settings)
    return await tool.execute(
        check_type=check_type,
        artifact_path=artifact_path
    )


async def track_complexity(
    violation: str,
    justification: str,
    alternatives_rejected: str,
    settings: Settings = None
) -> ToolResponse:
    """Track complexity violations."""
    tool = TrackComplexityTool(settings)
    return await tool.execute(
        violation=violation,
        justification=justification,
        alternatives_rejected=alternatives_rejected
    )