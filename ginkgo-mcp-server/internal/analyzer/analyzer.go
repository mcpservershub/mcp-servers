package analyzer

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/mcpservershub/mcpservers/ginkgo-mcp/pkg/types"
	"github.com/mcpservershub/mcpservers/ginkgo-mcp/pkg/utils"
)

// Analyzer analyzes Ginkgo test results and provides insights
type Analyzer struct {
	dataDir string
}

// NewAnalyzer creates a new analyzer instance
func NewAnalyzer(dataDir string) *Analyzer {
	// Ensure data directory exists
	os.MkdirAll(dataDir, 0755)
	return &Analyzer{
		dataDir: dataDir,
	}
}

// TestAnalysis contains detailed analysis of test results
type TestAnalysis struct {
	TotalTests    int                    `json:"total_tests"`
	PassedTests   int                    `json:"passed_tests"`
	FailedTests   int                    `json:"failed_tests"`
	SkippedTests  int                    `json:"skipped_tests"`
	PendingTests  int                    `json:"pending_tests"`
	SuccessRate   float64                `json:"success_rate"`
	FailureRate   float64                `json:"failure_rate"`
	AverageDuration time.Duration        `json:"average_duration"`
	Patterns      []types.FailurePattern `json:"patterns"`
	Insights      []string               `json:"insights"`
	Timestamp     time.Time              `json:"timestamp"`
}

// AnalyzeTestResults analyzes test results and returns insights
func (a *Analyzer) AnalyzeTestResults(results []types.TestResult) (*TestAnalysis, error) {
	if len(results) == 0 {
		return nil, fmt.Errorf("no test results to analyze")
	}

	analysis := &TestAnalysis{
		TotalTests: len(results),
		Timestamp:  time.Now(),
	}

	var totalDuration time.Duration

	// Calculate statistics
	for _, result := range results {
		totalDuration += result.Duration

		switch result.Status {
		case types.TestStatusPassed:
			analysis.PassedTests++
		case types.TestStatusFailed, types.TestStatusPanic:
			analysis.FailedTests++
		case types.TestStatusSkipped:
			analysis.SkippedTests++
		case types.TestStatusPending:
			analysis.PendingTests++
		}
	}

	// Calculate rates
	if analysis.TotalTests > 0 {
		analysis.SuccessRate = float64(analysis.PassedTests) / float64(analysis.TotalTests) * 100
		analysis.FailureRate = float64(analysis.FailedTests) / float64(analysis.TotalTests) * 100
		analysis.AverageDuration = totalDuration / time.Duration(analysis.TotalTests)
	}

	// Extract failure patterns
	analysis.Patterns = utils.ExtractFailurePatterns(results)

	// Generate insights
	analysis.Insights = a.generateInsights(analysis, results)

	// Save results for historical analysis
	if err := a.SaveTestResults(results); err != nil {
		// Log error but don't fail the analysis
		fmt.Printf("Warning: failed to save test results: %v\n", err)
	}

	// Track failure patterns
	for _, pattern := range analysis.Patterns {
		if err := a.TrackFailurePattern(pattern); err != nil {
			fmt.Printf("Warning: failed to track failure pattern: %v\n", err)
		}
	}

	return analysis, nil
}

// FindSimilarFailures finds similar historical failures
func (a *Analyzer) FindSimilarFailures(testResult types.TestResult, limit int) ([]types.TestResult, error) {
	if testResult.Status != types.TestStatusFailed {
		return nil, fmt.Errorf("test did not fail")
	}

	// Load historical results
	historicalFile := filepath.Join(a.dataDir, "test_history.json")
	var historicalResults []types.TestResult

	if err := utils.LoadFromJSON(historicalFile, &historicalResults); err != nil {
		// No historical data available
		return []types.TestResult{}, nil
	}

	// Find similar failures
	var similarFailures []struct {
		result     types.TestResult
		similarity float64
	}

	for _, historical := range historicalResults {
		if historical.Status != types.TestStatusFailed {
			continue
		}

		similarity := a.calculateSimilarity(testResult, historical)
		if similarity > 0.3 { // Minimum 30% similarity threshold
			similarFailures = append(similarFailures, struct {
				result     types.TestResult
				similarity float64
			}{historical, similarity})
		}
	}

	// Sort by similarity (highest first)
	sort.Slice(similarFailures, func(i, j int) bool {
		return similarFailures[i].similarity > similarFailures[j].similarity
	})

	// Return top N similar failures
	var results []types.TestResult
	for i := 0; i < len(similarFailures) && i < limit; i++ {
		results = append(results, similarFailures[i].result)
	}

	return results, nil
}

