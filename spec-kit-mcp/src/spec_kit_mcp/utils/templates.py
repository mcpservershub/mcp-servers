"""Template processing utilities."""

from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template, TemplateError
import logging
from datetime import datetime

from ..exceptions import TemplateProcessingError

logger = logging.getLogger(__name__)


class TemplateProcessor:
    """Process templates using Jinja2."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self.env.filters['snake_case'] = self._snake_case
        self.env.filters['kebab_case'] = self._kebab_case
        self.env.filters['camel_case'] = self._camel_case

        # Add global variables
        self.env.globals['now'] = datetime.now

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> str:
        """Render a template with the given context."""
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**context)

            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(rendered)
                logger.info(f"Wrote rendered template to {output_path}")

            return rendered

        except TemplateError as e:
            raise TemplateProcessingError(
                f"Failed to process template {template_name}",
                details={"error": str(e), "template": template_name}
            )
        except Exception as e:
            raise TemplateProcessingError(
                f"Unexpected error processing template {template_name}",
                details={"error": str(e)}
            )

    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template string."""
        try:
            template = Template(template_string)
            return template.render(**context)
        except TemplateError as e:
            raise TemplateProcessingError(
                f"Failed to process template string",
                details={"error": str(e)}
            )

    def process_spec_template(
        self,
        feature_description: str,
        branch_name: str,
        output_path: Path
    ) -> Path:
        """Process the specification template."""
        context = {
            "feature_name": self._extract_feature_name(branch_name),
            "feature_branch": branch_name,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "feature_description": feature_description,
            "status": "Draft",
        }

        self.render_template("spec-template.md", context, output_path)
        return output_path

    def process_plan_template(
        self,
        branch_name: str,
        tech_stack: str,
        language: str,
        framework: str,
        storage: Optional[str],
        project_type: str,
        output_path: Path
    ) -> Path:
        """Process the plan template."""
        context = {
            "feature_name": self._extract_feature_name(branch_name),
            "feature_branch": branch_name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tech_stack": tech_stack,
            "language": language,
            "framework": framework,
            "storage": storage or "N/A",
            "project_type": project_type,
        }

        self.render_template("plan-template.md", context, output_path)
        return output_path

    def process_tasks_template(
        self,
        branch_name: str,
        tasks_data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Process the tasks template."""
        context = {
            "feature_name": self._extract_feature_name(branch_name),
            "feature_branch": branch_name,
            **tasks_data
        }

        self.render_template("tasks-template.md", context, output_path)
        return output_path

    def _extract_feature_name(self, branch_name: str) -> str:
        """Extract feature name from branch name."""
        # Remove number prefix (e.g., "001-my-feature" -> "my-feature")
        parts = branch_name.split('-', 1)
        if len(parts) > 1:
            return parts[1].replace('-', ' ').title()
        return branch_name.replace('-', ' ').title()

    @staticmethod
    def _snake_case(text: str) -> str:
        """Convert text to snake_case."""
        return text.lower().replace(' ', '_').replace('-', '_')

    @staticmethod
    def _kebab_case(text: str) -> str:
        """Convert text to kebab-case."""
        return text.lower().replace(' ', '-').replace('_', '-')

    @staticmethod
    def _camel_case(text: str) -> str:
        """Convert text to CamelCase."""
        return ''.join(word.capitalize() for word in text.replace('-', ' ').replace('_', ' ').split())

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        template_path = self.templates_dir / template_name
        return template_path.exists() and template_path.is_file()