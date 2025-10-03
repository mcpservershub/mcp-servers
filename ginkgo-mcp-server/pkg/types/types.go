package types

import (
	"time"
)

// TestResult represents the result of a single Ginkgo test spec
type TestResult struct {
	SpecName      string            `json:"spec_name"`
	ContainerName string            `json:"container_name"`
	FullText      string            `json:"full_text"`
	Status        TestStatus        `json:"status"`
	Duration      time.Duration     `json:"duration"`
	Error         string            `json:"error,omitempty"`
	FailureMessage string           `json:"failure_message,omitempty"`
	FailureLocation string          `json:"failure_location,omitempty"`
	Output        string            `json:"output,omitempty"`
	Coverage      *CoverageInfo     `json:"coverage,omitempty"`
	Timestamp     time.Time         `json:"timestamp"`
	Tags          []string          `json:"tags,omitempty"`
	Metadata      map[string]string `json:"metadata,omitempty"`
	LineNumber    int               `json:"line_number,omitempty"`
	FileName      string            `json:"file_name,omitempty"`
}

// TestStatus represents the status of a test
type TestStatus string

const (
	TestStatusPassed  TestStatus = "passed"
	TestStatusFailed  TestStatus = "failed"
	TestStatusSkipped TestStatus = "skipped"
	TestStatusPending TestStatus = "pending"
	TestStatusPanic   TestStatus = "panic"
)

// CoverageInfo contains code coverage information
type CoverageInfo struct {
	TotalStatements   int     `json:"total_statements"`
	CoveredStatements int     `json:"covered_statements"`
	Percentage        float64 `json:"percentage"`
	UncoveredLines    []int   `json:"uncovered_lines,omitempty"`
}

// TestSuite represents a complete Ginkgo test suite
type TestSuite struct {
	Name         string        `json:"name"`
	Tests        []TestResult  `json:"tests"`
	TotalTests   int           `json:"total_tests"`
	PassedTests  int           `json:"passed_tests"`
	FailedTests  int           `json:"failed_tests"`
	SkippedTests int           `json:"skipped_tests"`
	PendingTests int           `json:"pending_tests"`
	Duration     time.Duration `json:"duration"`
	Coverage     *CoverageInfo `json:"coverage,omitempty"`
	Timestamp    time.Time     `json:"timestamp"`
}

// FailurePattern represents a pattern in test failures
type FailurePattern struct {
	ID          string    `json:"id"`
	Pattern     string    `json:"pattern"`
	Description string    `json:"description"`
	Count       int       `json:"count"`
	LastSeen    time.Time `json:"last_seen"`
	Tests       []string  `json:"tests"`
	Suggestions []string  `json:"suggestions"`
}

// DebuggingSession tracks a debugging session for a failing test
type DebuggingSession struct {
	ID           string            `json:"id"`
	TestName     string            `json:"test_name"`
	FailureType  string            `json:"failure_type"`
	StartTime    time.Time         `json:"start_time"`
	EndTime      *time.Time        `json:"end_time,omitempty"`
	Status       DebuggingStatus   `json:"status"`
	Steps        []DebuggingStep   `json:"steps"`
	Resolution   string            `json:"resolution,omitempty"`
	Metadata     map[string]string `json:"metadata,omitempty"`
}

// DebuggingStatus represents the status of a debugging session
type DebuggingStatus string

const (
	DebuggingStatusActive    DebuggingStatus = "active"
	DebuggingStatusResolved  DebuggingStatus = "resolved"
	DebuggingStatusAbandoned DebuggingStatus = "abandoned"
)

// DebuggingStep represents a single step in a debugging session
type DebuggingStep struct {
	ID          string                 `json:"id"`
	Description string                 `json:"description"`
	Action      string                 `json:"action"`
	Result      string                 `json:"result"`
	Timestamp   time.Time              `json:"timestamp"`
	Data        map[string]interface{} `json:"data,omitempty"`
}

// TestableFunction represents a function that can be tested with Ginkgo
type TestableFunction struct {
	PackageName   string   `json:"package_name"`
	FunctionName  string   `json:"function_name"`
	FilePath      string   `json:"file_path"`
	LineNumber    int      `json:"line_number"`
	Signature     string   `json:"signature"`
	Parameters    []Param  `json:"parameters"`
	ReturnTypes   []string `json:"return_types"`
	IsPublic      bool     `json:"is_public"`
	HasTests      bool     `json:"has_tests"`
	TestCoverage  float64  `json:"test_coverage"`
	Complexity    int      `json:"complexity"`
}

// Param represents a function parameter
type Param struct {
	Name string `json:"name"`
	Type string `json:"type"`
}

// GeneratedTest represents a generated Ginkgo test spec
type GeneratedTest struct {
	FunctionName string     `json:"function_name"`
	TestCode     string     `json:"test_code"`
	TestCases    []TestCase `json:"test_cases"`
	Imports      []string   `json:"imports"`
}

// TestCase represents a single test case scenario
type TestCase struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Inputs      map[string]interface{} `json:"inputs"`
	Expected    interface{}            `json:"expected"`
}

// BenchmarkResult represents Ginkgo benchmark results
type BenchmarkResult struct {
	Name           string        `json:"name"`
	Iterations     int           `json:"iterations"`
	NsPerOp        int64         `json:"ns_per_op"`
	MemAllocsPerOp int64         `json:"mem_allocs_per_op"`
	MemBytesPerOp  int64         `json:"mem_bytes_per_op"`
	Timestamp      time.Time     `json:"timestamp"`
}

// GinkgoSpec represents a Ginkgo test specification structure
type GinkgoSpec struct {
	Description string       `json:"description"`
	Contexts    []GinkgoContext `json:"contexts"`
	FilePath    string       `json:"file_path"`
	LineNumber  int          `json:"line_number"`
}

// GinkgoContext represents a Context or Describe block
type GinkgoContext struct {
	Type        string       `json:"type"` // "Describe" or "Context"
	Description string       `json:"description"`
	Specs       []string     `json:"specs"`
	SubContexts []GinkgoContext `json:"sub_contexts,omitempty"`
}