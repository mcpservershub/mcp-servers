package analyzer

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"

	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/types"
	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/utils"
)

type Analyzer struct {
	dataDir string
}

func NewAnalyzer(dataDir string) *Analyzer {
	return &Analyzer{
		dataDir: dataDir,
	}
}

func (a *Analyzer) AnalyzeTestResults(results []types.TestResult) *TestAnalysis {
	analysis := &TestAnalysis{
		Timestamp:        time.Now(),
		TotalTests:       len(results),
		FailurePatterns:  utils.ExtractFailurePatterns(results),
		TestTrends:       a.analyzeTestTrends(results),
		PerformanceStats: a.analyzePerformance(results),
		CoverageStats:    a.analyzeCoverage(results),
	}

	for _, result := range results {
		switch result.Status {
		case types.TestStatusPassed:
			analysis.PassedTests++
		case types.TestStatusFailed, types.TestStatusPanic:
			analysis.FailedTests++
		case types.TestStatusSkipped:
			analysis.SkippedTests++
		}
	}

	if analysis.TotalTests > 0 {
		analysis.PassRate = float64(analysis.PassedTests) / float64(analysis.TotalTests) * 100
	}

	return analysis
}

func (a *Analyzer) FindSimilarFailures(testResult types.TestResult, limit int) ([]types.TestResult, error) {
	historyFile := filepath.Join(a.dataDir, "test_history.json")

	var history []types.TestResult
	if err := utils.LoadFromJSON(historyFile, &history); err != nil {
		if !os.IsNotExist(err) {
			return nil, fmt.Errorf("failed to load test history: %w", err)
		}
	}

	var similarFailures []types.TestResult
	targetPattern := utils.ExtractFailurePatterns([]types.TestResult{testResult})

	if len(targetPattern) == 0 {
		return similarFailures, nil
	}

	pattern := targetPattern[0].Pattern

	for _, historicResult := range history {
		if historicResult.Status == types.TestStatusFailed {
			historicPatterns := utils.ExtractFailurePatterns([]types.TestResult{historicResult})
			if len(historicPatterns) > 0 && historicPatterns[0].Pattern == pattern {
				similarFailures = append(similarFailures, historicResult)
			}
		}
	}

	sort.Slice(similarFailures, func(i, j int) bool {
		return similarFailures[i].Timestamp.After(similarFailures[j].Timestamp)
	})

	if len(similarFailures) > limit {
		similarFailures = similarFailures[:limit]
	}

	return similarFailures, nil
}

func (a *Analyzer) GenerateDebuggingPrompt(testResult types.TestResult, similarFailures []types.TestResult) string {
	prompt := fmt.Sprintf(`# Test Failure Analysis

## Failed Test
- **Test Name**: %s
- **Function**: %s
- **Package**: %s
- **Status**: %s
- **Duration**: %s
- **Error**: %s

`, testResult.TestName, testResult.FunctionName, testResult.PackageName,
   testResult.Status, testResult.Duration, testResult.Error)

	if testResult.Output != "" {
		prompt += fmt.Sprintf("**Output**:\n```\n%s\n```\n\n", testResult.Output)
	}

	patterns := utils.ExtractFailurePatterns([]types.TestResult{testResult})
	if len(patterns) > 0 {
		pattern := patterns[0]
		prompt += fmt.Sprintf(`## Failure Pattern
- **Type**: %s
- **Description**: %s

### Suggested Actions
`, pattern.Pattern, pattern.Description)

		for _, suggestion := range pattern.Suggestions {
			prompt += fmt.Sprintf("- %s\n", suggestion)
		}
		prompt += "\n"
	}

	if len(similarFailures) > 0 {
		prompt += `## Similar Historical Failures
Recent tests with similar failure patterns:

`
		for i, failure := range similarFailures {
			if i >= 3 {
				break
			}
			prompt += fmt.Sprintf("- **%s** (%s): %s\n",
				failure.TestName, failure.Timestamp.Format("2006-01-02"), failure.Error)
		}
		prompt += "\n"
	}

	prompt += `## Debugging Questions
1. What is the root cause of this failure?
2. Are there any related code changes that might have caused this?
3. What additional tests should be added to prevent similar failures?
4. How can the error handling be improved?

## Next Steps
Please analyze the failure and provide:
- Root cause analysis
- Recommended fixes
- Prevention strategies
- Additional test cases needed
`

	return prompt
}

func (a *Analyzer) TrackFailurePattern(pattern types.FailurePattern) error {
	patternsFile := filepath.Join(a.dataDir, "failure_patterns.json")

	var patterns []types.FailurePattern
	if err := utils.LoadFromJSON(patternsFile, &patterns); err != nil {
		if !os.IsNotExist(err) {
			return fmt.Errorf("failed to load patterns: %w", err)
		}
	}

	found := false
	for i, p := range patterns {
		if p.Pattern == pattern.Pattern {
			patterns[i].Count += pattern.Count
			patterns[i].LastSeen = pattern.LastSeen
			patterns[i].Tests = append(patterns[i].Tests, pattern.Tests...)
			found = true
			break
		}
	}

	if !found {
		patterns = append(patterns, pattern)
	}

	return utils.SaveToJSON(patterns, patternsFile)
}

