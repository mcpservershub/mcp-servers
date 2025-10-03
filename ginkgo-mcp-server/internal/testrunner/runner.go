package testrunner

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/mcpservershub/mcpservers/ginkgo-mcp/pkg/types"
)

// Runner executes Ginkgo tests and parses results
type Runner struct {
	workDir string
}

// NewRunner creates a new Ginkgo test runner
func NewRunner(workDir string) *Runner {
	return &Runner{
		workDir: workDir,
	}
}

// RunTests executes Ginkgo tests for a package
func (r *Runner) RunTests(ctx context.Context, packagePath string, options *RunOptions) (*types.TestSuite, error) {
	if options == nil {
		options = &RunOptions{}
	}

	args := r.buildTestArgs(packagePath, options)

	cmd := exec.CommandContext(ctx, "ginkgo", args...)
	cmd.Dir = r.workDir

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	startTime := time.Now()
	err := cmd.Run()
	duration := time.Since(startTime)

	// Parse the output
	results, parseErr := r.parseTestOutput(stdout.String(), stderr.String())
	if parseErr != nil {
		return nil, fmt.Errorf("failed to parse test output: %w", parseErr)
	}

	suite := &types.TestSuite{
		Name:      packagePath,
		Tests:     results,
		Duration:  duration,
		Timestamp: startTime,
	}

	r.calculateTestSuiteStats(suite)

	// Parse coverage if requested
	if options.WithCoverage {
		coverage, coverageErr := r.parseCoverageOutput(stdout.String())
		if coverageErr == nil {
			suite.Coverage = coverage
		}
	}

	// If command failed and no results, return error
	if err != nil && len(results) == 0 {
		return nil, fmt.Errorf("test execution failed: %w\nStderr: %s", err, stderr.String())
	}

	return suite, nil
}

// RunSpecificTest runs a specific Ginkgo test by focus
func (r *Runner) RunSpecificTest(ctx context.Context, packagePath, testPattern string, options *RunOptions) (*types.TestResult, error) {
	if options == nil {
		options = &RunOptions{}
	}

	options.Focus = testPattern
	suite, err := r.RunTests(ctx, packagePath, options)
	if err != nil {
		return nil, err
	}

	// Find the matching test
	for _, test := range suite.Tests {
		if strings.Contains(test.FullText, testPattern) || strings.Contains(test.SpecName, testPattern) {
			return &test, nil
		}
	}

	return nil, fmt.Errorf("test matching pattern %s not found in results", testPattern)
}

// RunWithJSONOutput runs tests with JSON output format
func (r *Runner) RunWithJSONOutput(ctx context.Context, packagePath string, options *RunOptions) (*types.TestSuite, error) {
	if options == nil {
		options = &RunOptions{}
	}

	options.JSONReport = true

	// Create temp file for JSON output
	tmpFile := filepath.Join(r.workDir, ".ginkgo-report.json")
	defer os.Remove(tmpFile)

	args := r.buildTestArgs(packagePath, options)
	args = append(args, fmt.Sprintf("--json-report=%s", tmpFile))

	cmd := exec.CommandContext(ctx, "ginkgo", args...)
	cmd.Dir = r.workDir

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	startTime := time.Now()
	err := cmd.Run()
	duration := time.Since(startTime)

	// Try to read JSON report
	var results []types.TestResult
	if _, statErr := os.Stat(tmpFile); statErr == nil {
		jsonResults, jsonErr := r.parseJSONReport(tmpFile)
		if jsonErr == nil {
			results = jsonResults
		}
	}

	// Fallback to text parsing if JSON failed
	if len(results) == 0 {
		results, _ = r.parseTestOutput(stdout.String(), stderr.String())
	}

	suite := &types.TestSuite{
		Name:      packagePath,
		Tests:     results,
		Duration:  duration,
		Timestamp: startTime,
	}

	r.calculateTestSuiteStats(suite)

	if err != nil && len(results) == 0 {
		return nil, fmt.Errorf("test execution failed: %w\nStderr: %s", err, stderr.String())
	}

	return suite, nil
}

