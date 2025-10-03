package server

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"github.com/mcpservershub/mcpservers/ginkgo-mcp/internal/analyzer"
	"github.com/mcpservershub/mcpservers/ginkgo-mcp/internal/testrunner"
	"github.com/mcpservershub/mcpservers/ginkgo-mcp/internal/tools"
	"github.com/mcpservershub/mcpservers/ginkgo-mcp/pkg/types"
	"github.com/mcpservershub/mcpservers/ginkgo-mcp/pkg/utils"
)

// GinkgoMCPServer is the main MCP server for Ginkgo testing
type GinkgoMCPServer struct {
	workDir       string
	dataDir       string
	testRunner    *testrunner.Runner
	testGenerator *tools.TestGenerator
	analyzer      *analyzer.Analyzer
	sessions      map[string]*types.DebuggingSession
}

// NewGinkgoMCPServer creates a new Ginkgo MCP server
func NewGinkgoMCPServer(workDir, dataDir string) *GinkgoMCPServer {
	return &GinkgoMCPServer{
		workDir:       workDir,
		dataDir:       dataDir,
		testRunner:    testrunner.NewRunner(workDir),
		testGenerator: tools.NewTestGenerator(workDir),
		analyzer:      analyzer.NewAnalyzer(dataDir),
		sessions:      make(map[string]*types.DebuggingSession),
	}
}

// CreateMCPServer creates and configures the MCP server
func (g *GinkgoMCPServer) CreateMCPServer() *server.MCPServer {
	mcpServer := server.NewMCPServer(
		"ginkgo-mcp-server",
		"1.0.0",
		server.WithToolCapabilities(true),
	)

	// Register all tools
	g.registerTools(mcpServer)

	return mcpServer
}

