package tools

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/mcpservershub/mcpservers/ginkgo-mcp/pkg/types"
	"github.com/mcpservershub/mcpservers/ginkgo-mcp/pkg/utils"
)

// TestGenerator generates Ginkgo test specs
type TestGenerator struct {
	workDir string
}

// NewTestGenerator creates a new test generator
func NewTestGenerator(workDir string) *TestGenerator {
	return &TestGenerator{
		workDir: workDir,
	}
}

// FindTestableFunctions finds functions that can be tested with Ginkgo
func (tg *TestGenerator) FindTestableFunctions(packagePath string) ([]types.TestableFunction, error) {
	if err := utils.ValidatePackagePath(packagePath); err != nil {
		return nil, fmt.Errorf("invalid package path: %w", err)
	}

	goFiles, err := utils.FindGoFiles(packagePath)
	if err != nil {
		return nil, fmt.Errorf("failed to find Go files: %w", err)
	}

	var allFunctions []types.TestableFunction

	for _, filePath := range goFiles {
		file, fset, err := utils.ParseGoFile(filePath)
		if err != nil {
			continue
		}

		functions := utils.ExtractFunctions(file, fset, filePath)
		for i := range functions {
			functions[i].HasTests = tg.checkIfHasTests(functions[i])
			functions[i].TestCoverage = tg.estimateTestCoverage(functions[i])
		}

		allFunctions = append(allFunctions, functions...)
	}

	return allFunctions, nil
}

// GenerateTest generates a basic Ginkgo test spec
func (tg *TestGenerator) GenerateTest(function types.TestableFunction) (*types.GeneratedTest, error) {
	testCode, testCases, imports := tg.generateGinkgoSpec(function)

	generatedTest := &types.GeneratedTest{
		FunctionName: function.FunctionName,
		TestCode:     testCode,
		TestCases:    testCases,
		Imports:      imports,
	}

	return generatedTest, nil
}

// GenerateTableDrivenTest generates a table-driven Ginkgo test using DescribeTable
func (tg *TestGenerator) GenerateTableDrivenTest(function types.TestableFunction) (*types.GeneratedTest, error) {
	testCode, testCases, imports := tg.generateTableDrivenSpec(function)

	generatedTest := &types.GeneratedTest{
		FunctionName: function.FunctionName,
		TestCode:     testCode,
		TestCases:    testCases,
		Imports:      imports,
	}

	return generatedTest, nil
}

// GenerateSuite generates a complete Ginkgo test suite file
func (tg *TestGenerator) GenerateSuite(packageName string, functions []types.TestableFunction) (string, error) {
	var builder strings.Builder

	// Package declaration
	builder.WriteString(fmt.Sprintf("package %s_test\n\n", packageName))

	// Imports
	builder.WriteString("import (\n")
	builder.WriteString("\t\"testing\"\n\n")
	builder.WriteString("\t. \"github.com/onsi/ginkgo/v2\"\n")
	builder.WriteString("\t. \"github.com/onsi/gomega\"\n")
	builder.WriteString(")\n\n")

	// Test runner
	builder.WriteString(fmt.Sprintf("func Test%s(t *testing.T) {\n", capitalize(packageName)))
	builder.WriteString("\tRegisterFailHandler(Fail)\n")
	builder.WriteString(fmt.Sprintf("\tRunSpecs(t, \"%s Suite\")\n", capitalize(packageName)))
	builder.WriteString("}\n\n")

	// Generate specs for each function
	for _, fn := range functions {
		if !fn.HasTests {
			spec, _, _ := tg.generateGinkgoSpec(fn)
			builder.WriteString(spec)
			builder.WriteString("\n\n")
		}
	}

	return builder.String(), nil
}

