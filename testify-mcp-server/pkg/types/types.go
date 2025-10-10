package types

import (
	"time"
)

type TestResult struct {
	PackageName   string            `json:"package_name"`
	TestName      string            `json:"test_name"`
	FunctionName  string            `json:"function_name"`
	Status        TestStatus        `json:"status"`
	Duration      time.Duration     `json:"duration"`
	Error         string            `json:"error,omitempty"`
	Output        string            `json:"output,omitempty"`
	Coverage      *CoverageInfo     `json:"coverage,omitempty"`
	Timestamp     time.Time         `json:"timestamp"`
	Tags          []string          `json:"tags,omitempty"`
	Metadata      map[string]string `json:"metadata,omitempty"`
}

type TestStatus string

const (
	TestStatusPassed  TestStatus = "passed"
	TestStatusFailed  TestStatus = "failed"
	TestStatusSkipped TestStatus = "skipped"
	TestStatusPanic   TestStatus = "panic"
)

type CoverageInfo struct {
	TotalStatements   int     `json:"total_statements"`
	CoveredStatements int     `json:"covered_statements"`
	Percentage        float64 `json:"percentage"`
	UncoveredLines    []int   `json:"uncovered_lines,omitempty"`
}

type TestSuite struct {
	Name         string       `json:"name"`
	Tests        []TestResult `json:"tests"`
	TotalTests   int          `json:"total_tests"`
	PassedTests  int          `json:"passed_tests"`
	FailedTests  int          `json:"failed_tests"`
	SkippedTests int          `json:"skipped_tests"`
	Duration     time.Duration `json:"duration"`
	Coverage     *CoverageInfo `json:"coverage,omitempty"`
	Timestamp    time.Time    `json:"timestamp"`
}

type FailurePattern struct {
	ID          string    `json:"id"`
	Pattern     string    `json:"pattern"`
	Description string    `json:"description"`
	Count       int       `json:"count"`
	LastSeen    time.Time `json:"last_seen"`
	Tests       []string  `json:"tests"`
	Suggestions []string  `json:"suggestions"`
}

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

type DebuggingStatus string

const (
	DebuggingStatusActive    DebuggingStatus = "active"
	DebuggingStatusResolved  DebuggingStatus = "resolved"
	DebuggingStatusAbandoned DebuggingStatus = "abandoned"
)

type DebuggingStep struct {
	ID          string                 `json:"id"`
	Description string                 `json:"description"`
	Action      string                 `json:"action"`
	Result      string                 `json:"result"`
	Timestamp   time.Time              `json:"timestamp"`
	Data        map[string]interface{} `json:"data,omitempty"`
}

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

type Param struct {
	Name string `json:"name"`
	Type string `json:"type"`
}

type GeneratedTest struct {
	FunctionName string `json:"function_name"`
	TestCode     string `json:"test_code"`
	TestCases    []TestCase `json:"test_cases"`
	Imports      []string   `json:"imports"`
}

type TestCase struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Inputs      map[string]interface{} `json:"inputs"`
	Expected    interface{}            `json:"expected"`
}

type BenchmarkResult struct {
	Name           string        `json:"name"`
	Iterations     int           `json:"iterations"`
	NsPerOp        int64         `json:"ns_per_op"`
	MemAllocsPerOp int64         `json:"mem_allocs_per_op"`
	MemBytesPerOp  int64         `json:"mem_bytes_per_op"`
	Timestamp      time.Time     `json:"timestamp"`
}