// buildTestArgs constructs Ginkgo CLI arguments
func (r *Runner) buildTestArgs(packagePath string, options *RunOptions) []string {
	var args []string

	if options.Verbose {
		args = append(args, "-v")
	}

	if options.WithCoverage {
		args = append(args, "--cover")
		if options.CoverageProfile != "" {
			args = append(args, fmt.Sprintf("--coverprofile=%s", options.CoverageProfile))
		}
	}

	if options.Focus != "" {
		args = append(args, fmt.Sprintf("--focus=%s", options.Focus))
	}

	if options.Skip != "" {
		args = append(args, fmt.Sprintf("--skip=%s", options.Skip))
	}

	if options.Parallel > 0 {
		args = append(args, fmt.Sprintf("-p=%d", options.Parallel))
	}

	if options.RandomSeed > 0 {
		args = append(args, fmt.Sprintf("--seed=%d", options.RandomSeed))
	}

	if options.Timeout != "" {
		args = append(args, fmt.Sprintf("--timeout=%s", options.Timeout))
	}

	if options.FailFast {
		args = append(args, "--fail-fast")
	}

	if options.Trace {
		args = append(args, "--trace")
	}

	if options.Progress {
		args = append(args, "--progress")
	}

	// Add package path
	args = append(args, packagePath)

	return args
}

// parseTestOutput parses Ginkgo text output
func (r *Runner) parseTestOutput(stdout, stderr string) ([]types.TestResult, error) {
	var results []types.TestResult

	lines := strings.Split(stdout, "\n")

	// Regex patterns for Ginkgo output
	specRunRegex := regexp.MustCompile(`^•`)
	passRegex := regexp.MustCompile(`^✓`)
	failRegex := regexp.MustCompile(`^✗`)
	skipRegex := regexp.MustCompile(`^S`)
	pendingRegex := regexp.MustCompile(`^P`)

	// Pattern for spec descriptions
	descRegex := regexp.MustCompile(`^\s*(.+?)\s+\[(.+?)\]`)

	// Pattern for failure details
	failureRegex := regexp.MustCompile(`\[FAILED\](.+)$`)
	locationRegex := regexp.MustCompile(`^\s*(.+):(\d+)`)

	var currentTest *types.TestResult
	var inFailureBlock bool
	var failureLines []string

	for i, line := range lines {
		line = strings.TrimRight(line, "\r\n")

		// Check for spec execution
		if specRunRegex.MatchString(line) || passRegex.MatchString(line) ||
		   failRegex.MatchString(line) || skipRegex.MatchString(line) ||
		   pendingRegex.MatchString(line) {

			// Save previous test if exists
			if currentTest != nil {
				if len(failureLines) > 0 {
					currentTest.FailureMessage = strings.Join(failureLines, "\n")
					failureLines = []string{}
				}
				results = append(results, *currentTest)
			}

			// Determine status
			status := types.TestStatusPassed
			if failRegex.MatchString(line) {
				status = types.TestStatusFailed
				inFailureBlock = true
			} else if skipRegex.MatchString(line) {
				status = types.TestStatusSkipped
			} else if pendingRegex.MatchString(line) {
				status = types.TestStatusPending
			}

			// Extract spec description
			specDesc := strings.TrimLeft(line, "•✓✗SP ")

			// Try to extract timing info
			var duration time.Duration
			if matches := descRegex.FindStringSubmatch(specDesc); len(matches) > 2 {
				specDesc = strings.TrimSpace(matches[1])
				durationStr := matches[2]
				if parsedDur, err := time.ParseDuration(durationStr); err == nil {
					duration = parsedDur
				} else {
					// Try parsing seconds format
					if seconds, err := strconv.ParseFloat(strings.TrimSuffix(durationStr, "s"), 64); err == nil {
						duration = time.Duration(seconds * float64(time.Second))
					}
				}
			}

			currentTest = &types.TestResult{
				SpecName:  specDesc,
				FullText:  specDesc,
				Status:    status,
				Duration:  duration,
				Timestamp: time.Now(),
				Metadata:  make(map[string]string),
			}

			continue
		}

		// Collect failure information
		if inFailureBlock && currentTest != nil {
			if failureMatch := failureRegex.FindStringSubmatch(line); len(failureMatch) > 1 {
				failureLines = append(failureLines, strings.TrimSpace(failureMatch[1]))
			} else if locationMatch := locationRegex.FindStringSubmatch(line); len(locationMatch) > 2 {
				currentTest.FileName = locationMatch[1]
				if lineNum, err := strconv.Atoi(locationMatch[2]); err == nil {
					currentTest.LineNumber = lineNum
				}
				currentTest.FailureLocation = strings.TrimSpace(line)
			} else if strings.TrimSpace(line) != "" && !strings.HasPrefix(line, "-----") {
				failureLines = append(failureLines, strings.TrimSpace(line))
			}

			// Check if failure block ended
			if i+1 < len(lines) && (specRunRegex.MatchString(lines[i+1]) ||
			   passRegex.MatchString(lines[i+1]) || failRegex.MatchString(lines[i+1])) {
				inFailureBlock = false
			}
		}
	}

	// Add last test
	if currentTest != nil {
		if len(failureLines) > 0 {
			currentTest.FailureMessage = strings.Join(failureLines, "\n")
		}
		results = append(results, *currentTest)
	}

	return results, nil
}