// generateGinkgoSpec generates a Ginkgo spec for a function
func (tg *TestGenerator) generateGinkgoSpec(function types.TestableFunction) (string, []types.TestCase, []string) {
	imports := []string{
		"testing",
		"github.com/onsi/ginkgo/v2",
		"github.com/onsi/gomega",
	}

	if function.PackageName != "main" {
		relPath, _ := filepath.Rel(tg.workDir, filepath.Dir(function.FilePath))
		imports = append(imports, relPath)
	}

	testCases := tg.generateTestCases(function)

	var spec strings.Builder

	spec.WriteString(fmt.Sprintf("var _ = Describe(\"%s\", func() {\n", function.FunctionName))

	// Generate test cases
	for _, testCase := range testCases {
		spec.WriteString(fmt.Sprintf("\tContext(\"%s\", func() {\n", testCase.Name))
		spec.WriteString(fmt.Sprintf("\t\tIt(\"%s\", func() {\n", testCase.Description))

		// Generate test body
		spec.WriteString(tg.generateSpecBody(function, testCase))

		spec.WriteString("\t\t})\n")
		spec.WriteString("\t})\n\n")
	}

	spec.WriteString("})")

	return spec.String(), testCases, imports
}

// generateTableDrivenSpec generates a table-driven Ginkgo spec
func (tg *TestGenerator) generateTableDrivenSpec(function types.TestableFunction) (string, []types.TestCase, []string) {
	imports := []string{
		"testing",
		"github.com/onsi/ginkgo/v2",
		"github.com/onsi/gomega",
	}

	testCases := tg.generateTestCases(function)

	var spec strings.Builder

	spec.WriteString(fmt.Sprintf("var _ = DescribeTable(\"%s\",\n", function.FunctionName))
	spec.WriteString("\tfunc(")

	// Generate parameters
	var params []string
	for _, param := range function.Parameters {
		params = append(params, fmt.Sprintf("%s %s", param.Name, param.Type))
	}
	if tg.hasErrorReturn(function) {
		params = append(params, "shouldError bool")
	}
	params = append(params, fmt.Sprintf("expected %s", tg.getExpectedReturnType(function)))

	spec.WriteString(strings.Join(params, ", "))
	spec.WriteString(") {\n")

	// Generate function call
	spec.WriteString(tg.generateTableFunctionCall(function))

	spec.WriteString("\t},\n\n")

	// Generate table entries
	for _, testCase := range testCases {
		spec.WriteString(tg.generateTableEntry(function, testCase))
	}

	spec.WriteString(")")

	return spec.String(), testCases, imports
}

// generateSpecBody generates the body of a Ginkgo spec
func (tg *TestGenerator) generateSpecBody(function types.TestableFunction, testCase types.TestCase) string {
	var body strings.Builder

	// Arrange
	body.WriteString("\t\t\t// Arrange\n")
	for _, param := range function.Parameters {
		if value, exists := testCase.Inputs[param.Name]; exists {
			body.WriteString(fmt.Sprintf("\t\t\t%s := %v\n", param.Name, formatValue(value)))
		}
	}
	body.WriteString("\n")

	// Act
	body.WriteString("\t\t\t// Act\n")
	var paramNames []string
	for _, param := range function.Parameters {
		paramNames = append(paramNames, param.Name)
	}

	if len(function.ReturnTypes) > 0 {
		if tg.hasErrorReturn(function) {
			body.WriteString(fmt.Sprintf("\t\t\tresult, err := %s(%s)\n\n", function.FunctionName, strings.Join(paramNames, ", ")))
		} else {
			body.WriteString(fmt.Sprintf("\t\t\tresult := %s(%s)\n\n", function.FunctionName, strings.Join(paramNames, ", ")))
		}
	} else {
		body.WriteString(fmt.Sprintf("\t\t\t%s(%s)\n\n", function.FunctionName, strings.Join(paramNames, ", ")))
	}

	// Assert
	body.WriteString("\t\t\t// Assert\n")
	if tg.hasErrorReturn(function) {
		if testCase.Expected == "error" {
			body.WriteString("\t\t\tExpect(err).To(HaveOccurred())\n")
		} else {
			body.WriteString("\t\t\tExpect(err).ToNot(HaveOccurred())\n")
			if len(function.ReturnTypes) > 1 {
				body.WriteString(fmt.Sprintf("\t\t\tExpect(result).To(Equal(%v))\n", formatValue(testCase.Expected)))
			}
		}
	} else if len(function.ReturnTypes) > 0 {
		body.WriteString(fmt.Sprintf("\t\t\tExpect(result).To(Equal(%v))\n", formatValue(testCase.Expected)))
	}

	return body.String()
}

