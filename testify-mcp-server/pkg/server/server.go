package server

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/analyzer"
	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/testrunner"
	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/tools"
	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/types"
	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/utils"
)

type TestifyMCPServer struct {
	workDir       string
	dataDir       string
	runner        *testrunner.Runner
	analyzer      *analyzer.Analyzer
	testGenerator *tools.TestGenerator
	sessions      map[string]*types.DebuggingSession
}

func NewTestifyMCPServer(workDir, dataDir string) *TestifyMCPServer {
	if err := os.MkdirAll(dataDir, 0755); err != nil {
		log.Printf("Warning: Failed to create data directory: %v", err)
	}

	return &TestifyMCPServer{
		workDir:       workDir,
		dataDir:       dataDir,
		runner:        testrunner.NewRunner(workDir),
		analyzer:      analyzer.NewAnalyzer(dataDir),
		testGenerator: tools.NewTestGenerator(workDir),
		sessions:      make(map[string]*types.DebuggingSession),
	}
}

func (s *TestifyMCPServer) CreateMCPServer() *server.MCPServer {
	mcpServer := server.NewMCPServer("testify-mcp-server", "1.0.0")

	// Register all tools
	mcpServer.AddTools(
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "find_testable_functions",
				Description: "Find all testable functions in a Go package",
			},
			Handler: s.handleFindTestableFunctions,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "generate_test",
				Description: "Generate a test for a specific function using testify framework",
			},
			Handler: s.handleGenerateTest,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "run_tests",
				Description: "Run tests for a specific package and analyze results",
			},
			Handler: s.handleRunTests,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "analyze_test_failures",
				Description: "Analyze test failure patterns and generate debugging insights",
			},
			Handler: s.handleAnalyzeTestFailures,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "find_similar_failures",
				Description: "Find similar historical test failures for debugging insights",
			},
			Handler: s.handleFindSimilarFailures,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "generate_debugging_prompt",
				Description: "Generate AI-friendly debugging prompts for test failures",
			},
			Handler: s.handleGenerateDebuggingPrompt,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "start_debugging_session",
				Description: "Start a new debugging session for a failing test",
			},
			Handler: s.handleStartDebuggingSession,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "track_debugging_step",
				Description: "Track a debugging step in an active session",
			},
			Handler: s.handleTrackDebuggingStep,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "run_benchmarks",
				Description: "Run benchmarks for a Go package and analyze performance",
			},
			Handler: s.handleRunBenchmarks,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "get_failure_patterns",
				Description: "Get statistics about historical failure patterns",
			},
			Handler: s.handleGetFailurePatterns,
		},
		server.ServerTool{
			Tool: mcp.Tool{
				Name:        "generate_coverage_report",
				Description: "Generate detailed code coverage report",
			},
			Handler: s.handleGenerateCoverageReport,
		},
	)

	return mcpServer
}