// calculateSimilarity calculates similarity between two test failures
func (a *Analyzer) calculateSimilarity(test1, test2 types.TestResult) float64 {
	var score float64
	var factors int

	// Check test name similarity
	if test1.SpecName == test2.SpecName {
		score += 0.4
	} else if strings.Contains(test1.SpecName, test2.SpecName) || strings.Contains(test2.SpecName, test1.SpecName) {
		score += 0.2
	}
	factors++

	// Check error message similarity
	if test1.Error != "" && test2.Error != "" {
		errorSimilarity := a.stringJaccardSimilarity(test1.Error, test2.Error)
		score += errorSimilarity * 0.3
		factors++
	}

	// Check failure message similarity
	if test1.FailureMessage != "" && test2.FailureMessage != "" {
		failureSimilarity := a.stringJaccardSimilarity(test1.FailureMessage, test2.FailureMessage)
		score += failureSimilarity * 0.3
		factors++
	}

	// Check file location similarity
	if test1.FileName != "" && test2.FileName != "" && test1.FileName == test2.FileName {
		score += 0.1
		factors++
	}

	return score
}

// stringJaccardSimilarity calculates Jaccard similarity between two strings
func (a *Analyzer) stringJaccardSimilarity(s1, s2 string) float64 {
	words1 := strings.Fields(strings.ToLower(s1))
	words2 := strings.Fields(strings.ToLower(s2))

	set1 := make(map[string]bool)
	set2 := make(map[string]bool)

	for _, word := range words1 {
		set1[word] = true
	}
	for _, word := range words2 {
		set2[word] = true
	}

	intersection := 0
	for word := range set1 {
		if set2[word] {
			intersection++
		}
	}

	union := len(set1) + len(set2) - intersection

	if union == 0 {
		return 0
	}

	return float64(intersection) / float64(union)
}

// GenerateDebuggingPrompt generates an AI-friendly debugging prompt
func (a *Analyzer) GenerateDebuggingPrompt(testResult types.TestResult, similarFailures []types.TestResult) (string, error) {
	var prompt strings.Builder

	prompt.WriteString("# Ginkgo Test Failure Debugging\n\n")

	// Test Information
	prompt.WriteString("## Failed Test\n")
	prompt.WriteString(fmt.Sprintf("**Spec Name:** %s\n", testResult.SpecName))
	if testResult.ContainerName != "" {
		prompt.WriteString(fmt.Sprintf("**Container:** %s\n", testResult.ContainerName))
	}
	prompt.WriteString(fmt.Sprintf("**Status:** %s\n", testResult.Status))
	prompt.WriteString(fmt.Sprintf("**Duration:** %s\n", testResult.Duration))

	if testResult.FileName != "" {
		prompt.WriteString(fmt.Sprintf("**Location:** %s:%d\n", testResult.FileName, testResult.LineNumber))
	}

	prompt.WriteString("\n## Failure Details\n")
	if testResult.Error != "" {
		prompt.WriteString(fmt.Sprintf("**Error:** %s\n", testResult.Error))
	}
	if testResult.FailureMessage != "" {
		prompt.WriteString(fmt.Sprintf("**Failure Message:**\n```\n%s\n```\n", testResult.FailureMessage))
	}

	// Output
	if testResult.Output != "" {
		prompt.WriteString("\n## Test Output\n")
		prompt.WriteString(fmt.Sprintf("```\n%s\n```\n", testResult.Output))
	}

	// Similar Failures
	if len(similarFailures) > 0 {
		prompt.WriteString("\n## Similar Historical Failures\n")
		prompt.WriteString(fmt.Sprintf("Found %d similar failures in history:\n\n", len(similarFailures)))

		for i, similar := range similarFailures {
			if i >= 3 { // Limit to top 3 similar failures
				break
			}
			prompt.WriteString(fmt.Sprintf("%d. **%s** (failed at %s)\n", i+1, similar.SpecName, similar.Timestamp.Format("2006-01-02 15:04:05")))
			if similar.FailureMessage != "" {
				prompt.WriteString(fmt.Sprintf("   - %s\n", truncateString(similar.FailureMessage, 100)))
			}
		}
	}

	// Analysis Suggestions
	prompt.WriteString("\n## Debugging Suggestions\n")
	suggestions := a.generateDebuggingSuggestions(testResult, similarFailures)
	for i, suggestion := range suggestions {
		prompt.WriteString(fmt.Sprintf("%d. %s\n", i+1, suggestion))
	}

	// Request for AI assistance
	prompt.WriteString("\n## Analysis Request\n")
	prompt.WriteString("Please analyze this Ginkgo test failure and provide:\n")
	prompt.WriteString("1. Root cause analysis of the failure\n")
	prompt.WriteString("2. Specific steps to fix the issue\n")
	prompt.WriteString("3. Best practices to prevent similar failures\n")
	prompt.WriteString("4. Code examples if applicable\n")

	return prompt.String(), nil
}