// generateTableFunctionCall generates the function call for table-driven tests
func (tg *TestGenerator) generateTableFunctionCall(function types.TestableFunction) string {
	var body strings.Builder

	var paramNames []string
	for _, param := range function.Parameters {
		paramNames = append(paramNames, param.Name)
	}

	if tg.hasErrorReturn(function) {
		if len(function.ReturnTypes) > 1 {
			body.WriteString(fmt.Sprintf("\t\tresult, err := %s(%s)\n", function.FunctionName, strings.Join(paramNames, ", ")))
			body.WriteString("\t\tif shouldError {\n")
			body.WriteString("\t\t\tExpect(err).To(HaveOccurred())\n")
			body.WriteString("\t\t} else {\n")
			body.WriteString("\t\t\tExpect(err).ToNot(HaveOccurred())\n")
			body.WriteString("\t\t\tExpect(result).To(Equal(expected))\n")
			body.WriteString("\t\t}\n")
		} else {
			body.WriteString(fmt.Sprintf("\t\terr := %s(%s)\n", function.FunctionName, strings.Join(paramNames, ", ")))
			body.WriteString("\t\tif shouldError {\n")
			body.WriteString("\t\t\tExpect(err).To(HaveOccurred())\n")
			body.WriteString("\t\t} else {\n")
			body.WriteString("\t\t\tExpect(err).ToNot(HaveOccurred())\n")
			body.WriteString("\t\t}\n")
		}
	} else if len(function.ReturnTypes) > 0 {
		body.WriteString(fmt.Sprintf("\t\tresult := %s(%s)\n", function.FunctionName, strings.Join(paramNames, ", ")))
		body.WriteString("\t\tExpect(result).To(Equal(expected))\n")
	}

	return body.String()
}

// generateTableEntry generates a table entry for table-driven tests
func (tg *TestGenerator) generateTableEntry(function types.TestableFunction, testCase types.TestCase) string {
	var entry strings.Builder

	entry.WriteString(fmt.Sprintf("\tEntry(\"%s\",\n", testCase.Description))

	// Add parameter values
	for _, param := range function.Parameters {
		if value, exists := testCase.Inputs[param.Name]; exists {
			entry.WriteString(fmt.Sprintf("\t\t%v,\n", formatValue(value)))
		} else {
			entry.WriteString(fmt.Sprintf("\t\t%s,\n", tg.getZeroValue(param.Type)))
		}
	}

	// Add shouldError if applicable
	if tg.hasErrorReturn(function) {
		shouldError := testCase.Expected == "error"
		entry.WriteString(fmt.Sprintf("\t\t%t,\n", shouldError))
	}

	// Add expected value
	entry.WriteString(fmt.Sprintf("\t\t%v,\n", formatValue(testCase.Expected)))

	entry.WriteString("\t),\n\n")

	return entry.String()
}