// registerTools registers all MCP tools
func (g *GinkgoMCPServer) registerTools(s *server.MCPServer) {
	// Tool 1: find_testable_functions
	s.AddTool(mcp.Tool{
		Name:        "find_testable_functions",
		Description: "Discover all testable functions in a Go package for Ginkgo test generation",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"package_path": map[string]interface{}{
					"type":        "string",
					"description": "Path to the Go package to analyze",
				},
			},
			Required: []string{"package_path"},
		},
	}, g.handleFindTestableFunctions)

	// Tool 2: generate_test
	s.AddTool(mcp.Tool{
		Name:        "generate_test",
		Description: "Generate a Ginkgo test spec for a specific function",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"package_path": map[string]interface{}{
					"type":        "string",
					"description": "Path to the Go package",
				},
				"function_name": map[string]interface{}{
					"type":        "string",
					"description": "Name of the function to generate test for",
				},
				"test_type": map[string]interface{}{
					"type":        "string",
					"description": "Type of test to generate: 'basic', 'table_driven', or 'suite'",
					"enum":        []string{"basic", "table_driven", "suite"},
					"default":     "basic",
				},
			},
			Required: []string{"package_path", "function_name"},
		},
	}, g.handleGenerateTest)

	// Tool 3: run_tests
	s.AddTool(mcp.Tool{
		Name:        "run_tests",
		Description: "Run Ginkgo tests for a package and analyze results",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"package_path": map[string]interface{}{
					"type":        "string",
					"description": "Path to the Go package to test",
				},
				"focus": map[string]interface{}{
					"type":        "string",
					"description": "Focus on specific tests matching this pattern",
				},
				"skip": map[string]interface{}{
					"type":        "string",
					"description": "Skip tests matching this pattern",
				},
				"with_coverage": map[string]interface{}{
					"type":        "boolean",
					"description": "Include code coverage analysis",
					"default":     true,
				},
				"verbose": map[string]interface{}{
					"type":        "boolean",
					"description": "Run tests in verbose mode",
					"default":     false,
				},
				"parallel": map[string]interface{}{
					"type":        "integer",
					"description": "Number of parallel test nodes",
					"default":     1,
				},
				"timeout": map[string]interface{}{
					"type":        "string",
					"description": "Test timeout duration (e.g., '5m', '30s')",
					"default":     "5m",
				},
			},
			Required: []string{"package_path"},
		},
	}, g.handleRunTests)

	// Tool 4: analyze_test_failures
	s.AddTool(mcp.Tool{
		Name:        "analyze_test_failures",
		Description: "Analyze Ginkgo test failure patterns and generate debugging insights",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"test_results": map[string]interface{}{
					"type":        "string",
					"description": "JSON string of test results or path to results file",
				},
			},
			Required: []string{"test_results"},
		},
	}, g.handleAnalyzeTestFailures)

	// Tool 5: find_similar_failures
	s.AddTool(mcp.Tool{
		Name:        "find_similar_failures",
		Description: "Find similar historical Ginkgo test failures for debugging insights",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"test_name": map[string]interface{}{
					"type":        "string",
					"description": "Name of the failing test spec",
				},
				"error_message": map[string]interface{}{
					"type":        "string",
					"description": "Error or failure message from the test",
				},
				"limit": map[string]interface{}{
					"type":        "integer",
					"description": "Maximum number of similar failures to return",
					"default":     5,
				},
			},
			Required: []string{"test_name", "error_message"},
		},
	}, g.handleFindSimilarFailures)

	// Tool 6: generate_debugging_prompt
	s.AddTool(mcp.Tool{
		Name:        "generate_debugging_prompt",
		Description: "Generate AI-friendly debugging prompts for Ginkgo test failures",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"test_result": map[string]interface{}{
					"type":        "string",
					"description": "JSON string of the failing test result",
				},
				"include_similar": map[string]interface{}{
					"type":        "boolean",
					"description": "Include similar historical failures in the prompt",
					"default":     true,
				},
			},
			Required: []string{"test_result"},
		},
	}, g.handleGenerateDebuggingPrompt)

	// Tool 7: start_debugging_session
	s.AddTool(mcp.Tool{
		Name:        "start_debugging_session",
		Description: "Start a new debugging session for a failing Ginkgo test",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"test_name": map[string]interface{}{
					"type":        "string",
					"description": "Name of the failing test spec",
				},
				"failure_type": map[string]interface{}{
					"type":        "string",
					"description": "Type of failure (e.g., 'assertion', 'panic', 'timeout')",
				},
				"metadata": map[string]interface{}{
					"type":        "object",
					"description": "Additional metadata about the test failure",
				},
			},
			Required: []string{"test_name", "failure_type"},
		},
	}, g.handleStartDebuggingSession)

	// Tool 8: track_debugging_step
	s.AddTool(mcp.Tool{
		Name:        "track_debugging_step",
		Description: "Track a debugging step in an active session",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"session_id": map[string]interface{}{
					"type":        "string",
					"description": "ID of the debugging session",
				},
				"description": map[string]interface{}{
					"type":        "string",
					"description": "Description of the debugging step",
				},
				"action": map[string]interface{}{
					"type":        "string",
					"description": "Action taken during this step",
				},
				"result": map[string]interface{}{
					"type":        "string",
					"description": "Result of the debugging action",
				},
				"data": map[string]interface{}{
					"type":        "object",
					"description": "Additional data for this step",
				},
			},
			Required: []string{"session_id", "description", "action", "result"},
		},
	}, g.handleTrackDebuggingStep)

	// Tool 9: run_benchmarks
	s.AddTool(mcp.Tool{
		Name:        "run_benchmarks",
		Description: "Run benchmarks for a Go package and analyze performance",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"package_path": map[string]interface{}{
					"type":        "string",
					"description": "Path to the Go package to benchmark",
				},
				"bench_time": map[string]interface{}{
					"type":        "string",
					"description": "Time to run each benchmark (e.g., '10s')",
					"default":     "1s",
				},
				"count": map[string]interface{}{
					"type":        "integer",
					"description": "Number of times to run each benchmark",
					"default":     1,
				},
			},
			Required: []string{"package_path"},
		},
	}, g.handleRunBenchmarks)

	// Tool 10: get_failure_patterns
	s.AddTool(mcp.Tool{
		Name:        "get_failure_patterns",
		Description: "Get statistics about historical Ginkgo test failure patterns",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"limit": map[string]interface{}{
					"type":        "integer",
					"description": "Maximum number of patterns to return",
					"default":     10,
				},
			},
		},
	}, g.handleGetFailurePatterns)

	// Tool 11: generate_coverage_report
	s.AddTool(mcp.Tool{
		Name:        "generate_coverage_report",
		Description: "Generate detailed code coverage report for Ginkgo tests",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"package_path": map[string]interface{}{
					"type":        "string",
					"description": "Path to the Go package",
				},
				"output_path": map[string]interface{}{
					"type":        "string",
					"description": "Path to save the coverage report",
					"default":     "./coverage",
				},
			},
			Required: []string{"package_path"},
		},
	}, g.handleGenerateCoverageReport)

	// Tool 12: end_debugging_session
	s.AddTool(mcp.Tool{
		Name:        "end_debugging_session",
		Description: "End a debugging session with resolution or abandonment",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"session_id": map[string]interface{}{
					"type":        "string",
					"description": "ID of the debugging session",
				},
				"status": map[string]interface{}{
					"type":        "string",
					"description": "Final status: 'resolved' or 'abandoned'",
					"enum":        []string{"resolved", "abandoned"},
				},
				"resolution": map[string]interface{}{
					"type":        "string",
					"description": "Description of the resolution or reason for abandonment",
				},
			},
			Required: []string{"session_id", "status"},
		},
	}, g.handleEndDebuggingSession)
}