// generateDebuggingSuggestions generates debugging suggestions based on failure type
func (a *Analyzer) generateDebuggingSuggestions(testResult types.TestResult, similarFailures []types.TestResult) []string {
	var suggestions []string

	errorText := strings.ToLower(testResult.Error + " " + testResult.FailureMessage)

	// Check for common patterns
	if strings.Contains(errorText, "nil") || strings.Contains(errorText, "pointer") {
		suggestions = append(suggestions, "Check for nil pointer dereferences and ensure all objects are properly initialized")
	}

	if strings.Contains(errorText, "timeout") {
		suggestions = append(suggestions, "Increase timeout duration or optimize slow operations")
		suggestions = append(suggestions, "Check for potential deadlocks or blocking operations")
	}

	if strings.Contains(errorText, "panic") {
		suggestions = append(suggestions, "Review the panic stack trace to identify the source")
		suggestions = append(suggestions, "Add proper error handling and recovery mechanisms")
	}

	if strings.Contains(errorText, "expected") || strings.Contains(errorText, "to equal") {
		suggestions = append(suggestions, "Review the expected vs actual values in the assertion")
		suggestions = append(suggestions, "Verify the test expectations are correct")
		suggestions = append(suggestions, "Check if the function logic matches the test requirements")
	}

	if strings.Contains(errorText, "connection") || strings.Contains(errorText, "network") {
		suggestions = append(suggestions, "Verify network connectivity and service availability")
		suggestions = append(suggestions, "Check if required services are running")
	}

	if strings.Contains(errorText, "file") || strings.Contains(errorText, "directory") {
		suggestions = append(suggestions, "Verify file paths and permissions")
		suggestions = append(suggestions, "Ensure required files exist before the test runs")
	}

	// Add suggestions from similar failures
	if len(similarFailures) > 0 {
		suggestions = append(suggestions, "Review similar historical failures for potential patterns")
	}

	// Generic suggestions
	if len(suggestions) == 0 {
		suggestions = append(suggestions, "Review the test implementation and logic")
		suggestions = append(suggestions, "Check recent code changes that might have caused the failure")
		suggestions = append(suggestions, "Run the test in isolation to rule out test interdependencies")
	}

	return suggestions
}

