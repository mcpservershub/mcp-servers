"""Documentation tools for spec-kit MCP server."""

import asyncio
import re
import json
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from .base import BaseTool
from ..models import ToolResponse, DocumentFormat, ContractType
from ..exceptions import FileSystemError, ValidationError, ScriptExecutionError
from ..utils.scripts import ScriptRunner
from ..utils.templates import TemplateProcessor
from ..utils.git_ops import GitOperations
from ..config import Settings

logger = logging.getLogger(__name__)


class GenerateQuickstartTool(BaseTool):
    """Generate comprehensive quickstart documentation from feature specs."""

    async def execute(
        self,
        include_test_scenarios: bool = True,
        format: str = "markdown"
    ) -> ToolResponse:
        """Generate quickstart documentation."""
        try:
            # Validate inputs
            validated_inputs = await self.validate_inputs(
                include_test_scenarios=include_test_scenarios,
                format=format
            )

            format_enum = validated_inputs["format"]
            include_test_scenarios = validated_inputs["include_test_scenarios"]

            # Check if scripts are available
            if not self.settings.scripts_path or not self.settings.scripts_path.exists():
                # Fallback to manual generation
                return await self._manual_generate_quickstart(include_test_scenarios, format_enum)

            # Use spec-kit scripts
            script_runner = ScriptRunner(self.settings.scripts_path, self.settings.script_timeout)

            # Run quickstart generation script
            result = await script_runner.run_script(
                "generate-quickstart.sh",
                args=[
                    "--format", format_enum.value,
                    "--test-scenarios" if include_test_scenarios else "--no-test-scenarios",
                    "--json"
                ],
                json_output=True,
                cwd=self.settings.repo_path
            )

            quickstart_file = result.get("quickstart_file")
            feature_dir = result.get("feature_dir")
            sections_generated = result.get("sections_generated", [])

            if not quickstart_file:
                raise ScriptExecutionError(
                    "Script did not return expected output",
                    details={"result": result}
                )

            return self.create_success_response(
                message="Quickstart documentation generated",
                data={
                    "quickstart_file": quickstart_file,
                    "feature_dir": feature_dir,
                    "format": format_enum.value,
                    "include_test_scenarios": include_test_scenarios,
                    "sections_generated": sections_generated
                },
                artifacts=[Path(quickstart_file)]
            )

        except Exception as e:
            logger.error(f"Failed to generate quickstart using scripts: {e}")
            # Try manual fallback
            return await self._manual_generate_quickstart(
                include_test_scenarios,
                DocumentFormat(format) if isinstance(format, str) else format
            )

    async def validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize inputs."""
        format_str = kwargs.get("format", "markdown").strip()
        include_test_scenarios = kwargs.get("include_test_scenarios", True)

        # Validate format
        try:
            format_enum = DocumentFormat(format_str)
        except ValueError:
            valid_formats = [f.value for f in DocumentFormat]
            raise ValidationError(
                f"Invalid format: {format_str}",
                suggestions=[f"Use one of: {', '.join(valid_formats)}"]
            )

        return {
            "format": format_enum,
            "include_test_scenarios": bool(include_test_scenarios)
        }

    async def _manual_generate_quickstart(
        self,
        include_test_scenarios: bool,
        format_enum: DocumentFormat
    ) -> ToolResponse:
        """Manually generate quickstart without scripts."""
        # Get current branch and feature directory
        git_ops = GitOperations(self.settings.repo_path)
        branch_name = await git_ops.get_current_branch()

        if not branch_name or branch_name in ["main", "master"]:
            raise ValidationError(
                "Not on a feature branch",
                suggestions=["Switch to a feature branch first"]
            )

        feature_dir = self.get_feature_dir(branch_name)
        spec_file = self.get_spec_file(branch_name)
        plan_file = self.get_plan_file(branch_name)

        # Check required files exist
        if not spec_file.exists():
            raise ValidationError(
                f"Feature specification not found: {spec_file}",
                suggestions=["Run create_specification first"]
            )

        # Read feature documents
        feature_docs = await self._read_feature_documents(feature_dir)

        # Generate quickstart content
        quickstart_content = await self._generate_quickstart_content(
            feature_docs=feature_docs,
            branch_name=branch_name,
            include_test_scenarios=include_test_scenarios
        )

        # Create quickstart file
        quickstart_file = feature_dir / f"quickstart.{format_enum.value}"

        if format_enum == DocumentFormat.MARKDOWN:
            quickstart_file.write_text(quickstart_content)
        else:
            # For other formats, convert from markdown
            converted_content = await self._convert_format(quickstart_content, format_enum)
            quickstart_file.write_text(converted_content)

        return self.create_success_response(
            message="Quickstart documentation generated",
            data={
                "quickstart_file": str(quickstart_file),
                "feature_dir": str(feature_dir),
                "format": format_enum.value,
                "include_test_scenarios": include_test_scenarios,
                "sections_generated": ["prerequisites", "installation", "configuration", "basic_usage"]
            },
            artifacts=[quickstart_file]
        )

    async def _read_feature_documents(self, feature_dir: Path) -> Dict[str, str]:
        """Read all feature documents."""
        docs = {}

        # Read core documents
        doc_files = {
            "spec": "spec.md",
            "plan": "plan.md",
            "data_model": "data-model.md",
            "research": "research.md"
        }

        for doc_key, filename in doc_files.items():
            doc_path = feature_dir / filename
            if doc_path.exists():
                docs[doc_key] = doc_path.read_text()

        # Read contracts
        contracts_dir = feature_dir / "contracts"
        if contracts_dir.exists():
            contracts = []
            for contract_file in contracts_dir.glob("*.md"):
                contracts.append({
                    "name": contract_file.stem,
                    "content": contract_file.read_text()
                })
            docs["contracts"] = contracts

        return docs

    async def _generate_quickstart_content(
        self,
        feature_docs: Dict[str, Any],
        branch_name: str,
        include_test_scenarios: bool
    ) -> str:
        """Generate quickstart documentation content."""
        feature_name = self._extract_feature_name(branch_name)
        date = datetime.now().strftime("%Y-%m-%d")

        # Extract information from documents
        overview = self._extract_overview(feature_docs)
        tech_stack = self._extract_tech_stack(feature_docs)
        dependencies = self._extract_dependencies(feature_docs)
        usage_examples = self._extract_usage_examples(feature_docs)
        test_scenarios = self._extract_test_scenarios(feature_docs) if include_test_scenarios else []

        content = f"""# Quick Start: {feature_name}