// Tool handlers

func (g *GinkgoMCPServer) handleFindTestableFunctions(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		PackagePath string `json:"package_path"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	functions, err := g.testGenerator.FindTestableFunctions(args.PackagePath)
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to find testable functions: %v", err)), nil
	}

	result, err := json.MarshalIndent(map[string]interface{}{
		"functions": functions,
		"count":     len(functions),
	}, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

func (g *GinkgoMCPServer) handleGenerateTest(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		PackagePath  string `json:"package_path"`
		FunctionName string `json:"function_name"`
		TestType     string `json:"test_type"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	if args.TestType == "" {
		args.TestType = "basic"
	}

	// Find the function
	functions, err := g.testGenerator.FindTestableFunctions(args.PackagePath)
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to find functions: %v", err)), nil
	}

	var targetFunction *types.TestableFunction
	for _, fn := range functions {
		if fn.FunctionName == args.FunctionName {
			targetFunction = &fn
			break
		}
	}

	if targetFunction == nil {
		return errorResult(fmt.Sprintf("Function %s not found in package", args.FunctionName)), nil
	}

	var generatedTest *types.GeneratedTest
	switch args.TestType {
	case "basic":
		generatedTest, err = g.testGenerator.GenerateTest(*targetFunction)
	case "table_driven":
		generatedTest, err = g.testGenerator.GenerateTableDrivenTest(*targetFunction)
	case "suite":
		suiteCode, err := g.testGenerator.GenerateSuite(targetFunction.PackageName, []types.TestableFunction{*targetFunction})
		if err == nil {
			generatedTest = &types.GeneratedTest{
				FunctionName: targetFunction.FunctionName,
				TestCode:     suiteCode,
				Imports:      []string{"testing", "github.com/onsi/ginkgo/v2", "github.com/onsi/gomega"},
			}
		}
	default:
		return errorResult(fmt.Sprintf("Invalid test type: %s", args.TestType)), nil
	}

	if err != nil {
		return errorResult(fmt.Sprintf("Failed to generate test: %v", err)), nil
	}

	result, err := json.MarshalIndent(generatedTest, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

func (g *GinkgoMCPServer) handleRunTests(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		PackagePath  string `json:"package_path"`
		Focus        string `json:"focus"`
		Skip         string `json:"skip"`
		WithCoverage bool   `json:"with_coverage"`
		Verbose      bool   `json:"verbose"`
		Parallel     int    `json:"parallel"`
		Timeout      string `json:"timeout"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	if args.Timeout == "" {
		args.Timeout = "5m"
	}

	options := &testrunner.RunOptions{
		Verbose:      args.Verbose,
		WithCoverage: args.WithCoverage,
		Focus:        args.Focus,
		Skip:         args.Skip,
		Parallel:     args.Parallel,
		Timeout:      args.Timeout,
	}

	suite, err := g.testRunner.RunTests(ctx, args.PackagePath, options)
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to run tests: %v", err)), nil
	}

	// Analyze results
	analysis, err := g.analyzer.AnalyzeTestResults(suite.Tests)
	if err != nil {
		log.Printf("Warning: failed to analyze test results: %v", err)
	}

	result, err := json.MarshalIndent(map[string]interface{}{
		"suite":    suite,
		"analysis": analysis,
	}, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

func (g *GinkgoMCPServer) handleAnalyzeTestFailures(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		TestResults string `json:"test_results"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	var testResults []types.TestResult

	// Try to parse as JSON
	if err := json.Unmarshal([]byte(args.TestResults), &testResults); err != nil {
		// Try to load from file
		if utils.FileExists(args.TestResults) {
			if err := utils.LoadFromJSON(args.TestResults, &testResults); err != nil {
				return errorResult(fmt.Sprintf("Failed to load test results: %v", err)), nil
			}
		} else {
			return errorResult("Invalid test results format"), nil
		}
	}

	analysis, err := g.analyzer.AnalyzeTestResults(testResults)
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to analyze test results: %v", err)), nil
	}

	result, err := json.MarshalIndent(analysis, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

func (g *GinkgoMCPServer) handleFindSimilarFailures(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		TestName     string `json:"test_name"`
		ErrorMessage string `json:"error_message"`
		Limit        int    `json:"limit"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	if args.Limit == 0 {
		args.Limit = 5
	}

	testResult := types.TestResult{
		SpecName:       args.TestName,
		Status:         types.TestStatusFailed,
		FailureMessage: args.ErrorMessage,
	}

	similar, err := g.analyzer.FindSimilarFailures(testResult, args.Limit)
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to find similar failures: %v", err)), nil
	}

	result, err := json.MarshalIndent(map[string]interface{}{
		"similar_failures": similar,
		"count":            len(similar),
	}, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

func (g *GinkgoMCPServer) handleGenerateDebuggingPrompt(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		TestResult     string `json:"test_result"`
		IncludeSimilar bool   `json:"include_similar"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	var testResult types.TestResult
	if err := json.Unmarshal([]byte(args.TestResult), &testResult); err != nil {
		return errorResult(fmt.Sprintf("Invalid test result format: %v", err)), nil
	}

	var similarFailures []types.TestResult
	if args.IncludeSimilar {
		similarFailures, _ = g.analyzer.FindSimilarFailures(testResult, 5)
	}

	prompt, err := g.analyzer.GenerateDebuggingPrompt(testResult, similarFailures)
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to generate debugging prompt: %v", err)), nil
	}

	return mcp.NewToolResultText(prompt), nil
}

func (g *GinkgoMCPServer) handleStartDebuggingSession(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		TestName    string            `json:"test_name"`
		FailureType string            `json:"failure_type"`
		Metadata    map[string]string `json:"metadata"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	sessionID := utils.GenerateID(fmt.Sprintf("%s-%s-%d", args.TestName, args.FailureType, time.Now().UnixNano()))

	session := &types.DebuggingSession{
		ID:          sessionID,
		TestName:    args.TestName,
		FailureType: args.FailureType,
		StartTime:   time.Now(),
		Status:      types.DebuggingStatusActive,
		Steps:       []types.DebuggingStep{},
		Metadata:    args.Metadata,
	}

	g.sessions[sessionID] = session

	result, err := json.MarshalIndent(session, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

func (g *GinkgoMCPServer) handleTrackDebuggingStep(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		SessionID   string                 `json:"session_id"`
		Description string                 `json:"description"`
		Action      string                 `json:"action"`
		Result      string                 `json:"result"`
		Data        map[string]interface{} `json:"data"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	session, exists := g.sessions[args.SessionID]
	if !exists {
		return errorResult(fmt.Sprintf("Debugging session %s not found", args.SessionID)), nil
	}

	stepID := utils.GenerateID(fmt.Sprintf("%s-%d", args.SessionID, len(session.Steps)))

	step := types.DebuggingStep{
		ID:          stepID,
		Description: args.Description,
		Action:      args.Action,
		Result:      args.Result,
		Timestamp:   time.Now(),
		Data:        args.Data,
	}

	session.Steps = append(session.Steps, step)

	result, err := json.MarshalIndent(session, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

func (g *GinkgoMCPServer) handleRunBenchmarks(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		PackagePath string `json:"package_path"`
		BenchTime   string `json:"bench_time"`
		Count       int    `json:"count"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	if args.BenchTime == "" {
		args.BenchTime = "1s"
	}
	if args.Count == 0 {
		args.Count = 1
	}

	options := &testrunner.BenchmarkOptions{
		BenchTime: args.BenchTime,
		Count:     args.Count,
	}

	benchmarks, err := g.testRunner.RunBenchmarks(ctx, args.PackagePath, options)
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to run benchmarks: %v", err)), nil
	}

	result, err := json.MarshalIndent(map[string]interface{}{
		"benchmarks": benchmarks,
		"count":      len(benchmarks),
	}, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

func (g *GinkgoMCPServer) handleGetFailurePatterns(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		Limit int `json:"limit"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	if args.Limit == 0 {
		args.Limit = 10
	}

	patterns, err := g.analyzer.GetFailurePatternStats()
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to get failure patterns: %v", err)), nil
	}

	// Limit results
	if len(patterns) > args.Limit {
		patterns = patterns[:args.Limit]
	}

	result, err := json.MarshalIndent(map[string]interface{}{
		"patterns": patterns,
		"count":    len(patterns),
	}, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

func (g *GinkgoMCPServer) handleGenerateCoverageReport(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		PackagePath string `json:"package_path"`
		OutputPath  string `json:"output_path"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	if args.OutputPath == "" {
		args.OutputPath = "./coverage"
	}

	err := g.testRunner.GenerateCoverageReport(ctx, args.PackagePath, args.OutputPath)
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to generate coverage report: %v", err)), nil
	}

	result := map[string]interface{}{
		"status":       "success",
		"message":      "Coverage report generated successfully",
		"output_path":  args.OutputPath,
		"profile_file": fmt.Sprintf("%s/coverage.out", args.OutputPath),
		"html_file":    fmt.Sprintf("%s/coverage.html", args.OutputPath),
	}

	resultJSON, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(resultJSON)), nil
}

func (g *GinkgoMCPServer) handleEndDebuggingSession(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		SessionID  string `json:"session_id"`
		Status     string `json:"status"`
		Resolution string `json:"resolution"`
	}

	if err := parseArguments(request.Params.Arguments, &args); err != nil {
		return errorResult(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	session, exists := g.sessions[args.SessionID]
	if !exists {
		return errorResult(fmt.Sprintf("Debugging session %s not found", args.SessionID)), nil
	}

	now := time.Now()
	session.EndTime = &now
	session.Resolution = args.Resolution

	switch args.Status {
	case "resolved":
		session.Status = types.DebuggingStatusResolved
	case "abandoned":
		session.Status = types.DebuggingStatusAbandoned
	default:
		return errorResult(fmt.Sprintf("Invalid status: %s", args.Status)), nil
	}

	result, err := json.MarshalIndent(session, "", "  ")
	if err != nil {
		return errorResult(fmt.Sprintf("Failed to marshal results: %v", err)), nil
	}

	return mcp.NewToolResultText(string(result)), nil
}

// Helper functions

func parseArguments(args interface{}, target interface{}) error {
	jsonData, err := json.Marshal(args)
	if err != nil {
		return fmt.Errorf("failed to marshal arguments: %w", err)
	}

	if err := json.Unmarshal(jsonData, target); err != nil {
		return fmt.Errorf("failed to unmarshal arguments: %w", err)
	}

	return nil
}

func errorResult(message string) *mcp.CallToolResult {
	result := mcp.NewToolResultError(message)
	return result
}