func (a *Analyzer) GetFailurePatternStats() ([]types.FailurePattern, error) {
	patternsFile := filepath.Join(a.dataDir, "failure_patterns.json")

	var patterns []types.FailurePattern
	if err := utils.LoadFromJSON(patternsFile, &patterns); err != nil {
		if os.IsNotExist(err) {
			return []types.FailurePattern{}, nil
		}
		return nil, fmt.Errorf("failed to load patterns: %w", err)
	}

	sort.Slice(patterns, func(i, j int) bool {
		return patterns[i].Count > patterns[j].Count
	})

	return patterns, nil
}

func (a *Analyzer) SaveTestResults(results []types.TestResult) error {
	historyFile := filepath.Join(a.dataDir, "test_history.json")

	var history []types.TestResult
	if err := utils.LoadFromJSON(historyFile, &history); err != nil {
		if !os.IsNotExist(err) {
			return fmt.Errorf("failed to load history: %w", err)
		}
	}

	history = append(history, results...)

	cutoff := time.Now().AddDate(0, -3, 0)
	var filteredHistory []types.TestResult
	for _, result := range history {
		if result.Timestamp.After(cutoff) {
			filteredHistory = append(filteredHistory, result)
		}
	}

	return utils.SaveToJSON(filteredHistory, historyFile)
}

func (a *Analyzer) analyzeTestTrends(results []types.TestResult) TestTrends {
	trends := TestTrends{
		TestsByDay:    make(map[string]int),
		FailuresByDay: make(map[string]int),
	}

	for _, result := range results {
		day := result.Timestamp.Format("2006-01-02")
		trends.TestsByDay[day]++

		if result.Status == types.TestStatusFailed || result.Status == types.TestStatusPanic {
			trends.FailuresByDay[day]++
		}
	}

	return trends
}

func (a *Analyzer) analyzePerformance(results []types.TestResult) PerformanceStats {
	if len(results) == 0 {
		return PerformanceStats{}
	}

	var durations []time.Duration
	var totalDuration time.Duration

	for _, result := range results {
		durations = append(durations, result.Duration)
		totalDuration += result.Duration
	}

	sort.Slice(durations, func(i, j int) bool {
		return durations[i] < durations[j]
	})

	stats := PerformanceStats{
		AverageTestDuration: totalDuration / time.Duration(len(results)),
		FastestTest:        durations[0],
		SlowestTest:       durations[len(durations)-1],
	}

	if len(durations)%2 == 0 {
		mid := len(durations) / 2
		stats.MedianTestDuration = (durations[mid-1] + durations[mid]) / 2
	} else {
		stats.MedianTestDuration = durations[len(durations)/2]
	}

	return stats
}

func (a *Analyzer) analyzeCoverage(results []types.TestResult) CoverageStats {
	var totalCoverage float64
	var coveredTests int

	for _, result := range results {
		if result.Coverage != nil {
			totalCoverage += result.Coverage.Percentage
			coveredTests++
		}
	}

	stats := CoverageStats{}
	if coveredTests > 0 {
		stats.AverageCoverage = totalCoverage / float64(coveredTests)
	}

	return stats
}

func (a *Analyzer) GenerateTestReport(analysis *TestAnalysis, outputPath string) error {
	report := TestReport{
		Analysis:      *analysis,
		GeneratedAt:   time.Now(),
		ReportVersion: "1.0",
	}

	reportData, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal report: %w", err)
	}

	err = os.WriteFile(outputPath, reportData, 0644)
	if err != nil {
		return fmt.Errorf("failed to write report: %w", err)
	}

	return nil
}

type TestAnalysis struct {
	Timestamp        time.Time               `json:"timestamp"`
	TotalTests       int                     `json:"total_tests"`
	PassedTests      int                     `json:"passed_tests"`
	FailedTests      int                     `json:"failed_tests"`
	SkippedTests     int                     `json:"skipped_tests"`
	PassRate         float64                 `json:"pass_rate"`
	FailurePatterns  []types.FailurePattern  `json:"failure_patterns"`
	TestTrends       TestTrends              `json:"test_trends"`
	PerformanceStats PerformanceStats        `json:"performance_stats"`
	CoverageStats    CoverageStats           `json:"coverage_stats"`
}

type TestTrends struct {
	TestsByDay    map[string]int `json:"tests_by_day"`
	FailuresByDay map[string]int `json:"failures_by_day"`
}

type PerformanceStats struct {
	AverageTestDuration time.Duration `json:"average_test_duration"`
	MedianTestDuration  time.Duration `json:"median_test_duration"`
	FastestTest        time.Duration `json:"fastest_test"`
	SlowestTest        time.Duration `json:"slowest_test"`
}

type CoverageStats struct {
	AverageCoverage float64 `json:"average_coverage"`
}

type TestReport struct {
	Analysis      TestAnalysis `json:"analysis"`
	GeneratedAt   time.Time    `json:"generated_at"`
	ReportVersion string       `json:"report_version"`
}