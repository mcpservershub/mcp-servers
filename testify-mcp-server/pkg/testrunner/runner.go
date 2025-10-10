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

	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/types"
)

type Runner struct {
	workDir string
}

func NewRunner(workDir string) *Runner {
	return &Runner{
		workDir: workDir,
	}
}

func (r *Runner) RunTests(ctx context.Context, packagePath string, options *RunOptions) (*types.TestSuite, error) {
	if options == nil {
		options = &RunOptions{}
	}

	args := r.buildTestArgs(packagePath, options)

	cmd := exec.CommandContext(ctx, "go", args...)
	cmd.Dir = r.workDir

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	startTime := time.Now()
	err := cmd.Run()
	duration := time.Since(startTime)

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

	if options.WithCoverage {
		coverage, coverageErr := r.parseCoverageOutput(stdout.String())
		if coverageErr == nil {
			suite.Coverage = coverage
		}
	}

	if err != nil && len(results) == 0 {
		return nil, fmt.Errorf("test execution failed: %w", err)
	}

	return suite, nil
}

func (r *Runner) RunSpecificTest(ctx context.Context, packagePath, testName string, options *RunOptions) (*types.TestResult, error) {
	if options == nil {
		options = &RunOptions{}
	}

	options.TestPattern = testName
	suite, err := r.RunTests(ctx, packagePath, options)
	if err != nil {
		return nil, err
	}

	for _, test := range suite.Tests {
		if test.TestName == testName {
			return &test, nil
		}
	}

	return nil, fmt.Errorf("test %s not found in results", testName)
}

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
	if options.MemProfile {
		args = append(args, "-memprofile=mem.prof")
	}
	if options.CPUProfile {
		args = append(args, "-cpuprofile=cpu.prof")
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

func (r *Runner) buildTestArgs(packagePath string, options *RunOptions) []string {
	args := []string{"test"}

	if options.Verbose {
		args = append(args, "-v")
	}

	if options.WithCoverage {
		args = append(args, "-cover")
		if options.CoverageProfile != "" {
			args = append(args, "-coverprofile="+options.CoverageProfile)
		}
	}

	if options.TestPattern != "" {
		args = append(args, "-run="+options.TestPattern)
	}

	if options.Count > 0 {
		args = append(args, "-count="+strconv.Itoa(options.Count))
	}

	if options.Timeout != "" {
		args = append(args, "-timeout="+options.Timeout)
	}

	if options.Parallel > 0 {
		args = append(args, "-parallel="+strconv.Itoa(options.Parallel))
	}

	if options.JSON {
		args = append(args, "-json")
	}

	args = append(args, packagePath)
	return args
}

func (r *Runner) parseTestOutput(stdout, stderr string) ([]types.TestResult, error) {
	var results []types.TestResult

	lines := strings.Split(stdout, "\n")
	testRegex := regexp.MustCompile(`^=== RUN\s+(\w+)`)
	resultRegex := regexp.MustCompile(`^\s*--- (PASS|FAIL|SKIP):\s+(\w+)\s+\(([0-9.]+)s\)`)
	failureRegex := regexp.MustCompile(`^\s+(.+)$`)

	var currentTest *types.TestResult
	var inFailureMode bool

	for _, line := range lines {
		line = strings.TrimSpace(line)

		if testMatch := testRegex.FindStringSubmatch(line); testMatch != nil {
			if currentTest != nil {
				results = append(results, *currentTest)
			}

			currentTest = &types.TestResult{
				TestName:     testMatch[1],
				FunctionName: testMatch[1],
				Timestamp:    time.Now(),
				Status:       types.TestStatusFailed,
				Metadata:     make(map[string]string),
			}
			inFailureMode = false
		}

		if resultMatch := resultRegex.FindStringSubmatch(line); resultMatch != nil && currentTest != nil {
			status := strings.ToLower(resultMatch[1])
			duration, _ := strconv.ParseFloat(resultMatch[3], 64)

			currentTest.Duration = time.Duration(duration * float64(time.Second))

			switch status {
			case "pass":
				currentTest.Status = types.TestStatusPassed
			case "fail":
				currentTest.Status = types.TestStatusFailed
				inFailureMode = true
			case "skip":
				currentTest.Status = types.TestStatusSkipped
			}
		}

		if inFailureMode && currentTest != nil {
			if failureMatch := failureRegex.FindStringSubmatch(line); failureMatch != nil {
				if currentTest.Error != "" {
					currentTest.Error += "\n"
				}
				currentTest.Error += failureMatch[1]
			}
		}

		if strings.Contains(line, "panic:") && currentTest != nil {
			currentTest.Status = types.TestStatusPanic
			if currentTest.Error == "" {
				currentTest.Error = line
			}
		}
	}

	if currentTest != nil {
		results = append(results, *currentTest)
	}

	if len(results) == 0 && stderr != "" {
		results = r.parseJSONOutput(stdout)
	}

	return results, nil
}

func (r *Runner) parseJSONOutput(output string) []types.TestResult {
	var results []types.TestResult
	lines := strings.Split(output, "\n")

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		var event struct {
			Time    string  `json:"Time"`
			Action  string  `json:"Action"`
			Package string  `json:"Package"`
			Test    string  `json:"Test"`
			Elapsed float64 `json:"Elapsed"`
			Output  string  `json:"Output"`
		}

		if err := json.Unmarshal([]byte(line), &event); err != nil {
			continue
		}

		if event.Action == "pass" || event.Action == "fail" || event.Action == "skip" {
			timestamp, _ := time.Parse(time.RFC3339Nano, event.Time)

			var status types.TestStatus
			switch event.Action {
			case "pass":
				status = types.TestStatusPassed
			case "fail":
				status = types.TestStatusFailed
			case "skip":
				status = types.TestStatusSkipped
			}

			result := types.TestResult{
				PackageName:  event.Package,
				TestName:     event.Test,
				FunctionName: event.Test,
				Status:       status,
				Duration:     time.Duration(event.Elapsed * float64(time.Second)),
				Output:       event.Output,
				Timestamp:    timestamp,
				Metadata:     make(map[string]string),
			}

			results = append(results, result)
		}
	}

	return results
}

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
		}
	}
}

func (r *Runner) GenerateCoverageReport(ctx context.Context, packagePath string, outputPath string) error {
	profilePath := filepath.Join(outputPath, "coverage.out")
	htmlPath := filepath.Join(outputPath, "coverage.html")

	options := &RunOptions{
		WithCoverage:    true,
		CoverageProfile: profilePath,
	}

	_, err := r.RunTests(ctx, packagePath, options)
	if err != nil {
		return fmt.Errorf("failed to run tests with coverage: %w", err)
	}

	if _, err := os.Stat(profilePath); os.IsNotExist(err) {
		return fmt.Errorf("coverage profile not generated")
	}

	cmd := exec.CommandContext(ctx, "go", "tool", "cover", "-html="+profilePath, "-o", htmlPath)
	cmd.Dir = r.workDir

	err = cmd.Run()
	if err != nil {
		return fmt.Errorf("failed to generate HTML coverage report: %w", err)
	}

	return nil
}

type RunOptions struct {
	Verbose         bool
	WithCoverage    bool
	CoverageProfile string
	TestPattern     string
	Count           int
	Timeout         string
	Parallel        int
	JSON            bool
}

type BenchmarkOptions struct {
	BenchTime  string
	Count      int
	MemProfile bool
	CPUProfile bool
}