// TrackFailurePattern tracks a failure pattern for historical analysis
func (a *Analyzer) TrackFailurePattern(pattern types.FailurePattern) error {
	patternsFile := filepath.Join(a.dataDir, "failure_patterns.json")

	var patterns []types.FailurePattern

	// Load existing patterns
	if utils.FileExists(patternsFile) {
		if err := utils.LoadFromJSON(patternsFile, &patterns); err != nil {
			return fmt.Errorf("failed to load patterns: %w", err)
		}
	}

	// Update or add pattern
	found := false
	for i := range patterns {
		if patterns[i].ID == pattern.ID {
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

	// Save updated patterns
	return utils.SaveToJSON(patterns, patternsFile)
}

// GetFailurePatternStats retrieves failure pattern statistics
func (a *Analyzer) GetFailurePatternStats() ([]types.FailurePattern, error) {
	patternsFile := filepath.Join(a.dataDir, "failure_patterns.json")

	var patterns []types.FailurePattern

	if !utils.FileExists(patternsFile) {
		return []types.FailurePattern{}, nil
	}

	if err := utils.LoadFromJSON(patternsFile, &patterns); err != nil {
		return nil, fmt.Errorf("failed to load patterns: %w", err)
	}

	// Sort by count (most frequent first)
	sort.Slice(patterns, func(i, j int) bool {
		return patterns[i].Count > patterns[j].Count
	})

	return patterns, nil
}

// SaveTestResults saves test results to history
func (a *Analyzer) SaveTestResults(results []types.TestResult) error {
	historyFile := filepath.Join(a.dataDir, "test_history.json")

	var history []types.TestResult

	// Load existing history
	if utils.FileExists(historyFile) {
		if err := utils.LoadFromJSON(historyFile, &history); err != nil {
			// If load fails, start fresh
			history = []types.TestResult{}
		}
	}

	// Append new results
	history = append(history, results...)

	// Keep only last 1000 results to prevent unbounded growth
	if len(history) > 1000 {
		history = history[len(history)-1000:]
	}

	// Save updated history
	return utils.SaveToJSON(history, historyFile)
}

// GenerateTestReport generates a comprehensive test report
func (a *Analyzer) GenerateTestReport(analysis *TestAnalysis, outputPath string) error {
	// Ensure output directory exists
	if err := utils.EnsureDir(filepath.Dir(outputPath)); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Create report structure
	report := map[string]interface{}{
		"timestamp":        analysis.Timestamp,
		"total_tests":      analysis.TotalTests,
		"passed_tests":     analysis.PassedTests,
		"failed_tests":     analysis.FailedTests,
		"skipped_tests":    analysis.SkippedTests,
		"pending_tests":    analysis.PendingTests,
		"success_rate":     fmt.Sprintf("%.2f%%", analysis.SuccessRate),
		"failure_rate":     fmt.Sprintf("%.2f%%", analysis.FailureRate),
		"average_duration": analysis.AverageDuration.String(),
		"patterns":         analysis.Patterns,
		"insights":         analysis.Insights,
	}

	// Save as JSON
	reportData, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal report: %w", err)
	}

	if err := os.WriteFile(outputPath, reportData, 0644); err != nil {
		return fmt.Errorf("failed to write report: %w", err)
	}

	return nil
}

// generateInsights generates insights from test analysis
func (a *Analyzer) generateInsights(analysis *TestAnalysis, results []types.TestResult) []string {
	var insights []string

	// Success rate insights
	if analysis.SuccessRate == 100 {
		insights = append(insights, "✓ All tests passed successfully")
	} else if analysis.SuccessRate >= 90 {
		insights = append(insights, "⚠ High success rate but some failures detected")
	} else if analysis.SuccessRate >= 70 {
		insights = append(insights, "⚠ Moderate success rate - multiple failures need attention")
	} else {
		insights = append(insights, "✗ Low success rate - significant issues detected")
	}

	// Duration insights
	if analysis.AverageDuration > 5*time.Second {
		insights = append(insights, "⚠ Tests are running slowly - consider optimization")
	}

	// Pending tests insight
	if analysis.PendingTests > 0 {
		insights = append(insights, fmt.Sprintf("⚠ %d pending tests need implementation", analysis.PendingTests))
	}

	// Failure pattern insights
	if len(analysis.Patterns) > 0 {
		insights = append(insights, fmt.Sprintf("Found %d distinct failure patterns", len(analysis.Patterns)))
	}

	// Specific failure insights
	var panicCount int
	for _, result := range results {
		if result.Status == types.TestStatusPanic {
			panicCount++
		}
	}

	if panicCount > 0 {
		insights = append(insights, fmt.Sprintf("✗ Critical: %d tests panicked - immediate attention required", panicCount))
	}

	return insights
}

// truncateString truncates a string to the specified length
func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}