// generateTestCases generates test cases for a function
func (tg *TestGenerator) generateTestCases(function types.TestableFunction) []types.TestCase {
	var testCases []types.TestCase

	// Valid input case
	testCases = append(testCases, types.TestCase{
		Name:        "with valid input",
		Description: "should return expected result with valid inputs",
		Inputs:      tg.generateValidInputs(function),
		Expected:    tg.generateExpectedOutput(function),
	})

	// Error case if function returns error
	if tg.hasErrorReturn(function) {
		testCases = append(testCases, types.TestCase{
			Name:        "with invalid input",
			Description: "should return error with invalid inputs",
			Inputs:      tg.generateErrorInputs(function),
			Expected:    "error",
		})
	}

	// Edge case
	testCases = append(testCases, types.TestCase{
		Name:        "with edge case",
		Description: "should handle edge cases correctly",
		Inputs:      tg.generateEdgeCaseInputs(function),
		Expected:    tg.generateEdgeCaseOutput(function),
	})

	// Nil/empty case for pointer/slice/map parameters
	if tg.hasNillableParams(function) {
		testCases = append(testCases, types.TestCase{
			Name:        "with nil/empty input",
			Description: "should handle nil or empty inputs gracefully",
			Inputs:      tg.generateNilInputs(function),
			Expected:    tg.generateNilCaseOutput(function),
		})
	}

	return testCases
}

// Helper methods

func (tg *TestGenerator) checkIfHasTests(function types.TestableFunction) bool {
	testDir := filepath.Dir(function.FilePath)
	testFiles, err := utils.FindGinkgoTestFiles(testDir)
	if err != nil || len(testFiles) == 0 {
		return false
	}

	// Check if any test file contains this function name
	for _, testFile := range testFiles {
		file, _, err := utils.ParseGoFile(testFile)
		if err != nil {
			continue
		}

		// Simple check: does the function name appear in the test file?
		if strings.Contains(fmt.Sprintf("%v", file), function.FunctionName) {
			return true
		}
	}

	return false
}

func (tg *TestGenerator) estimateTestCoverage(function types.TestableFunction) float64 {
	if !function.HasTests {
		return 0.0
	}
	// Estimate based on complexity
	baseCoverage := 70.0
	if function.Complexity > 5 {
		baseCoverage -= float64(function.Complexity-5) * 5.0
	}
	if baseCoverage < 30.0 {
		baseCoverage = 30.0
	}
	return baseCoverage
}

func (tg *TestGenerator) hasErrorReturn(function types.TestableFunction) bool {
	for _, returnType := range function.ReturnTypes {
		if returnType == "error" {
			return true
		}
	}
	return false
}

func (tg *TestGenerator) hasNillableParams(function types.TestableFunction) bool {
	for _, param := range function.Parameters {
		if strings.HasPrefix(param.Type, "*") ||
			strings.HasPrefix(param.Type, "[]") ||
			strings.HasPrefix(param.Type, "map[") {
			return true
		}
	}
	return false
}

func (tg *TestGenerator) getExpectedReturnType(function types.TestableFunction) string {
	if len(function.ReturnTypes) == 0 {
		return "interface{}"
	}

	nonErrorTypes := make([]string, 0, len(function.ReturnTypes))
	for _, returnType := range function.ReturnTypes {
		if returnType != "error" {
			nonErrorTypes = append(nonErrorTypes, returnType)
		}
	}

	if len(nonErrorTypes) == 0 {
		return "interface{}"
	}

	if len(nonErrorTypes) == 1 {
		return nonErrorTypes[0]
	}

	return fmt.Sprintf("(%s)", strings.Join(nonErrorTypes, ", "))
}

func (tg *TestGenerator) getZeroValue(typeName string) string {
	switch typeName {
	case "string":
		return `""`
	case "int", "int8", "int16", "int32", "int64":
		return "0"
	case "uint", "uint8", "uint16", "uint32", "uint64":
		return "0"
	case "float32", "float64":
		return "0.0"
	case "bool":
		return "false"
	case "[]byte":
		return "nil"
	default:
		if strings.HasPrefix(typeName, "[]") ||
			strings.HasPrefix(typeName, "map[") ||
			strings.HasPrefix(typeName, "*") {
			return "nil"
		}
		return "nil"
	}
}