// parseJSONReport parses Ginkgo JSON report
func (r *Runner) parseJSONReport(jsonFile string) ([]types.TestResult, error) {
	data, err := os.ReadFile(jsonFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read JSON report: %w", err)
	}

	var report []struct {
		SpecReports []struct {
			LeafNodeText     string  `json:"LeafNodeText"`
			FullText         string  `json:"FullText"`
			State            string  `json:"State"`
			RunTime          float64 `json:"RunTime"`
			FailureMessage   string  `json:"FailureMessage"`
			FailureLocation  struct {
				FileName   string `json:"FileName"`
				LineNumber int    `json:"LineNumber"`
			} `json:"FailureLocation"`
			ContainerHierarchyTexts []string `json:"ContainerHierarchyTexts"`
		} `json:"SpecReports"`
	}

	if err := json.Unmarshal(data, &report); err != nil {
		return nil, fmt.Errorf("failed to parse JSON report: %w", err)
	}

	var results []types.TestResult

	for _, suite := range report {
		for _, spec := range suite.SpecReports {
			status := types.TestStatusPassed
			switch spec.State {
			case "passed":
				status = types.TestStatusPassed
			case "failed":
				status = types.TestStatusFailed
			case "skipped":
				status = types.TestStatusSkipped
			case "pending":
				status = types.TestStatusPending
			case "panicked":
				status = types.TestStatusPanic
			}

			containerName := ""
			if len(spec.ContainerHierarchyTexts) > 0 {
				containerName = strings.Join(spec.ContainerHierarchyTexts, " > ")
			}

			result := types.TestResult{
				SpecName:        spec.LeafNodeText,
				FullText:        spec.FullText,
				ContainerName:   containerName,
				Status:          status,
				Duration:        time.Duration(spec.RunTime * float64(time.Second)),
				FailureMessage:  spec.FailureMessage,
				FileName:        spec.FailureLocation.FileName,
				LineNumber:      spec.FailureLocation.LineNumber,
				FailureLocation: fmt.Sprintf("%s:%d", spec.FailureLocation.FileName, spec.FailureLocation.LineNumber),
				Timestamp:       time.Now(),
				Metadata:        make(map[string]string),
			}

			results = append(results, result)
		}
	}

	return results, nil
}

// parseCoverageOutput extracts coverage information from output
func (r *Runner) parseCoverageOutput(output string) (*types.CoverageInfo, error) {
	coverageRegex := regexp.MustCompile(`coverage:\s+([0-9.]+)%\s+of\s+statements`)

	matches := coverageRegex.FindStringSubmatch(output)
	if len(matches) < 2 {
		return nil, fmt.Errorf("coverage information not found")
	}

	percentage, err := strconv.ParseFloat(matches[1], 64)
	if err != nil {
		return nil, fmt.Errorf("failed to parse coverage percentage: %w", err)
	}

	return &types.CoverageInfo{
		Percentage: percentage,
	}, nil
}