**Generated**: {date}
**Feature Branch**: `{branch_name}`

## Overview
{overview}

## Prerequisites

### System Requirements
{self._generate_system_requirements(tech_stack)}

### Dependencies
{self._generate_dependencies_section(dependencies)}

## Installation

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd <project-directory>

# Switch to feature branch
git checkout {branch_name}
```

### 2. Install Dependencies
{self._generate_installation_commands(tech_stack, dependencies)}

### 3. Configuration
{self._generate_configuration_section(feature_docs)}

## Basic Usage

{self._generate_basic_usage(usage_examples, tech_stack)}

## API Reference

{self._generate_api_reference(feature_docs.get('contracts', []))}

## Development

### Development Setup
```bash
# Install development dependencies
{self._generate_dev_setup_commands(tech_stack)}

# Run in development mode
{self._generate_dev_run_commands(tech_stack)}
```

### Testing
```bash
# Run all tests
{self._generate_test_commands(tech_stack)}

# Run specific test types
{self._generate_specific_test_commands(tech_stack)}
```
"""

        if include_test_scenarios and test_scenarios:
            content += "\n## Test Scenarios\n\n"
            for i, scenario in enumerate(test_scenarios, 1):
                content += f"### {i}. {scenario['name']}\n"
                content += f"{scenario['description']}\n\n"
                if 'steps' in scenario:
                    content += "**Steps**:\n"
                    for step in scenario['steps']:
                        content += f"1. {step}\n"
                    content += "\n"

        content += f"""
## Troubleshooting

### Common Issues

{self._generate_troubleshooting_section(tech_stack)}

### Getting Help

- Check the [specification](spec.md) for detailed requirements
- Review the [implementation plan](plan.md) for technical details
- Check [data model](data-model.md) for entity relationships
- Review contracts in the [contracts/](contracts/) directory

## Next Steps

1. **Explore the API**: Use the endpoints defined in the contracts
2. **Customize Configuration**: Adjust settings for your environment
3. **Extend Functionality**: Add new features following the established patterns
4. **Run Tests**: Ensure everything works in your environment

## Support

For support and questions:
- Review the feature documentation in the `specs/{branch_name}/` directory
- Check the implementation plan for architectural decisions
- Refer to the research document for technical background
"""

        return content

    def _extract_feature_name(self, branch_name: str) -> str:
        """Extract feature name from branch name."""
        parts = branch_name.split('-', 1)
        if len(parts) > 1:
            return parts[1].replace('-', ' ').title()
        return branch_name.replace('-', ' ').title()

    def _extract_overview(self, feature_docs: Dict[str, Any]) -> str:
        """Extract feature overview from documents."""
        spec_content = feature_docs.get("spec", "")
        plan_content = feature_docs.get("plan", "")

        # Try to extract from spec first
        if spec_content:
            # Look for summary or overview section
            overview_match = re.search(r'##\s*(?:Summary|Overview)\s*\n([^#]+)', spec_content, re.IGNORECASE)
            if overview_match:
                return overview_match.group(1).strip()

        # Fallback to plan summary
        if plan_content:
            summary_match = re.search(r'##\s*Summary\s*\n([^#]+)', plan_content, re.IGNORECASE)
            if summary_match:
                return summary_match.group(1).strip()

        return "This feature provides enhanced functionality to the application."

    def _extract_tech_stack(self, feature_docs: Dict[str, Any]) -> Dict[str, str]:
        """Extract technology stack information."""
        plan_content = feature_docs.get("plan", "")
        tech_stack = {}

        if plan_content:
            # Extract language
            lang_match = re.search(r'\*\*Language/Version\*\*:\s*([^\n]+)', plan_content)
            if lang_match:
                tech_stack["language"] = lang_match.group(1).strip()

            # Extract framework
            framework_match = re.search(r'\*\*Primary Dependencies\*\*:\s*([^\n]+)', plan_content)
            if framework_match:
                tech_stack["framework"] = framework_match.group(1).strip()

            # Extract storage
            storage_match = re.search(r'\*\*Storage\*\*:\s*([^\n]+)', plan_content)
            if storage_match and "N/A" not in storage_match.group(1):
                tech_stack["storage"] = storage_match.group(1).strip()

        return tech_stack

    def _extract_dependencies(self, feature_docs: Dict[str, Any]) -> List[str]:
        """Extract project dependencies."""
        dependencies = []
        plan_content = feature_docs.get("plan", "")

        if plan_content:
            # Look for dependencies section
            deps_match = re.search(r'##\s*Dependencies.*?\n([^#]+)', plan_content, re.IGNORECASE | re.DOTALL)
            if deps_match:
                deps_text = deps_match.group(1)
                # Extract items from lists
                deps = re.findall(r'-\s*([^\n]+)', deps_text)
                dependencies.extend([dep.strip() for dep in deps])

        return dependencies

    def _extract_usage_examples(self, feature_docs: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract usage examples from contracts."""
        examples = []
        contracts = feature_docs.get("contracts", [])

        for contract in contracts:
            content = contract.get("content", "")
            # Look for example sections
            example_matches = re.findall(r'```(?:bash|json|curl)\s*\n([^`]+)```', content)
            for example in example_matches:
                examples.append({
                    "type": "API",
                    "content": example.strip()
                })

        return examples

    def _extract_test_scenarios(self, feature_docs: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract test scenarios from documents."""
        scenarios = []
        spec_content = feature_docs.get("spec", "")
        quickstart_content = feature_docs.get("quickstart", "")

        # Look for scenario patterns
        for content in [spec_content, quickstart_content]:
            if content:
                scenario_matches = re.findall(
                    r'##\s*([^\n]*[Ss]cenario[^\n]*)\s*\n([^#]+)',
                    content,
                    re.IGNORECASE
                )
                for name, description in scenario_matches:
                    scenarios.append({
                        "name": name.strip(),
                        "description": description.strip()
                    })

        return scenarios

    def _generate_system_requirements(self, tech_stack: Dict[str, str]) -> str:
        """Generate system requirements section."""
        language = tech_stack.get("language", "")
        reqs = []

        if "python" in language.lower():
            reqs.append("- Python 3.8 or higher")
            reqs.append("- pip package manager")
        elif "node" in language.lower() or "javascript" in language.lower():
            reqs.append("- Node.js 16 or higher")
            reqs.append("- npm or yarn package manager")
        elif "java" in language.lower():
            reqs.append("- Java 11 or higher")
            reqs.append("- Maven or Gradle")
        else:
            reqs.append(f"- {language} runtime")

        reqs.append("- Git for version control")
        return "\n".join(reqs) if reqs else "- Standard development environment"

    def _generate_dependencies_section(self, dependencies: List[str]) -> str:
        """Generate dependencies section."""
        if not dependencies:
            return "- No additional dependencies required"
        return "\n".join([f"- {dep}" for dep in dependencies])

    def _generate_installation_commands(self, tech_stack: Dict[str, str], dependencies: List[str]) -> str:
        """Generate installation commands."""
        language = tech_stack.get("language", "").lower()
        commands = []

        if "python" in language:
            commands.append("# Install Python dependencies")
            commands.append("pip install -r requirements.txt")
            commands.append("")
            commands.append("# Or install in development mode")
            commands.append("pip install -e .")
        elif "node" in language or "javascript" in language:
            commands.append("# Install Node.js dependencies")
            commands.append("npm install")
            commands.append("")
            commands.append("# Or using yarn")
            commands.append("yarn install")
        else:
            commands.append("# Install dependencies")
            commands.append("# Follow language-specific installation steps")

        return "```bash\n" + "\n".join(commands) + "\n```"

    def _generate_configuration_section(self, feature_docs: Dict[str, Any]) -> str:
        """Generate configuration section."""
        return """Create configuration file:

```bash
# Copy example configuration
cp config.example.env config.env

# Edit configuration
# Add your specific settings
```

**Key Configuration Options**:
- Environment settings
- Database connections
- API endpoints
- Authentication settings"""

    def _generate_basic_usage(self, usage_examples: List[Dict[str, str]], tech_stack: Dict[str, str]) -> str:
        """Generate basic usage section."""
        content = """### Quick Start Example

```bash
# Start the application
"""

        language = tech_stack.get("language", "").lower()
        if "python" in language:
            content += "python main.py\n"
        elif "node" in language:
            content += "npm start\n"
        else:
            content += "# Run the application\n"

        content += "```\n\n"

        if usage_examples:
            content += "### API Usage\n\n"
            for example in usage_examples[:3]:  # Limit to 3 examples
                content += f"```{example['type'].lower()}\n{example['content']}\n```\n\n"

        return content

    def _generate_api_reference(self, contracts: List[Dict[str, str]]) -> str:
        """Generate API reference section."""
        if not contracts:
            return "API documentation will be available in the contracts directory."

        content = "### Available Endpoints\n\n"
        for contract in contracts:
            content += f"#### {contract['name'].title()} API\n"
            content += f"See [contracts/{contract['name']}.md](contracts/{contract['name']}.md) for detailed specifications.\n\n"

        return content

    def _generate_dev_setup_commands(self, tech_stack: Dict[str, str]) -> str:
        """Generate development setup commands."""
        language = tech_stack.get("language", "").lower()

        if "python" in language:
            return "pip install -e .[dev]\npip install pytest black flake8"
        elif "node" in language:
            return "npm install --dev\n# or\nyarn install --dev"
        else:
            return "# Install development dependencies"

    def _generate_dev_run_commands(self, tech_stack: Dict[str, str]) -> str:
        """Generate development run commands."""
        language = tech_stack.get("language", "").lower()

        if "python" in language:
            return "python -m uvicorn main:app --reload\n# or\npython main.py --dev"
        elif "node" in language:
            return "npm run dev\n# or\nyarn dev"
        else:
            return "# Run in development mode"

    def _generate_test_commands(self, tech_stack: Dict[str, str]) -> str:
        """Generate test commands."""
        language = tech_stack.get("language", "").lower()

        if "python" in language:
            return "pytest\n# or\npython -m pytest tests/"
        elif "node" in language:
            return "npm test\n# or\nyarn test"
        else:
            return "# Run tests"

    def _generate_specific_test_commands(self, tech_stack: Dict[str, str]) -> str:
        """Generate specific test commands."""
        language = tech_stack.get("language", "").lower()

        if "python" in language:
            return "pytest tests/unit/\npytest tests/integration/\npytest tests/contract/"
        elif "node" in language:
            return "npm run test:unit\nnpm run test:integration\nnpm run test:contract"
        else:
            return "# Run specific test types"

    def _generate_troubleshooting_section(self, tech_stack: Dict[str, str]) -> str:
        """Generate troubleshooting section."""
        return """#### Installation Issues
- Ensure all prerequisites are installed
- Check version compatibility
- Clear package cache if needed

#### Runtime Issues
- Verify configuration settings
- Check log files for detailed error messages
- Ensure all required services are running

#### API Issues
- Verify endpoint URLs
- Check authentication credentials
- Validate request format"""

    async def _convert_format(self, content: str, format_enum: DocumentFormat) -> str:
        """Convert markdown content to other formats."""
        # For now, just return markdown content
        # In a full implementation, you might use pandoc or similar
        if format_enum == DocumentFormat.HTML:
            # Basic HTML conversion
            html_content = content.replace("\n", "<br>\n")
            return f"<html><body>{html_content}</body></html>"
        elif format_enum == DocumentFormat.PDF:
            # For PDF, return markdown with note
            return f"# PDF Generation Not Implemented\n\n{content}"
        return content


class GenerateContractsTool(BaseTool):
    """Generate OpenAPI/GraphQL/gRPC contracts from feature requirements."""

    async def execute(
        self,
        contract_type: str = "openapi",
        include_tests: bool = True
    ) -> ToolResponse:
        """Generate API contracts."""
        try:
            # Validate inputs
            validated_inputs = await self.validate_inputs(
                contract_type=contract_type,
                include_tests=include_tests
            )

            contract_type_enum = validated_inputs["contract_type"]
            include_tests = validated_inputs["include_tests"]

            # Check if scripts are available
            if not self.settings.scripts_path or not self.settings.scripts_path.exists():
                # Fallback to manual generation
                return await self._manual_generate_contracts(contract_type_enum, include_tests)

            # Use spec-kit scripts
            script_runner = ScriptRunner(self.settings.scripts_path, self.settings.script_timeout)

            # Run contract generation script
            result = await script_runner.run_script(
                "generate-contracts.sh",
                args=[
                    "--type", contract_type_enum.value,
                    "--tests" if include_tests else "--no-tests",
                    "--json"
                ],
                json_output=True,
                cwd=self.settings.repo_path
            )

            contracts_dir = result.get("contracts_dir")
            generated_files = result.get("generated_files", [])
            contract_specs = result.get("contract_specs", [])

            if not contracts_dir:
                raise ScriptExecutionError(
                    "Script did not return expected output",
                    details={"result": result}
                )

            return self.create_success_response(
                message=f"{contract_type_enum.value.upper()} contracts generated",
                data={
                    "contract_type": contract_type_enum.value,
                    "contracts_dir": contracts_dir,
                    "generated_files": generated_files,
                    "contract_specs": contract_specs,
                    "include_tests": include_tests
                },
                artifacts=[Path(f) for f in generated_files]
            )

        except Exception as e:
            logger.error(f"Failed to generate contracts using scripts: {e}")
            # Try manual fallback
            return await self._manual_generate_contracts(
                ContractType(contract_type) if isinstance(contract_type, str) else contract_type,
                include_tests
            )

    async def validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize inputs."""
        contract_type = kwargs.get("contract_type", "openapi").strip()
        include_tests = kwargs.get("include_tests", True)

        # Validate contract_type
        try:
            contract_type_enum = ContractType(contract_type)
        except ValueError:
            valid_types = [t.value for t in ContractType]
            raise ValidationError(
                f"Invalid contract_type: {contract_type}",
                suggestions=[f"Use one of: {', '.join(valid_types)}"]
            )

        return {
            "contract_type": contract_type_enum,
            "include_tests": bool(include_tests)
        }

    async def _manual_generate_contracts(
        self,
        contract_type: ContractType,
        include_tests: bool
    ) -> ToolResponse:
        """Manually generate contracts without scripts."""
        # Get current branch and feature directory
        git_ops = GitOperations(self.settings.repo_path)
        branch_name = await git_ops.get_current_branch()

        if not branch_name or branch_name in ["main", "master"]:
            raise ValidationError(
                "Not on a feature branch",
                suggestions=["Switch to a feature branch first"]
            )

        feature_dir = self.get_feature_dir(branch_name)
        spec_file = self.get_spec_file(branch_name)
        plan_file = self.get_plan_file(branch_name)

        # Check required files exist
        if not spec_file.exists():
            raise ValidationError(
                f"Feature specification not found: {spec_file}",
                suggestions=["Run create_specification first"]
            )

        # Read feature documents
        feature_docs = await self._read_feature_documents(feature_dir)

        # Create contracts directory
        contracts_dir = feature_dir / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)

        # Generate contracts based on type
        generated_files = []
        if contract_type == ContractType.OPENAPI:
            openapi_files = await self._generate_openapi_contracts(contracts_dir, feature_docs, include_tests)
            generated_files.extend(openapi_files)
        elif contract_type == ContractType.GRAPHQL:
            graphql_files = await self._generate_graphql_contracts(contracts_dir, feature_docs, include_tests)
            generated_files.extend(graphql_files)
        elif contract_type == ContractType.GRPC:
            grpc_files = await self._generate_grpc_contracts(contracts_dir, feature_docs, include_tests)
            generated_files.extend(grpc_files)

        return self.create_success_response(
            message=f"{contract_type.value.upper()} contracts generated",
            data={
                "contract_type": contract_type.value,
                "contracts_dir": str(contracts_dir),
                "generated_files": [str(f) for f in generated_files],
                "include_tests": include_tests
            },
            artifacts=generated_files
        )

    async def _read_feature_documents(self, feature_dir: Path) -> Dict[str, str]:
        """Read all feature documents."""
        docs = {}

        # Read core documents
        doc_files = {
            "spec": "spec.md",
            "plan": "plan.md",
            "data_model": "data-model.md"
        }

        for doc_key, filename in doc_files.items():
            doc_path = feature_dir / filename
            if doc_path.exists():
                docs[doc_key] = doc_path.read_text()

        return docs

    async def _generate_openapi_contracts(self, contracts_dir: Path, feature_docs: Dict[str, str], include_tests: bool) -> List[Path]:
        """Generate OpenAPI contracts."""
        generated_files = []

        # Extract API information from documents
        api_info = self._extract_api_info(feature_docs)
        entities = self._extract_entities(feature_docs.get("data_model", ""))

        # Generate OpenAPI specification
        openapi_spec = self._create_openapi_spec(api_info, entities)

        # Write OpenAPI spec file
        openapi_file = contracts_dir / "openapi.yaml"
        openapi_file.write_text(yaml.dump(openapi_spec, default_flow_style=False))
        generated_files.append(openapi_file)

        # Generate markdown documentation
        doc_file = contracts_dir / "api.md"
        doc_content = self._create_openapi_docs(openapi_spec)
        doc_file.write_text(doc_content)
        generated_files.append(doc_file)

        # Generate test files if requested
        if include_tests:
            test_file = contracts_dir / "api_tests.md"
            test_content = self._create_api_tests(openapi_spec)
            test_file.write_text(test_content)
            generated_files.append(test_file)

        return generated_files

    async def _generate_graphql_contracts(self, contracts_dir: Path, feature_docs: Dict[str, str], include_tests: bool) -> List[Path]:
        """Generate GraphQL contracts."""
        generated_files = []

        # Extract data model information
        entities = self._extract_entities(feature_docs.get("data_model", ""))

        # Generate GraphQL schema
        schema_content = self._create_graphql_schema(entities)

        # Write GraphQL schema file
        schema_file = contracts_dir / "schema.graphql"
        schema_file.write_text(schema_content)
        generated_files.append(schema_file)

        # Generate documentation
        doc_file = contracts_dir / "graphql.md"
        doc_content = self._create_graphql_docs(schema_content)
        doc_file.write_text(doc_content)
        generated_files.append(doc_file)

        # Generate test queries if requested
        if include_tests:
            test_file = contracts_dir / "graphql_tests.md"
            test_content = self._create_graphql_tests(entities)
            test_file.write_text(test_content)
            generated_files.append(test_file)

        return generated_files

    async def _generate_grpc_contracts(self, contracts_dir: Path, feature_docs: Dict[str, str], include_tests: bool) -> List[Path]:
        """Generate gRPC contracts."""
        generated_files = []

        # Extract service information
        entities = self._extract_entities(feature_docs.get("data_model", ""))

        # Generate protobuf definitions
        proto_content = self._create_proto_definitions(entities)

        # Write proto file
        proto_file = contracts_dir / "service.proto"
        proto_file.write_text(proto_content)
        generated_files.append(proto_file)

        # Generate documentation
        doc_file = contracts_dir / "grpc.md"
        doc_content = self._create_grpc_docs(proto_content)
        doc_file.write_text(doc_content)
        generated_files.append(doc_file)

        # Generate test scenarios if requested
        if include_tests:
            test_file = contracts_dir / "grpc_tests.md"
            test_content = self._create_grpc_tests(entities)
            test_file.write_text(test_content)
            generated_files.append(test_file)

        return generated_files

    def _extract_api_info(self, feature_docs: Dict[str, str]) -> Dict[str, Any]:
        """Extract API information from feature documents."""
        spec_content = feature_docs.get("spec", "")
        plan_content = feature_docs.get("plan", "")

        api_info = {
            "title": "API",
            "version": "1.0.0",
            "description": "API for the feature",
            "endpoints": []
        }

        # Extract title from spec
        title_match = re.search(r'#\s*([^\n]+)', spec_content)
        if title_match:
            api_info["title"] = title_match.group(1).strip() + " API"

        # Extract version from plan
        version_match = re.search(r'version[:\s]+([\d\.]+)', plan_content, re.IGNORECASE)
        if version_match:
            api_info["version"] = version_match.group(1)

        # Extract endpoints from existing contracts or infer from entities
        endpoints = self._extract_endpoints_from_docs(feature_docs)
        api_info["endpoints"] = endpoints

        return api_info

    def _extract_endpoints_from_docs(self, feature_docs: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract API endpoints from documents."""
        endpoints = []

        # Look in existing contracts or data model
        for doc_content in feature_docs.values():
            if isinstance(doc_content, str):
                # Find HTTP method patterns
                endpoint_patterns = [
                    r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)',
                    r'###\s*(GET|POST|PUT|DELETE|PATCH)\s+([^\n]+)'
                ]

                for pattern in endpoint_patterns:
                    matches = re.findall(pattern, doc_content, re.IGNORECASE)
                    for method, path in matches:
                        endpoints.append({
                            "method": method.upper(),
                            "path": path.strip(),
                            "description": f"{method.title()} operation"
                        })

        # If no endpoints found, create basic CRUD endpoints
        if not endpoints:
            entities = self._extract_entities(feature_docs.get("data_model", ""))
            for entity in entities:
                resource = entity.lower() + "s"
                endpoints.extend([
                    {"method": "GET", "path": f"/{resource}", "description": f"List {resource}"},
                    {"method": "POST", "path": f"/{resource}", "description": f"Create {entity.lower()}"},
                    {"method": "GET", "path": f"/{resource}/{{id}}", "description": f"Get {entity.lower()}"},
                    {"method": "PUT", "path": f"/{resource}/{{id}}", "description": f"Update {entity.lower()}"},
                    {"method": "DELETE", "path": f"/{resource}/{{id}}", "description": f"Delete {entity.lower()}"}
                ])

        return endpoints

    def _extract_entities(self, data_model_content: str) -> List[str]:
        """Extract entity names from data model."""
        entities = []

        if data_model_content:
            # Look for entity patterns
            entity_patterns = [
                r'###\s*([A-Z][a-zA-Z]+)\s*Entity',
                r'###\s*([A-Z][a-zA-Z]+)\s*$',
                r'##\s*([A-Z][a-zA-Z]+)\s*$'
            ]

            for pattern in entity_patterns:
                matches = re.findall(pattern, data_model_content)
                entities.extend([match.strip() for match in matches if match.strip()])

        # Default entity if none found
        if not entities:
            entities = ["User"]

        return list(set(entities))  # Remove duplicates

    def _create_openapi_spec(self, api_info: Dict[str, Any], entities: List[str]) -> Dict[str, Any]:
        """Create OpenAPI specification."""
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": api_info["title"],
                "version": api_info["version"],
                "description": api_info["description"]
            },
            "servers": [
                {"url": "http://localhost:8000", "description": "Development server"}
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "responses": {
                    "NotFound": {
                        "description": "Resource not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "error": {"type": "string"},
                                        "message": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Add entity schemas
        for entity in entities:
            spec["components"]["schemas"][entity] = {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "format": "int64"},
                    "name": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                },
                "required": ["name"]
            }

        # Add paths from endpoints
        for endpoint in api_info["endpoints"]:
            path = endpoint["path"]
            method = endpoint["method"].lower()

            if path not in spec["paths"]:
                spec["paths"][path] = {}

            spec["paths"][path][method] = {
                "summary": endpoint["description"],
                "responses": {
                    "200": {"description": "Successful response"}
                }
            }

            # Add appropriate request/response schemas
            if method in ["post", "put"]:
                spec["paths"][path][method]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{entities[0] if entities else 'Object'}"}
                        }
                    }
                }

        return spec

    def _create_openapi_docs(self, openapi_spec: Dict[str, Any]) -> str:
        """Create OpenAPI documentation."""
        info = openapi_spec.get("info", {})
        return f"""# {info.get('title', 'API')} Documentation

**Version**: {info.get('version', '1.0.0')}
**Description**: {info.get('description', 'API documentation')}

## Base URL
```
http://localhost:8000
```

## Authentication
[Add authentication details]

## Endpoints

{self._format_openapi_paths(openapi_spec.get('paths', {}))}

## Schemas

{self._format_openapi_schemas(openapi_spec.get('components', {}).get('schemas', {}))}

## Error Responses

All endpoints may return these error responses:
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
"""

    def _format_openapi_paths(self, paths: Dict[str, Any]) -> str:
        """Format OpenAPI paths for documentation."""
        content = ""
        for path, methods in paths.items():
            for method, details in methods.items():
                content += f"### {method.upper()} {path}\n"
                content += f"{details.get('summary', 'No description')}\n\n"

                if 'requestBody' in details:
                    content += "**Request Body**:\n```json\n{\n  \"example\": \"request\"\n}\n```\n\n"

                content += "**Response**:\n```json\n{\n  \"example\": \"response\"\n}\n```\n\n"

        return content

    def _format_openapi_schemas(self, schemas: Dict[str, Any]) -> str:
        """Format OpenAPI schemas for documentation."""
        content = ""
        for schema_name, schema_def in schemas.items():
            content += f"### {schema_name}\n"
            properties = schema_def.get('properties', {})
            for prop_name, prop_def in properties.items():
                prop_type = prop_def.get('type', 'unknown')
                content += f"- `{prop_name}`: {prop_type}\n"
            content += "\n"

        return content

    def _create_api_tests(self, openapi_spec: Dict[str, Any]) -> str:
        """Create API test scenarios."""
        return f"""# API Test Scenarios

## Test Setup
```bash
# Set base URL
export API_BASE_URL="http://localhost:8000"
```

## Authentication Tests
```bash
# Test authentication
curl -X GET "$API_BASE_URL/auth/status"
```

## Endpoint Tests

{self._generate_endpoint_tests(openapi_spec.get('paths', {}))}

## Error Handling Tests
```bash
# Test 404 error
curl -X GET "$API_BASE_URL/nonexistent"

# Test validation error
curl -X POST "$API_BASE_URL/resource" -H "Content-Type: application/json" -d '{{}}'
```
"""

    def _generate_endpoint_tests(self, paths: Dict[str, Any]) -> str:
        """Generate test cases for endpoints."""
        content = ""
        for path, methods in paths.items():
            for method, details in methods.items():
                content += f"### Test {method.upper()} {path}\n"
                content += f"```bash\n"

                if method.lower() in ['post', 'put']:
                    content += f'curl -X {method.upper()} "$API_BASE_URL{path}" -H "Content-Type: application/json" -d \'{{"test": "data"}}\'\\n'
                else:
                    content += f'curl -X {method.upper()} "$API_BASE_URL{path}"\n'

                content += f"```\n\n"

        return content

    def _create_graphql_schema(self, entities: List[str]) -> str:
        """Create GraphQL schema."""
        schema = """# GraphQL Schema

scalar DateTime

"""

        # Add entity types
        for entity in entities:
            schema += f"""type {entity} {{
  id: ID!
  name: String!
  createdAt: DateTime!
  updatedAt: DateTime!
}}

"""

        # Add input types
        for entity in entities:
            schema += f"""input {entity}Input {{
  name: String!
}}

input {entity}UpdateInput {{
  name: String
}}

"""

        # Add Query type
        schema += "type Query {\n"
        for entity in entities:
            entity_lower = entity.lower()
            schema += f"  {entity_lower}(id: ID!): {entity}\n"
            schema += f"  {entity_lower}s: [{entity}!]!\n"
        schema += "}\n\n"

        # Add Mutation type
        schema += "type Mutation {\n"
        for entity in entities:
            entity_lower = entity.lower()
            schema += f"  create{entity}(input: {entity}Input!): {entity}!\n"
            schema += f"  update{entity}(id: ID!, input: {entity}UpdateInput!): {entity}!\n"
            schema += f"  delete{entity}(id: ID!): Boolean!\n"
        schema += "}\n"

        return schema

    def _create_graphql_docs(self, schema_content: str) -> str:
        """Create GraphQL documentation."""
        return f"""# GraphQL API Documentation

## Schema

```graphql
{schema_content}
```

## Example Queries

### Query Example
```graphql
query {{
  users {{
    id
    name
    createdAt
  }}
}}
```

### Mutation Example
```graphql
mutation {{
  createUser(input: {{ name: "John Doe" }}) {{
    id
    name
    createdAt
  }}
}}
```

## Error Handling

GraphQL errors are returned in the `errors` field of the response:

```json
{{
  "data": null,
  "errors": [
    {{
      "message": "User not found",
      "path": ["user"],
      "extensions": {{
        "code": "NOT_FOUND"
      }}
    }}
  ]
}}
```
"""

    def _create_graphql_tests(self, entities: List[str]) -> str:
        """Create GraphQL test scenarios."""
        return f"""# GraphQL Test Scenarios

## Test Setup
```bash
# Set GraphQL endpoint
export GRAPHQL_URL="http://localhost:8000/graphql"
```

## Query Tests

### Test List Query
```bash
curl -X POST "$GRAPHQL_URL" \
  -H "Content-Type: application/json" \
  -d '{{
    "query": "{{ users {{ id name }} }}"
  }}'
```

### Test Single Item Query
```bash
curl -X POST "$GRAPHQL_URL" \
  -H "Content-Type: application/json" \
  -d '{{
    "query": "{{ user(id: \"1\") {{ id name createdAt }} }}"
  }}'
```

## Mutation Tests

### Test Create Mutation
```bash
curl -X POST "$GRAPHQL_URL" \
  -H "Content-Type: application/json" \
  -d '{{
    "query": "mutation {{ createUser(input: {{ name: \"Test User\" }}) {{ id name }} }}"
  }}'
```

### Test Update Mutation
```bash
curl -X POST "$GRAPHQL_URL" \
  -H "Content-Type: application/json" \
  -d '{{
    "query": "mutation {{ updateUser(id: \"1\", input: {{ name: \"Updated Name\" }}) {{ id name }} }}"
  }}'
```

## Error Tests

### Test Invalid Query
```bash
curl -X POST "$GRAPHQL_URL" \
  -H "Content-Type: application/json" \
  -d '{{
    "query": "{{ invalidField }}"
  }}'
```
"""

    def _create_proto_definitions(self, entities: List[str]) -> str:
        """Create protobuf definitions."""
        proto = """syntax = "proto3";

package api.v1;

import "google/protobuf/timestamp.proto";

option go_package = "./api/v1";

"""

        # Add message definitions
        for entity in entities:
            proto += f"""message {entity} {{
  int64 id = 1;
  string name = 2;
  google.protobuf.Timestamp created_at = 3;
  google.protobuf.Timestamp updated_at = 4;
}}

message {entity}Request {{
  string name = 1;
}}

message {entity}Response {{
  {entity} {entity.lower()} = 1;
}}

message List{entity}sRequest {{
  int32 page = 1;
  int32 page_size = 2;
}}

message List{entity}sResponse {{
  repeated {entity} {entity.lower()}s = 1;
  int32 total = 2;
}}

"""

        # Add service definition
        proto += "service ApiService {\n"
        for entity in entities:
            entity_lower = entity.lower()
            proto += f"  rpc Create{entity}({entity}Request) returns ({entity}Response);\n"
            proto += f"  rpc Get{entity}(GetRequest) returns ({entity}Response);\n"
            proto += f"  rpc List{entity}s(List{entity}sRequest) returns (List{entity}sResponse);\n"
            proto += f"  rpc Update{entity}(Update{entity}Request) returns ({entity}Response);\n"
            proto += f"  rpc Delete{entity}(DeleteRequest) returns (DeleteResponse);\n"
        proto += "}\n\n"

        # Add common messages
        proto += """message GetRequest {
  int64 id = 1;
}

message DeleteRequest {
  int64 id = 1;
}

message DeleteResponse {
  bool success = 1;
}
"""

        return proto

    def _create_grpc_docs(self, proto_content: str) -> str:
        """Create gRPC documentation."""
        return f"""# gRPC API Documentation

## Protocol Buffer Definition

```proto
{proto_content}
```

## Service Methods

### Authentication
All methods require authentication. Include the authentication token in the metadata:

```
authorization: Bearer <token>
```

### Error Handling

gRPC uses status codes for error handling:
- `OK` (0): Success
- `INVALID_ARGUMENT` (3): Invalid request parameters
- `NOT_FOUND` (5): Resource not found
- `ALREADY_EXISTS` (6): Resource already exists
- `UNAUTHENTICATED` (16): Authentication required
- `INTERNAL` (13): Internal server error

## Code Generation

### Go
```bash
protoc --go_out=. --go-grpc_out=. service.proto
```

### Python
```bash
python -m grpc_tools.protoc --python_out=. --grpc_python_out=. service.proto
```

### Node.js
```bash
npx grpc_tools_node_protoc --js_out=import_style=commonjs,binary:. --grpc_out=. service.proto
```
"""

    def _create_grpc_tests(self, entities: List[str]) -> str:
        """Create gRPC test scenarios."""
        return f"""# gRPC Test Scenarios

## Test Setup

### Install grpcurl
```bash
# macOS
brew install grpcurl

# Linux
go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest
```

### Set Server URL
```bash
export GRPC_SERVER="localhost:9000"
```

## Service Tests

### List Services
```bash
grpcurl -plaintext $GRPC_SERVER list
```

### Describe Service
```bash
grpcurl -plaintext $GRPC_SERVER describe api.v1.ApiService
```

## Method Tests

### Test Create Method
```bash
grpcurl -plaintext -d '{{
  "name": "Test User"
}}' $GRPC_SERVER api.v1.ApiService/CreateUser
```

### Test Get Method
```bash
grpcurl -plaintext -d '{{
  "id": 1
}}' $GRPC_SERVER api.v1.ApiService/GetUser
```

### Test List Method
```bash
grpcurl -plaintext -d '{{
  "page": 1,
  "page_size": 10
}}' $GRPC_SERVER api.v1.ApiService/ListUsers
```

### Test Update Method
```bash
grpcurl -plaintext -d '{{
  "id": 1,
  "name": "Updated Name"
}}' $GRPC_SERVER api.v1.ApiService/UpdateUser
```

### Test Delete Method
```bash
grpcurl -plaintext -d '{{
  "id": 1
}}' $GRPC_SERVER api.v1.ApiService/DeleteUser
```

## Error Testing

### Test Invalid Request
```bash
grpcurl -plaintext -d '{{}}' $GRPC_SERVER api.v1.ApiService/CreateUser
```

### Test Not Found
```bash
grpcurl -plaintext -d '{{
  "id": 999999
}}' $GRPC_SERVER api.v1.ApiService/GetUser
```
"""


# Export tool functions
async def generate_quickstart(
    include_test_scenarios: bool = True,
    format: str = "markdown",
    settings: Settings = None
) -> ToolResponse:
    """Generate quickstart documentation."""
    tool = GenerateQuickstartTool(settings)
    return await tool.execute(
        include_test_scenarios=include_test_scenarios,
        format=format
    )


async def generate_contracts(
    contract_type: str = "openapi",
    include_tests: bool = True,
    settings: Settings = None
) -> ToolResponse:
    """Generate API contracts."""
    tool = GenerateContractsTool(settings)
    return await tool.execute(
        contract_type=contract_type,
        include_tests=include_tests
    )