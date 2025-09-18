"""Input and path validation utilities."""

from pathlib import Path
from typing import Optional, Any, List, Dict
import re

from ..exceptions import ValidationError


class PathValidator:
    """Validate file system paths."""

    @staticmethod
    def validate_path(
        path: Path,
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
        allowed_extensions: Optional[List[str]] = None
    ) -> Path:
        """Validate a path with various constraints."""
        try:
            resolved_path = path.resolve()
        except Exception as e:
            raise ValidationError(
                f"Invalid path: {path}",
                details={"path": str(path), "error": str(e)}
            )

        if must_exist and not resolved_path.exists():
            raise ValidationError(
                f"Path does not exist: {path}",
                details={"path": str(path)},
                suggestions=["Check the path and try again"]
            )

        if must_be_file and not resolved_path.is_file():
            raise ValidationError(
                f"Path is not a file: {path}",
                details={"path": str(path)},
                suggestions=["Provide a file path, not a directory"]
            )

        if must_be_dir and not resolved_path.is_dir():
            raise ValidationError(
                f"Path is not a directory: {path}",
                details={"path": str(path)},
                suggestions=["Provide a directory path, not a file"]
            )

        if allowed_extensions and resolved_path.is_file():
            if not any(str(path).endswith(ext) for ext in allowed_extensions):
                raise ValidationError(
                    f"Invalid file extension: {path}",
                    details={"allowed_extensions": allowed_extensions},
                    suggestions=[f"Use a file with extension: {', '.join(allowed_extensions)}"]
                )

        return resolved_path

    @staticmethod
    def is_safe_path(base_path: Path, target_path: Path) -> bool:
        """Check if target path is within base path (prevent directory traversal)."""
        try:
            base_resolved = base_path.resolve()
            target_resolved = target_path.resolve()
            target_resolved.relative_to(base_resolved)
            return True
        except ValueError:
            return False


class InputValidator:
    """Validate various input types."""

    @staticmethod
    def validate_branch_name(branch_name: str) -> str:
        """Validate feature branch name format."""
        pattern = r'^\d{3}-[a-z0-9-]+$'
        if not re.match(pattern, branch_name):
            raise ValidationError(
                f"Invalid branch name format: {branch_name}",
                details={"expected_format": "###-feature-name"},
                suggestions=[
                    "Use format like '001-my-feature'",
                    "Use lowercase letters, numbers, and hyphens only"
                ]
            )
        return branch_name

    @staticmethod
    def validate_project_name(name: str) -> str:
        """Validate project name."""
        if not name:
            raise ValidationError("Project name cannot be empty")

        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name):
            raise ValidationError(
                f"Invalid project name: {name}",
                details={"requirements": "Must start with letter, contain only letters, numbers, hyphens, underscores"},
                suggestions=["Use a name like 'my-project' or 'my_project'"]
            )

        if len(name) > 100:
            raise ValidationError(
                f"Project name too long: {name}",
                details={"max_length": 100},
                suggestions=["Use a shorter name"]
            )

        return name

    @staticmethod
    def validate_task_id(task_id: str) -> str:
        """Validate task ID format."""
        if not re.match(r'^T\d{3}$', task_id):
            raise ValidationError(
                f"Invalid task ID format: {task_id}",
                details={"expected_format": "T###"},
                suggestions=["Use format like 'T001', 'T002', etc."]
            )
        return task_id

    @staticmethod
    def validate_feature_description(description: str) -> str:
        """Validate feature description."""
        if not description or not description.strip():
            raise ValidationError(
                "Feature description cannot be empty",
                suggestions=["Provide a meaningful description of the feature"]
            )

        cleaned = description.strip()

        if len(cleaned) < 10:
            raise ValidationError(
                "Feature description too short",
                details={"min_length": 10},
                suggestions=["Provide more detail about the feature"]
            )

        if len(cleaned) > 5000:
            raise ValidationError(
                "Feature description too long",
                details={"max_length": 5000},
                suggestions=["Be more concise in your description"]
            )

        return cleaned

    @staticmethod
    def validate_tech_stack(tech_stack: str) -> str:
        """Validate technology stack description."""
        if not tech_stack or not tech_stack.strip():
            raise ValidationError(
                "Technology stack cannot be empty",
                suggestions=["Specify the technologies you want to use"]
            )

        cleaned = tech_stack.strip()

        if len(cleaned) < 5:
            raise ValidationError(
                "Technology stack description too short",
                details={"min_length": 5},
                suggestions=["Provide more detail about the technology choices"]
            )

        return cleaned

    @staticmethod
    def validate_enum_value(value: str, enum_class: Any, field_name: str) -> str:
        """Validate that a value is in an enum."""
        valid_values = [e.value for e in enum_class]
        if value not in valid_values:
            raise ValidationError(
                f"Invalid {field_name}: {value}",
                details={"valid_values": valid_values},
                suggestions=[f"Use one of: {', '.join(valid_values)}"]
            )
        return value

    @staticmethod
    def validate_dict(data: Any, field_name: str) -> Dict:
        """Validate that data is a dictionary."""
        if not isinstance(data, dict):
            raise ValidationError(
                f"{field_name} must be a dictionary",
                details={"received_type": type(data).__name__},
                suggestions=["Provide a dictionary/object"]
            )
        return data

    @staticmethod
    def validate_list(data: Any, field_name: str, min_items: int = 0, max_items: Optional[int] = None) -> List:
        """Validate that data is a list with optional size constraints."""
        if not isinstance(data, list):
            raise ValidationError(
                f"{field_name} must be a list",
                details={"received_type": type(data).__name__},
                suggestions=["Provide a list/array"]
            )

        if len(data) < min_items:
            raise ValidationError(
                f"{field_name} must have at least {min_items} items",
                details={"received": len(data), "minimum": min_items}
            )

        if max_items and len(data) > max_items:
            raise ValidationError(
                f"{field_name} must have at most {max_items} items",
                details={"received": len(data), "maximum": max_items}
            )

        return data