// calculateTestSuiteStats calculates summary statistics for the test suite
func (r *Runner) calculateTestSuiteStats(suite *types.TestSuite) {
	suite.TotalTests = len(suite.Tests)

	for _, test := range suite.Tests {
		switch test.Status {
		case types.TestStatusPassed:
			suite.PassedTests++
		case types.TestStatusFailed, types.TestStatusPanic:
			suite.FailedTests++
		case types.TestStatusSkipped:
			suite.SkippedTests++
		case types.TestStatusPending:
			suite.PendingTests++
		}
	}
}

// GenerateCoverageReport generates HTML coverage report
func (r *Runner) GenerateCoverageReport(ctx context.Context, packagePath string, outputPath string) error {
	profilePath := filepath.Join(outputPath, "coverage.out")
	htmlPath := filepath.Join(outputPath, "coverage.html")

	// Ensure output directory exists
	if err := os.MkdirAll(outputPath, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Run tests with coverage
	options := &RunOptions{
		WithCoverage:    true,
		CoverageProfile: profilePath,
	}

	_, err := r.RunTests(ctx, packagePath, options)
	if err != nil {
		return fmt.Errorf("failed to run tests with coverage: %w", err)
	}

	// Check if profile was generated
	if _, err := os.Stat(profilePath); os.IsNotExist(err) {
		return fmt.Errorf("coverage profile not generated")
	}

	// Generate HTML report
	cmd := exec.CommandContext(ctx, "go", "tool", "cover", "-html="+profilePath, "-o", htmlPath)
	cmd.Dir = r.workDir

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to generate HTML coverage report: %w", err)
	}

	return nil
}

// RunBenchmarks runs Ginkgo benchmarks (using Measure blocks)
func (r *Runner) RunBenchmarks(ctx context.Context, packagePath string, options *BenchmarkOptions) ([]types.BenchmarkResult, error) {
	if options == nil {
		options = &BenchmarkOptions{}
	}

	args := []string{"test", "-bench=."}
	if options.BenchTime != "" {
		args = append(args, "-benchtime="+options.BenchTime)
	}
	if options.Count > 0 {
		args = append(args, "-count="+strconv.Itoa(options.Count))
	}

	args = append(args, packagePath)

	cmd := exec.CommandContext(ctx, "go", args...)
	cmd.Dir = r.workDir

	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stdout

	err := cmd.Run()
	if err != nil {
		return nil, fmt.Errorf("benchmark execution failed: %w", err)
	}

	return r.parseBenchmarkOutput(stdout.String())
}

// parseBenchmarkOutput parses Go benchmark output
func (r *Runner) parseBenchmarkOutput(output string) ([]types.BenchmarkResult, error) {
	var results []types.BenchmarkResult

	benchRegex := regexp.MustCompile(`^Benchmark(\w+)-?\d*\s+(\d+)\s+([0-9.]+)\s+ns/op(?:\s+(\d+)\s+B/op)?(?:\s+(\d+)\s+allocs/op)?`)

	scanner := bufio.NewScanner(strings.NewReader(output))
	for scanner.Scan() {
		line := scanner.Text()

		if matches := benchRegex.FindStringSubmatch(line); matches != nil {
			iterations, _ := strconv.Atoi(matches[2])
			nsPerOp, _ := strconv.ParseFloat(matches[3], 64)

			result := types.BenchmarkResult{
				Name:       matches[1],
				Iterations: iterations,
				NsPerOp:    int64(nsPerOp),
				Timestamp:  time.Now(),
			}

			if len(matches) > 4 && matches[4] != "" {
				result.MemBytesPerOp, _ = strconv.ParseInt(matches[4], 10, 64)
			}

			if len(matches) > 5 && matches[5] != "" {
				result.MemAllocsPerOp, _ = strconv.ParseInt(matches[5], 10, 64)
			}

			results = append(results, result)
		}
	}

	return results, nil
}

// RunOptions contains options for running tests
type RunOptions struct {
	Verbose         bool
	WithCoverage    bool
	CoverageProfile string
	Focus           string
	Skip            string
	Parallel        int
	RandomSeed      int64
	Timeout         string
	FailFast        bool
	Trace           bool
	Progress        bool
	JSONReport      bool
}

// BenchmarkOptions contains options for running benchmarks
type BenchmarkOptions struct {
	BenchTime string
	Count     int
}