func (s *TestifyMCPServer) handleFindTestableFunctions(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	packagePath, ok := request.GetArguments()["package_path"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "package_path must be a string",
				},
			},
		}, nil
	}

	functions, err := s.testGenerator.FindTestableFunctions(packagePath)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Failed to find testable functions: %v", err),
				},
			},
		}, nil
	}

	result := map[string]interface{}{
		"package_path":         packagePath,
		"testable_functions":   functions,
		"total_functions":      len(functions),
		"functions_with_tests": countFunctionsWithTests(functions),
		"timestamp":            time.Now(),
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleGenerateTest(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	packagePath, ok := request.GetArguments()["package_path"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "package_path must be a string",
				},
			},
		}, nil
	}

	functionName, ok := request.GetArguments()["function_name"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "function_name must be a string",
				},
			},
		}, nil
	}

	testType := "basic"
	if t, exists := request.GetArguments()["test_type"].(string); exists {
		testType = t
	}

	functions, err := s.testGenerator.FindTestableFunctions(packagePath)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Failed to find functions: %v", err),
				},
			},
		}, nil
	}

	var targetFunction *types.TestableFunction
	for _, fn := range functions {
		if fn.FunctionName == functionName {
			targetFunction = &fn
			break
		}
	}

	if targetFunction == nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Function %s not found in package %s", functionName, packagePath),
				},
			},
		}, nil
	}

	var generatedTest *types.GeneratedTest

	switch testType {
	case "basic":
		generatedTest, err = s.testGenerator.GenerateTest(*targetFunction)
	case "table_driven":
		generatedTest, err = s.testGenerator.GenerateTableDrivenTest(*targetFunction)
	case "benchmark":
		benchmarkCode, benchErr := s.testGenerator.GenerateBenchmark(*targetFunction)
		if benchErr != nil {
			return &mcp.CallToolResult{
				IsError: true,
				Content: []mcp.Content{
					mcp.TextContent{
						Type: "text",
						Text: fmt.Sprintf("Failed to generate benchmark: %v", benchErr),
					},
				},
			}, nil
		}
		generatedTest = &types.GeneratedTest{
			FunctionName: targetFunction.FunctionName,
			TestCode:     benchmarkCode,
			TestCases:    []types.TestCase{},
			Imports:      []string{"testing"},
		}
	default:
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Unknown test type: %s", testType),
				},
			},
		}, nil
	}

	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Failed to generate test: %v", err),
				},
			},
		}, nil
	}

	result := map[string]interface{}{
		"function_name":  functionName,
		"package_path":   packagePath,
		"test_type":      testType,
		"generated_test": generatedTest,
		"timestamp":      time.Now(),
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleRunTests(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	packagePath, ok := request.GetArguments()["package_path"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "package_path must be a string",
				},
			},
		}, nil
	}

	options := &testrunner.RunOptions{
		WithCoverage: true,
		Verbose:      false,
		Timeout:      "5m",
	}

	if testPattern, exists := request.GetArguments()["test_pattern"].(string); exists {
		options.TestPattern = testPattern
	}

	if withCoverage, exists := request.GetArguments()["with_coverage"].(bool); exists {
		options.WithCoverage = withCoverage
	}

	if verbose, exists := request.GetArguments()["verbose"].(bool); exists {
		options.Verbose = verbose
	}

	if timeout, exists := request.GetArguments()["timeout"].(string); exists {
		options.Timeout = timeout
	}

	suite, err := s.runner.RunTests(ctx, packagePath, options)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Failed to run tests: %v", err),
				},
			},
		}, nil
	}

	if err := s.analyzer.SaveTestResults(suite.Tests); err != nil {
		log.Printf("Warning: Failed to save test results: %v", err)
	}

	analysis := s.analyzer.AnalyzeTestResults(suite.Tests)

	result := map[string]interface{}{
		"test_suite": suite,
		"analysis":   analysis,
		"timestamp":  time.Now(),
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleAnalyzeTestFailures(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	testResultsData, ok := request.GetArguments()["test_results"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "test_results must be a string",
				},
			},
		}, nil
	}

	var testResults []types.TestResult

	if filepath.IsAbs(testResultsData) {
		if err := utils.LoadFromJSON(testResultsData, &testResults); err != nil {
			return &mcp.CallToolResult{
				IsError: true,
				Content: []mcp.Content{
					mcp.TextContent{
						Type: "text",
						Text: fmt.Sprintf("Failed to load test results from file: %v", err),
					},
				},
			}, nil
		}
	} else {
		if err := json.Unmarshal([]byte(testResultsData), &testResults); err != nil {
			return &mcp.CallToolResult{
				IsError: true,
				Content: []mcp.Content{
					mcp.TextContent{
						Type: "text",
						Text: fmt.Sprintf("Failed to parse test results JSON: %v", err),
					},
				},
			}, nil
		}
	}

	analysis := s.analyzer.AnalyzeTestResults(testResults)

	for _, pattern := range analysis.FailurePatterns {
		if err := s.analyzer.TrackFailurePattern(pattern); err != nil {
			log.Printf("Warning: Failed to track failure pattern: %v", err)
		}
	}

	result := map[string]interface{}{
		"analysis":  analysis,
		"timestamp": time.Now(),
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleFindSimilarFailures(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	testName, ok := request.GetArguments()["test_name"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "test_name must be a string",
				},
			},
		}, nil
	}

	errorMessage, ok := request.GetArguments()["error_message"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "error_message must be a string",
				},
			},
		}, nil
	}

	limit := 5
	if l, exists := request.GetArguments()["limit"].(float64); exists {
		limit = int(l)
	}

	testResult := types.TestResult{
		TestName:  testName,
		Status:    types.TestStatusFailed,
		Error:     errorMessage,
		Timestamp: time.Now(),
	}

	similarFailures, err := s.analyzer.FindSimilarFailures(testResult, limit)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Failed to find similar failures: %v", err),
				},
			},
		}, nil
	}

	result := map[string]interface{}{
		"test_name":        testName,
		"similar_failures": similarFailures,
		"total_found":      len(similarFailures),
		"timestamp":        time.Now(),
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleGenerateDebuggingPrompt(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	testResultData, ok := request.GetArguments()["test_result"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "test_result must be a string",
				},
			},
		}, nil
	}

	includeSimilar := true
	if include, exists := request.GetArguments()["include_similar"].(bool); exists {
		includeSimilar = include
	}

	var testResult types.TestResult
	if err := json.Unmarshal([]byte(testResultData), &testResult); err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Failed to parse test result JSON: %v", err),
				},
			},
		}, nil
	}

	var similarFailures []types.TestResult
	if includeSimilar {
		var err error
		similarFailures, err = s.analyzer.FindSimilarFailures(testResult, 5)
		if err != nil {
			log.Printf("Warning: Failed to find similar failures: %v", err)
		}
	}

	prompt := s.analyzer.GenerateDebuggingPrompt(testResult, similarFailures)

	result := map[string]interface{}{
		"test_name":        testResult.TestName,
		"debugging_prompt": prompt,
		"similar_failures": len(similarFailures),
		"timestamp":        time.Now(),
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleStartDebuggingSession(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	testName, ok := request.GetArguments()["test_name"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "test_name must be a string",
				},
			},
		}, nil
	}

	failureType, ok := request.GetArguments()["failure_type"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "failure_type must be a string",
				},
			},
		}, nil
	}

	sessionID := utils.GenerateID(testName + failureType)

	session := &types.DebuggingSession{
		ID:          sessionID,
		TestName:    testName,
		FailureType: failureType,
		StartTime:   time.Now(),
		Status:      types.DebuggingStatusActive,
		Steps:       []types.DebuggingStep{},
		Metadata:    make(map[string]string),
	}

	if metadata, exists := request.GetArguments()["metadata"].(map[string]interface{}); exists {
		for k, v := range metadata {
			if str, ok := v.(string); ok {
				session.Metadata[k] = str
			}
		}
	}

	s.sessions[sessionID] = session

	result := map[string]interface{}{
		"session_id":   sessionID,
		"test_name":    testName,
		"failure_type": failureType,
		"status":       session.Status,
		"start_time":   session.StartTime,
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleTrackDebuggingStep(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	sessionID, ok := request.GetArguments()["session_id"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "session_id must be a string",
				},
			},
		}, nil
	}

	description, ok := request.GetArguments()["description"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "description must be a string",
				},
			},
		}, nil
	}

	action, ok := request.GetArguments()["action"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "action must be a string",
				},
			},
		}, nil
	}

	result, ok := request.GetArguments()["result"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "result must be a string",
				},
			},
		}, nil
	}

	session, exists := s.sessions[sessionID]
	if !exists {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Debugging session %s not found", sessionID),
				},
			},
		}, nil
	}

	step := types.DebuggingStep{
		ID:          utils.GenerateID(sessionID + description),
		Description: description,
		Action:      action,
		Result:      result,
		Timestamp:   time.Now(),
		Data:        make(map[string]interface{}),
	}

	if data, exists := request.GetArguments()["data"].(map[string]interface{}); exists {
		step.Data = data
	}

	session.Steps = append(session.Steps, step)

	response := map[string]interface{}{
		"session_id": sessionID,
		"step_id":    step.ID,
		"step_count": len(session.Steps),
		"timestamp":  step.Timestamp,
	}

	responseJSON, _ := json.MarshalIndent(response, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(responseJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleRunBenchmarks(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	packagePath, ok := request.GetArguments()["package_path"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "package_path must be a string",
				},
			},
		}, nil
	}

	options := &testrunner.BenchmarkOptions{
		BenchTime:  "1s",
		Count:      1,
		MemProfile: false,
		CPUProfile: false,
	}

	if benchTime, exists := request.GetArguments()["bench_time"].(string); exists {
		options.BenchTime = benchTime
	}

	if count, exists := request.GetArguments()["count"].(float64); exists {
		options.Count = int(count)
	}

	if memProfile, exists := request.GetArguments()["mem_profile"].(bool); exists {
		options.MemProfile = memProfile
	}

	benchmarks, err := s.runner.RunBenchmarks(ctx, packagePath, options)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Failed to run benchmarks: %v", err),
				},
			},
		}, nil
	}

	result := map[string]interface{}{
		"package_path":     packagePath,
		"benchmarks":       benchmarks,
		"total_benchmarks": len(benchmarks),
		"timestamp":        time.Now(),
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleGetFailurePatterns(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	limit := 10
	if l, exists := request.GetArguments()["limit"].(float64); exists {
		limit = int(l)
	}

	patterns, err := s.analyzer.GetFailurePatternStats()
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Failed to get failure patterns: %v", err),
				},
			},
		}, nil
	}

	if len(patterns) > limit {
		patterns = patterns[:limit]
	}

	result := map[string]interface{}{
		"failure_patterns": patterns,
		"total_patterns":   len(patterns),
		"timestamp":        time.Now(),
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func (s *TestifyMCPServer) handleGenerateCoverageReport(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	packagePath, ok := request.GetArguments()["package_path"].(string)
	if !ok {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: "package_path must be a string",
				},
			},
		}, nil
	}

	outputPath := "./coverage"
	if output, exists := request.GetArguments()["output_path"].(string); exists {
		outputPath = output
	}

	if err := s.runner.GenerateCoverageReport(ctx, packagePath, outputPath); err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				mcp.TextContent{
					Type: "text",
					Text: fmt.Sprintf("Failed to generate coverage report: %v", err),
				},
			},
		}, nil
	}

	result := map[string]interface{}{
		"package_path": packagePath,
		"output_path":  outputPath,
		"profile_file": filepath.Join(outputPath, "coverage.out"),
		"html_report":  filepath.Join(outputPath, "coverage.html"),
		"timestamp":    time.Now(),
	}

	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.TextContent{
				Type: "text",
				Text: string(resultJSON),
			},
		},
	}, nil
}

func countFunctionsWithTests(functions []types.TestableFunction) int {
	count := 0
	for _, fn := range functions {
		if fn.HasTests {
			count++
		}
	}
	return count
}