func (tg *TestGenerator) generateValidInputs(function types.TestableFunction) map[string]interface{} {
	inputs := make(map[string]interface{})
	for _, param := range function.Parameters {
		inputs[param.Name] = tg.getValidValue(param.Type)
	}
	return inputs
}

func (tg *TestGenerator) generateErrorInputs(function types.TestableFunction) map[string]interface{} {
	inputs := make(map[string]interface{})
	for _, param := range function.Parameters {
		inputs[param.Name] = tg.getErrorValue(param.Type)
	}
	return inputs
}

func (tg *TestGenerator) generateEdgeCaseInputs(function types.TestableFunction) map[string]interface{} {
	inputs := make(map[string]interface{})
	for _, param := range function.Parameters {
		inputs[param.Name] = tg.getEdgeCaseValue(param.Type)
	}
	return inputs
}

func (tg *TestGenerator) generateNilInputs(function types.TestableFunction) map[string]interface{} {
	inputs := make(map[string]interface{})
	for _, param := range function.Parameters {
		if strings.HasPrefix(param.Type, "*") ||
			strings.HasPrefix(param.Type, "[]") ||
			strings.HasPrefix(param.Type, "map[") {
			inputs[param.Name] = nil
		} else {
			inputs[param.Name] = tg.getZeroValue(param.Type)
		}
	}
	return inputs
}

func (tg *TestGenerator) generateExpectedOutput(function types.TestableFunction) interface{} {
	if len(function.ReturnTypes) == 0 {
		return nil
	}
	for _, rt := range function.ReturnTypes {
		if rt != "error" {
			return tg.getValidValue(rt)
		}
	}
	return nil
}

func (tg *TestGenerator) generateEdgeCaseOutput(function types.TestableFunction) interface{} {
	if len(function.ReturnTypes) == 0 {
		return nil
	}
	for _, rt := range function.ReturnTypes {
		if rt != "error" {
			return tg.getEdgeCaseValue(rt)
		}
	}
	return nil
}

func (tg *TestGenerator) generateNilCaseOutput(function types.TestableFunction) interface{} {
	if tg.hasErrorReturn(function) {
		return "error"
	}
	return tg.getZeroValue(tg.getExpectedReturnType(function))
}

func (tg *TestGenerator) getValidValue(typeName string) interface{} {
	switch typeName {
	case "string":
		return "\"test\""
	case "int", "int8", "int16", "int32", "int64":
		return 42
	case "uint", "uint8", "uint16", "uint32", "uint64":
		return 42
	case "float32", "float64":
		return 3.14
	case "bool":
		return true
	default:
		return "nil"
	}
}

func (tg *TestGenerator) getErrorValue(typeName string) interface{} {
	switch typeName {
	case "string":
		return "\"\""
	case "int", "int8", "int16", "int32", "int64":
		return -1
	case "uint", "uint8", "uint16", "uint32", "uint64":
		return 0
	case "float32", "float64":
		return -1.0
	case "bool":
		return false
	default:
		return "nil"
	}
}

func (tg *TestGenerator) getEdgeCaseValue(typeName string) interface{} {
	switch typeName {
	case "string":
		return "\"edge_case_string!@#$%\""
	case "int", "int8", "int16", "int32", "int64":
		return 0
	case "uint", "uint8", "uint16", "uint32", "uint64":
		return 0
	case "float32", "float64":
		return 0.0
	case "bool":
		return false
	default:
		return "nil"
	}
}

// Helper functions

func capitalize(s string) string {
	if len(s) == 0 {
		return s
	}
	return strings.ToUpper(s[:1]) + s[1:]
}

func formatValue(value interface{}) string {
	switch v := value.(type) {
	case string:
		// Check if already quoted
		if strings.HasPrefix(v, "\"") && strings.HasSuffix(v, "\"") {
			return v
		}
		return fmt.Sprintf("\"%s\"", v)
	case nil:
		return "nil"
	default:
		return fmt.Sprintf("%v", v)
	}
}