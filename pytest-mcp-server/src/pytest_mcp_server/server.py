"""
Main MCP server implementation using FastMCP.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from .models import (
    DebuggingProgress,
    FailureAnalysis,
    FailurePattern,
    TestCase,
    TestEnvironment,
    TestOutcome,
    TestResult,
    TestSession,
    TestSummary,
)
from .storage import TestStorage
from .analysis import FailureAnalyzer
from .code_analyzer import CodeAnalyzer
from .test_generator import TestGenerator
from .coverage_analyzer import CoverageAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage and analyzer instances
storage = TestStorage()
analyzer = FailureAnalyzer()
code_analyzer = CodeAnalyzer()
test_generator = TestGenerator()
coverage_analyzer = CoverageAnalyzer()


def create_server() -> FastMCP:
    """Create and configure the FastMCP server."""
    app = FastMCP("pytest-mcp-server")

    @app.tool()
    def record_session_start(environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record the start of a pytest session.

        Args:
            environment: Dictionary containing environment information
                - os: Operating system name
                - python_version: Python version string
                - pytest_version: Pytest version (optional)
                - platform: Platform information (optional)
                - architecture: System architecture (optional)

        Returns:
            Dictionary with session information and status
        """
        try:
            # Validate environment data
            env = TestEnvironment(**environment)

            # Create new session
            session_id = str(uuid4())
            session = TestSession(
                session_id=session_id,
                environment=env,
                start_time=datetime.now(),
                status="running"
            )

            # Store session
            storage.store_session(session)
            logger.info(f"Started test session: {session_id}")

            return {
                "success": True,
                "session_id": session_id,
                "message": f"Test session started successfully",
                "environment": env.dict(),
                "timestamp": session.start_time.isoformat()
            }

        except ValidationError as e:
            logger.error(f"Validation error in record_session_start: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "details": e.errors()
            }
        except Exception as e:
            logger.error(f"Error in record_session_start: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def record_test_outcome(
        nodeid: str,
        outcome: str,
        duration: float,
        error: Optional[str] = None,
        traceback: Optional[str] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        markers: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Record the outcome of an individual test case.

        Args:
            nodeid: Unique test node identifier
            outcome: Test outcome (passed, failed, skipped, error, xfail, xpass)
            duration: Test duration in seconds
            error: Error message if test failed (optional)
            traceback: Full traceback if available (optional)
            stdout: Captured stdout (optional)
            stderr: Captured stderr (optional)
            markers: Test markers (optional)
            keywords: Test keywords (optional)
            file_path: Test file path (optional)
            line_number: Test line number (optional)

        Returns:
            Dictionary with test result information and analysis
        """
        try:
            # Validate and create test case
            test_case = TestCase(
                nodeid=nodeid,
                outcome=TestOutcome(outcome),
                duration=duration,
                error=error,
                traceback=traceback,
                stdout=stdout,
                stderr=stderr,
                markers=markers or [],
                keywords=keywords or [],
                file_path=file_path,
                line_number=line_number
            )

            # Get current session
            current_session = storage.get_current_session()
            if not current_session:
                logger.warning("No active session found, creating default session")
                current_session = storage.create_default_session()

            # Create test result
            test_result = TestResult(
                test_case=test_case,
                session_id=current_session.session_id
            )

            # Perform failure analysis if needed
            analysis_result = None
            if test_result.is_failure:
                try:
                    analysis_result = analyzer.analyze_failure(test_case)
                    test_result.analysis = analysis_result
                except Exception as e:
                    logger.error(f"Failed to analyze failure: {e}")

            # Store test result
            storage.store_test_result(test_result)
            logger.info(f"Recorded test outcome: {nodeid} - {outcome}")

            response = {
                "success": True,
                "test_case": test_case.dict(),
                "session_id": current_session.session_id,
                "message": f"Test outcome recorded: {outcome}",
                "timestamp": datetime.now().isoformat()
            }

            if analysis_result:
                response["failure_analysis"] = analysis_result.dict()

            return response

        except ValidationError as e:
            logger.error(f"Validation error in record_test_outcome: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "details": e.errors()
            }
        except Exception as e:
            logger.error(f"Error in record_test_outcome: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def record_session_finish(summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record the completion of a pytest session.

        Args:
            summary: Dictionary containing session summary
                - total_tests: Total number of tests
                - passed: Number of passed tests
                - failed: Number of failed tests
                - skipped: Number of skipped tests
                - errors: Number of error tests (optional)
                - xfailed: Number of expected failures (optional)
                - xpassed: Number of unexpected passes (optional)
                - exitstatus: Exit status code
                - duration: Total session duration (optional)

        Returns:
            Dictionary with session completion information
        """
        try:
            # Get current session
            current_session = storage.get_current_session()
            if not current_session:
                return {
                    "success": False,
                    "error": "No active session found"
                }

            # Validate summary
            if 'duration' not in summary:
                summary['duration'] = (datetime.now() - current_session.start_time).total_seconds()

            test_summary = TestSummary(**summary)

            # Update session
            current_session.end_time = datetime.now()
            current_session.status = "finished"

            # Store updated session and summary
            storage.store_session(current_session)
            storage.store_session_summary(current_session.session_id, test_summary)

            logger.info(f"Finished test session: {current_session.session_id}")

            return {
                "success": True,
                "session_id": current_session.session_id,
                "summary": test_summary.dict(),
                "message": "Test session completed successfully",
                "end_time": current_session.end_time.isoformat()
            }

        except ValidationError as e:
            logger.error(f"Validation error in record_session_finish: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "details": e.errors()
            }
        except Exception as e:
            logger.error(f"Error in record_session_finish: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def get_session_status(session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the status of a test session.

        Args:
            session_id: Session identifier (optional, uses current session if not provided)

        Returns:
            Dictionary with session status and information
        """
        try:
            if session_id:
                session = storage.get_session(session_id)
            else:
                session = storage.get_current_session()

            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }

            summary = storage.get_session_summary(session.session_id)
            test_results = storage.get_session_results(session.session_id)

            return {
                "success": True,
                "session": session.dict(),
                "summary": summary.dict() if summary else None,
                "test_count": len(test_results),
                "failure_count": sum(1 for r in test_results if r.is_failure)
            }

        except Exception as e:
            logger.error(f"Error in get_session_status: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def get_failure_analysis(test_nodeid: str) -> Dict[str, Any]:
        """
        Get failure analysis for a specific test.

        Args:
            test_nodeid: Test node identifier

        Returns:
            Dictionary with failure analysis information
        """
        try:
            test_result = storage.get_test_result(test_nodeid)
            if not test_result:
                return {
                    "success": False,
                    "error": f"Test result not found: {test_nodeid}"
                }

            if not test_result.is_failure:
                return {
                    "success": False,
                    "error": f"Test did not fail: {test_nodeid}"
                }

            if not test_result.analysis:
                # Try to analyze now
                try:
                    analysis = analyzer.analyze_failure(test_result.test_case)
                    test_result.analysis = analysis
                    storage.store_test_result(test_result)
                except Exception as e:
                    logger.error(f"Failed to analyze failure: {e}")
                    return {
                        "success": False,
                        "error": f"Failed to analyze failure: {str(e)}"
                    }

            return {
                "success": True,
                "test_case": test_result.test_case.dict(),
                "analysis": test_result.analysis.dict() if test_result.analysis else None
            }

        except Exception as e:
            logger.error(f"Error in get_failure_analysis: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def find_similar_failures(
        error_pattern: Optional[str] = None,
        test_pattern: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Find similar test failures across sessions.

        Args:
            error_pattern: Error pattern to search for (optional)
            test_pattern: Test name pattern to search for (optional)
            limit: Maximum number of results to return

        Returns:
            Dictionary with similar failures information
        """
        try:
            similar_failures = analyzer.find_similar_failures(
                error_pattern=error_pattern,
                test_pattern=test_pattern,
                limit=limit
            )

            return {
                "success": True,
                "similar_failures": [f.dict() for f in similar_failures],
                "count": len(similar_failures)
            }

        except Exception as e:
            logger.error(f"Error in find_similar_failures: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def track_debugging_progress(
        failure_id: str,
        action: str,
        step_description: Optional[str] = None,
        hypothesis: Optional[str] = None,
        resolution_status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track debugging progress for a specific failure.

        Args:
            failure_id: Failure identifier
            action: Action to take (add_step, add_hypothesis, update_status, add_notes)
            step_description: Description of debugging step taken (optional)
            hypothesis: New hypothesis to add (optional)
            resolution_status: New resolution status (optional)
            notes: Additional notes (optional)

        Returns:
            Dictionary with updated debugging progress
        """
        try:
            progress = storage.get_debugging_progress(failure_id)
            if not progress:
                progress = DebuggingProgress(failure_id=failure_id)

            if action == "add_step" and step_description:
                progress.steps_taken.append(step_description)
            elif action == "add_hypothesis" and hypothesis:
                progress.hypotheses.append(hypothesis)
            elif action == "update_status" and resolution_status:
                progress.resolution_status = resolution_status
            elif action == "add_notes" and notes:
                if progress.notes:
                    progress.notes += f"\n\n{notes}"
                else:
                    progress.notes = notes

            progress.updated_at = datetime.now()
            storage.store_debugging_progress(progress)

            return {
                "success": True,
                "debugging_progress": progress.dict(),
                "message": f"Debugging progress updated: {action}"
            }

        except ValidationError as e:
            logger.error(f"Validation error in track_debugging_progress: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "details": e.errors()
            }
        except Exception as e:
            logger.error(f"Error in track_debugging_progress: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def generate_debugging_prompt(test_nodeid: str) -> Dict[str, Any]:
        """
        Generate a targeted debugging prompt for LLMs.

        Args:
            test_nodeid: Test node identifier

        Returns:
            Dictionary with generated debugging prompt and context
        """
        try:
            test_result = storage.get_test_result(test_nodeid)
            if not test_result:
                return {
                    "success": False,
                    "error": f"Test result not found: {test_nodeid}"
                }

            if not test_result.is_failure:
                return {
                    "success": False,
                    "error": f"Test did not fail: {test_nodeid}"
                }

            # Generate comprehensive debugging prompt
            prompt = analyzer.generate_debugging_prompt(test_result)

            return {
                "success": True,
                "test_case": test_result.test_case.dict(),
                "debugging_prompt": prompt,
                "context": {
                    "failure_analysis": test_result.analysis.dict() if test_result.analysis else None,
                    "debugging_progress": test_result.debugging_progress.dict() if test_result.debugging_progress else None
                }
            }

        except Exception as e:
            logger.error(f"Error in generate_debugging_prompt: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def get_test_statistics() -> Dict[str, Any]:
        """
        Get overall test statistics and metrics.

        Returns:
            Dictionary with comprehensive test statistics
        """
        try:
            stats = storage.get_test_statistics()

            return {
                "success": True,
                "statistics": stats
            }

        except Exception as e:
            logger.error(f"Error in get_test_statistics: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def analyze_code_for_testing(
        file_path: Optional[str] = None,
        source_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze source code to identify testing opportunities.

        Args:
            file_path: Path to Python source file (optional)
            source_code: Python source code as string (optional)

        Returns:
            Dictionary with code analysis results and testing recommendations
        """
        try:
            if not file_path and not source_code:
                return {
                    "success": False,
                    "error": "Either file_path or source_code must be provided"
                }

            if file_path:
                # Analyze file
                analysis = code_analyzer.analyze_file(file_path)
                source_path = file_path
            else:
                # Create temporary analysis from source code
                import tempfile
                from pathlib import Path

                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(source_code)
                    temp_path = f.name

                try:
                    analysis = code_analyzer.analyze_file(temp_path)
                    source_path = "inline_code"
                finally:
                    Path(temp_path).unlink()

            # Convert to serializable format
            result = {
                "success": True,
                "file_path": source_path,
                "functions": [
                    {
                        "name": func.name,
                        "signature": func.signature,
                        "parameters": func.parameters,
                        "complexity": func.complexity,
                        "is_async": func.is_async,
                        "docstring": func.docstring
                    }
                    for func in analysis.functions
                ],
                "classes": [
                    {
                        "name": cls.name,
                        "methods": [
                            {
                                "name": method.name,
                                "signature": method.signature,
                                "complexity": method.complexity
                            }
                            for method in cls.methods
                        ],
                        "docstring": cls.docstring
                    }
                    for cls in analysis.classes
                ],
                "complexity_score": analysis.complexity_score,
                "recommendations": analysis.test_recommendations,
                "estimated_tests": len(analysis.functions) * 3 + sum(len(cls.methods) * 2 for cls in analysis.classes)
            }

            return result

        except Exception as e:
            logger.error(f"Error in analyze_code_for_testing: {e}")
            return {
                "success": False,
                "error": f"Code analysis failed: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def generate_unit_tests(
        source_code: Optional[str] = None,
        file_path: Optional[str] = None,
        function_name: Optional[str] = None,
        class_name: Optional[str] = None,
        framework: str = "pytest",
        include_mocks: bool = True
    ) -> Dict[str, Any]:
        """
        Generate unit tests for Python code.

        Args:
            source_code: Python source code to generate tests for (optional)
            file_path: Path to Python source file (optional)
            function_name: Specific function name to test (optional)
            class_name: Specific class name to test (optional)
            framework: Test framework (pytest or unittest)
            include_mocks: Include mock-based tests

        Returns:
            Dictionary with generated test code and metadata
        """
        try:
            if not source_code and not file_path:
                return {
                    "success": False,
                    "error": "Either source_code or file_path must be provided"
                }

            # Get source code
            if file_path:
                from pathlib import Path
                path = Path(file_path)
                if not path.exists():
                    return {
                        "success": False,
                        "error": f"File not found: {file_path}"
                    }
                source_code = path.read_text()

            # Analyze the code first
            try:
                if function_name:
                    # Generate tests for specific function
                    functions = code_analyzer.analyze_function(source_code, function_name)
                    if not functions:
                        return {
                            "success": False,
                            "error": f"Function '{function_name}' not found in source code"
                        }

                    tests = test_generator.generate_tests_for_function(
                        functions[0], framework, include_mocks
                    )

                elif class_name:
                    # This would require extending code_analyzer to find specific classes
                    return {
                        "success": False,
                        "error": "Class-specific test generation not yet implemented"
                    }

                else:
                    # Generate tests for all functions in the code
                    functions = code_analyzer.analyze_function(source_code)
                    if not functions:
                        return {
                            "success": False,
                            "error": "No functions found in source code"
                        }

                    tests = []
                    for func in functions:
                        func_tests = test_generator.generate_tests_for_function(
                            func, framework, include_mocks
                        )
                        tests.extend(func_tests)

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Test generation failed: {str(e)}"
                }

            # Format response
            result = {
                "success": True,
                "framework": framework,
                "test_count": len(tests),
                "tests": [
                    {
                        "name": test.name,
                        "description": test.description,
                        "test_code": test.test_code,
                        "test_type": test.test_type,
                        "priority": test.priority
                    }
                    for test in tests
                ],
                "estimated_runtime": sum(0.1 for _ in tests),  # Rough estimate
                "imports": list(set(imp for test in tests for imp in test.imports))
            }

            return result

        except Exception as e:
            logger.error(f"Error in generate_unit_tests: {e}")
            return {
                "success": False,
                "error": f"Test generation failed: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def suggest_test_cases(
        function_name: str,
        source_code: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest test cases for a specific function.

        Args:
            function_name: Name of the function to suggest tests for
            source_code: Python source code containing the function (optional)
            file_path: Path to Python file containing the function (optional)

        Returns:
            Dictionary with suggested test cases and recommendations
        """
        try:
            if not source_code and not file_path:
                return {
                    "success": False,
                    "error": "Either source_code or file_path must be provided"
                }

            # Get source code
            if file_path:
                from pathlib import Path
                path = Path(file_path)
                if not path.exists():
                    return {
                        "success": False,
                        "error": f"File not found: {file_path}"
                    }
                source_code = path.read_text()

            # Analyze the specific function
            functions = code_analyzer.analyze_function(source_code, function_name)
            if not functions:
                return {
                    "success": False,
                    "error": f"Function '{function_name}' not found in source code"
                }

            func_info = functions[0]

            # Generate test case suggestions
            suggestions = code_analyzer.suggest_test_cases(func_info)

            result = {
                "success": True,
                "function_name": function_name,
                "function_signature": func_info.signature,
                "complexity": func_info.complexity,
                "parameter_count": len(func_info.parameters),
                "suggested_tests": [
                    {
                        "name": suggestion["name"],
                        "description": suggestion["description"],
                        "test_type": suggestion["test_type"],
                        "priority": suggestion["priority"]
                    }
                    for suggestion in suggestions
                ],
                "recommendations": [
                    f"Function has complexity score of {func_info.complexity}",
                    f"Consider testing with {len(func_info.parameters)} different parameter combinations",
                    "Focus on edge cases and error conditions" if func_info.complexity > 3 else "Basic testing should be sufficient"
                ]
            }

            return result

        except Exception as e:
            logger.error(f"Error in suggest_test_cases: {e}")
            return {
                "success": False,
                "error": f"Test case suggestion failed: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def generate_test_file(
        file_path: str,
        output_path: Optional[str] = None,
        framework: str = "pytest",
        include_integration: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a complete test file for a Python module.

        Args:
            file_path: Path to Python source file
            output_path: Path for generated test file (optional)
            framework: Test framework to use (pytest or unittest)
            include_integration: Include integration tests

        Returns:
            Dictionary with generated test file content and metadata
        """
        try:
            from pathlib import Path

            source_path = Path(file_path)
            if not source_path.exists():
                return {
                    "success": False,
                    "error": f"Source file not found: {file_path}"
                }

            # Analyze the entire file
            analysis = code_analyzer.analyze_file(file_path)

            # Generate complete test file
            test_file = test_generator.generate_test_file(
                analysis, framework, output_path
            )

            # Render the test file content
            test_content = test_generator.render_test_file(test_file)

            result = {
                "success": True,
                "source_file": file_path,
                "test_file_name": test_file.file_name,
                "framework": framework,
                "test_content": test_content,
                "test_count": len(test_file.test_cases),
                "imports": test_file.imports,
                "estimated_coverage": 75.0,  # Rough estimate
                "metadata": {
                    "functions_tested": len(analysis.functions),
                    "classes_tested": len(analysis.classes),
                    "complexity_score": analysis.complexity_score,
                    "high_priority_tests": len([t for t in test_file.test_cases if t.priority == "high"])
                }
            }

            # Optionally write to file
            if output_path:
                output_file = Path(output_path)
                output_file.write_text(test_content)
                result["file_written"] = str(output_file)

            return result

        except Exception as e:
            logger.error(f"Error in generate_test_file: {e}")
            return {
                "success": False,
                "error": f"Test file generation failed: {str(e)}",
                "traceback": traceback.format_exc()
            }

    @app.tool()
    def analyze_test_coverage(
        source_dir: str,
        test_dir: Optional[str] = None,
        coverage_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze test coverage and provide improvement recommendations.

        Args:
            source_dir: Directory containing source code
            test_dir: Directory containing tests (optional)
            coverage_file: Path to existing coverage report file (optional)

        Returns:
            Dictionary with coverage analysis and recommendations
        """
        try:
            from pathlib import Path

            if coverage_file:
                # Analyze existing coverage file
                reports = coverage_analyzer.analyze_coverage_from_file(coverage_file)

                result = {
                    "success": True,
                    "coverage_reports": [
                        {
                            "file_path": report.file_path,
                            "coverage_percentage": report.coverage_percentage,
                            "total_lines": report.total_lines,
                            "covered_lines": report.covered_lines,
                            "missing_lines": report.missing_lines[:20],  # Limit output
                            "uncovered_functions": report.uncovered_functions[:10]
                        }
                        for report in reports
                    ],
                    "overall_coverage": coverage_analyzer._calculate_overall_coverage(reports),
                    "files_analyzed": len(reports)
                }

                # Generate improvement plan
                improvement_plan = coverage_analyzer.generate_coverage_improvement_plan(reports)
                result["improvement_plan"] = improvement_plan

                return result

            elif test_dir:
                # Run coverage analysis
                coverage_result = coverage_analyzer.run_coverage_analysis(source_dir, test_dir)
                return coverage_result

            else:
                return {
                    "success": False,
                    "error": "Either coverage_file or test_dir must be provided"
                }

        except Exception as e:
            logger.error(f"Error in analyze_test_coverage: {e}")
            return {
                "success": False,
                "error": f"Coverage analysis failed: {str(e)}",
                "traceback": traceback.format_exc()
            }

    return app