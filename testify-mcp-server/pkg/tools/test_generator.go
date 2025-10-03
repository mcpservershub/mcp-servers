package tools

import (
	"fmt"
	"go/ast"
	"path/filepath"
	"strings"

	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/types"
	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/utils"
)

type TestGenerator struct {
	workDir string
}

func NewTestGenerator(workDir string) *TestGenerator {
	return &TestGenerator{
		workDir: workDir,
	}
}

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

func (tg *TestGenerator) GenerateTest(function types.TestableFunction) (*types.GeneratedTest, error) {
	testCode, testCases, imports := tg.generateTestCode(function)

	generatedTest := &types.GeneratedTest{
		FunctionName: function.FunctionName,
		TestCode:     testCode,
		TestCases:    testCases,
		Imports:      imports,
	}

	return generatedTest, nil
}

func (tg *TestGenerator) GenerateTableDrivenTest(function types.TestableFunction) (*types.GeneratedTest, error) {
	testCode, testCases, imports := tg.generateTableDrivenTestCode(function)

	generatedTest := &types.GeneratedTest{
		FunctionName: function.FunctionName,
		TestCode:     testCode,
		TestCases:    testCases,
		Imports:      imports,
	}

	return generatedTest, nil
}

func (tg *TestGenerator) GenerateBenchmark(function types.TestableFunction) (string, error) {
	benchmarkCode := tg.generateBenchmarkCode(function)
	return benchmarkCode, nil
}

func (tg *TestGenerator) generateTestCode(function types.TestableFunction) (string, []types.TestCase, []string) {
	imports := []string{
		"testing",
		"github.com/stretchr/testify/assert",
		"github.com/stretchr/testify/require",
	}

	if function.PackageName != "main" {
		relPath, _ := filepath.Rel(tg.workDir, filepath.Dir(function.FilePath))
		imports = append(imports, relPath)
	}

	testCases := tg.generateTestCases(function)

	testCode := fmt.Sprintf(`func Test%s(t *testing.T) {
	tests := []struct {
		name     string
		%s
		want     %s
		wantErr  bool
	}{
%s
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			%s
		})
	}
}`, function.FunctionName,
		tg.generateTestStructFields(function),
		tg.getExpectedReturnType(function),
		tg.generateTestCaseData(testCases, function),
		tg.generateTestBody(function))

	return testCode, testCases, imports
}

func (tg *TestGenerator) generateTableDrivenTestCode(function types.TestableFunction) (string, []types.TestCase, []string) {
	imports := []string{
		"testing",
		"github.com/stretchr/testify/assert",
		"github.com/stretchr/testify/require",
	}

	testCases := tg.generateTestCases(function)

	testCode := fmt.Sprintf(`func Test%s_TableDriven(t *testing.T) {
	type args struct {
%s
	}
	tests := []struct {
		name     string
		args     args
		want     %s
		wantErr  bool
	}{
%s
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			%s
		})
	}
}`, function.FunctionName,
		tg.generateArgsStructFields(function),
		tg.getExpectedReturnType(function),
		tg.generateTableTestCaseData(testCases, function),
		tg.generateTableTestBody(function))

	return testCode, testCases, imports
}

func (tg *TestGenerator) generateBenchmarkCode(function types.TestableFunction) string {
	benchArgs := tg.generateBenchmarkArgs(function)

	benchmarkCode := fmt.Sprintf(`func Benchmark%s(b *testing.B) {
	%s

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		%s(%s)
	}
}`, function.FunctionName,
		tg.generateBenchmarkSetup(function),
		function.FunctionName,
		benchArgs)

	return benchmarkCode
}

func (tg *TestGenerator) generateTestCases(function types.TestableFunction) []types.TestCase {
	var testCases []types.TestCase

	testCases = append(testCases, types.TestCase{
		Name:        "valid input",
		Description: "Test with valid input parameters",
		Inputs:      tg.generateValidInputs(function),
		Expected:    tg.generateExpectedOutput(function),
	})

	if tg.hasErrorReturn(function) {
		testCases = append(testCases, types.TestCase{
			Name:        "error case",
			Description: "Test error handling",
			Inputs:      tg.generateErrorInputs(function),
			Expected:    "error",
		})
	}

	testCases = append(testCases, types.TestCase{
		Name:        "edge case",
		Description: "Test edge case scenarios",
		Inputs:      tg.generateEdgeCaseInputs(function),
		Expected:    tg.generateEdgeCaseOutput(function),
	})

	return testCases
}

func (tg *TestGenerator) generateTestStructFields(function types.TestableFunction) string {
	var fields []string

	for _, param := range function.Parameters {
		fields = append(fields, fmt.Sprintf("%s %s", param.Name, param.Type))
	}

	return strings.Join(fields, "\n\t\t")
}

func (tg *TestGenerator) generateArgsStructFields(function types.TestableFunction) string {
	var fields []string

	for _, param := range function.Parameters {
		fields = append(fields, fmt.Sprintf("\t\t%s %s", param.Name, param.Type))
	}

	return strings.Join(fields, "\n")
}

func (tg *TestGenerator) getExpectedReturnType(function types.TestableFunction) string {
	if len(function.ReturnTypes) == 0 {
		return "interface{}"
	}

	if len(function.ReturnTypes) == 1 {
		return function.ReturnTypes[0]
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

func (tg *TestGenerator) generateTestCaseData(testCases []types.TestCase, function types.TestableFunction) string {
	var caseData []string

	for _, testCase := range testCases {
		var paramValues []string
		for _, param := range function.Parameters {
			if value, exists := testCase.Inputs[param.Name]; exists {
				paramValues = append(paramValues, fmt.Sprintf("%s: %v", param.Name, value))
			} else {
				paramValues = append(paramValues, fmt.Sprintf("%s: %s", param.Name, tg.getZeroValue(param.Type)))
			}
		}

		caseStr := fmt.Sprintf(`		{
			name: "%s",
			%s,
			want: %v,
			wantErr: %t,
		}`, testCase.Name,
			strings.Join(paramValues, ",\n\t\t\t"),
			testCase.Expected,
			testCase.Expected == "error")

		caseData = append(caseData, caseStr)
	}

	return strings.Join(caseData, ",\n")
}

func (tg *TestGenerator) generateTableTestCaseData(testCases []types.TestCase, function types.TestableFunction) string {
	var caseData []string

	for _, testCase := range testCases {
		var paramValues []string
		for _, param := range function.Parameters {
			if value, exists := testCase.Inputs[param.Name]; exists {
				paramValues = append(paramValues, fmt.Sprintf("%s: %v", param.Name, value))
			} else {
				paramValues = append(paramValues, fmt.Sprintf("%s: %s", param.Name, tg.getZeroValue(param.Type)))
			}
		}

		caseStr := fmt.Sprintf(`		{
			name: "%s",
			args: args{
				%s,
			},
			want: %v,
			wantErr: %t,
		}`, testCase.Name,
			strings.Join(paramValues, ",\n\t\t\t\t"),
			testCase.Expected,
			testCase.Expected == "error")

		caseData = append(caseData, caseStr)
	}

	return strings.Join(caseData, ",\n")
}

func (tg *TestGenerator) generateTestBody(function types.TestableFunction) string {
	var paramNames []string
	for _, param := range function.Parameters {
		paramNames = append(paramNames, "tt."+param.Name)
	}

	if tg.hasErrorReturn(function) {
		if len(function.ReturnTypes) > 1 {
			return fmt.Sprintf(`got, err := %s(%s)
			if (err != nil) != tt.wantErr {
				t.Errorf("%s() error = %%v, wantErr %%v", err, tt.wantErr)
				return
			}
			if !assert.Equal(t, tt.want, got) {
				t.Errorf("%s() = %%v, want %%v", got, tt.want)
			}`, function.FunctionName, strings.Join(paramNames, ", "),
				function.FunctionName, function.FunctionName)
		} else {
			return fmt.Sprintf(`err := %s(%s)
			if (err != nil) != tt.wantErr {
				t.Errorf("%s() error = %%v, wantErr %%v", err, tt.wantErr)
			}`, function.FunctionName, strings.Join(paramNames, ", "), function.FunctionName)
		}
	} else {
		return fmt.Sprintf(`got := %s(%s)
			if !assert.Equal(t, tt.want, got) {
				t.Errorf("%s() = %%v, want %%v", got, tt.want)
			}`, function.FunctionName, strings.Join(paramNames, ", "), function.FunctionName)
	}
}

func (tg *TestGenerator) generateTableTestBody(function types.TestableFunction) string {
	var paramNames []string
	for _, param := range function.Parameters {
		paramNames = append(paramNames, "tt.args."+param.Name)
	}

	if tg.hasErrorReturn(function) {
		if len(function.ReturnTypes) > 1 {
			return fmt.Sprintf(`got, err := %s(%s)
			if (err != nil) != tt.wantErr {
				t.Errorf("%s() error = %%v, wantErr %%v", err, tt.wantErr)
				return
			}
			if !assert.Equal(t, tt.want, got) {
				t.Errorf("%s() = %%v, want %%v", got, tt.want)
			}`, function.FunctionName, strings.Join(paramNames, ", "),
				function.FunctionName, function.FunctionName)
		} else {
			return fmt.Sprintf(`err := %s(%s)
			if (err != nil) != tt.wantErr {
				t.Errorf("%s() error = %%v, wantErr %%v", err, tt.wantErr)
			}`, function.FunctionName, strings.Join(paramNames, ", "), function.FunctionName)
		}
	} else {
		return fmt.Sprintf(`got := %s(%s)
			if !assert.Equal(t, tt.want, got) {
				t.Errorf("%s() = %%v, want %%v", got, tt.want)
			}`, function.FunctionName, strings.Join(paramNames, ", "), function.FunctionName)
	}
}

func (tg *TestGenerator) generateBenchmarkArgs(function types.TestableFunction) string {
	var args []string
	for _, param := range function.Parameters {
		args = append(args, tg.getBenchmarkValue(param.Type))
	}
	return strings.Join(args, ", ")
}

func (tg *TestGenerator) generateBenchmarkSetup(function types.TestableFunction) string {
	var setup []string
	for _, param := range function.Parameters {
		if tg.needsSetup(param.Type) {
			setup = append(setup, fmt.Sprintf("%s := %s", param.Name, tg.getBenchmarkValue(param.Type)))
		}
	}
	return strings.Join(setup, "\n\t")
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

func (tg *TestGenerator) generateExpectedOutput(function types.TestableFunction) interface{} {
	if len(function.ReturnTypes) == 0 {
		return nil
	}

	nonErrorTypes := make([]string, 0, len(function.ReturnTypes))
	for _, returnType := range function.ReturnTypes {
		if returnType != "error" {
			nonErrorTypes = append(nonErrorTypes, returnType)
		}
	}

	if len(nonErrorTypes) == 0 {
		return nil
	}

	return tg.getValidValue(nonErrorTypes[0])
}

func (tg *TestGenerator) generateEdgeCaseOutput(function types.TestableFunction) interface{} {
	if len(function.ReturnTypes) == 0 {
		return nil
	}

	nonErrorTypes := make([]string, 0, len(function.ReturnTypes))
	for _, returnType := range function.ReturnTypes {
		if returnType != "error" {
			nonErrorTypes = append(nonErrorTypes, returnType)
		}
	}

	if len(nonErrorTypes) == 0 {
		return nil
	}

	return tg.getEdgeCaseValue(nonErrorTypes[0])
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
		if strings.HasPrefix(typeName, "[]") {
			return "nil"
		}
		if strings.HasPrefix(typeName, "map[") {
			return "nil"
		}
		if strings.HasPrefix(typeName, "*") {
			return "nil"
		}
		return "nil"
	}
}

func (tg *TestGenerator) getValidValue(typeName string) interface{} {
	switch typeName {
	case "string":
		return "test"
	case "int", "int8", "int16", "int32", "int64":
		return 42
	case "uint", "uint8", "uint16", "uint32", "uint64":
		return 42
	case "float32", "float64":
		return 3.14
	case "bool":
		return true
	default:
		return nil
	}
}

func (tg *TestGenerator) getErrorValue(typeName string) interface{} {
	switch typeName {
	case "string":
		return ""
	case "int", "int8", "int16", "int32", "int64":
		return -1
	case "uint", "uint8", "uint16", "uint32", "uint64":
		return 0
	case "float32", "float64":
		return -1.0
	case "bool":
		return false
	default:
		return nil
	}
}

func (tg *TestGenerator) getEdgeCaseValue(typeName string) interface{} {
	switch typeName {
	case "string":
		return "edge_case_string_with_special_chars!@#$%"
	case "int", "int8", "int16", "int32", "int64":
		return 0
	case "uint", "uint8", "uint16", "uint32", "uint64":
		return 0
	case "float32", "float64":
		return 0.0
	case "bool":
		return false
	default:
		return nil
	}
}

func (tg *TestGenerator) getBenchmarkValue(typeName string) string {
	switch typeName {
	case "string":
		return `"benchmark_string"`
	case "int", "int8", "int16", "int32", "int64":
		return "1000"
	case "uint", "uint8", "uint16", "uint32", "uint64":
		return "1000"
	case "float32", "float64":
		return "1000.0"
	case "bool":
		return "true"
	default:
		return "nil"
	}
}

func (tg *TestGenerator) needsSetup(typeName string) bool {
	return strings.HasPrefix(typeName, "[]") || strings.HasPrefix(typeName, "map[") || strings.HasPrefix(typeName, "*")
}

func (tg *TestGenerator) hasErrorReturn(function types.TestableFunction) bool {
	for _, returnType := range function.ReturnTypes {
		if returnType == "error" {
			return true
		}
	}
	return false
}

func (tg *TestGenerator) checkIfHasTests(function types.TestableFunction) bool {
	testFilePath := strings.Replace(function.FilePath, ".go", "_test.go", 1)

	file, _, err := utils.ParseGoFile(testFilePath)
	if err != nil {
		return false
	}

	expectedTestName := "Test" + function.FunctionName

	for _, decl := range file.Decls {
		if funcDecl, ok := decl.(*ast.FuncDecl); ok {
			if strings.HasPrefix(funcDecl.Name.Name, expectedTestName) {
				return true
			}
		}
	}

	return false
}

func (tg *TestGenerator) estimateTestCoverage(function types.TestableFunction) float64 {
	if !function.HasTests {
		return 0.0
	}

	baseCoverage := 70.0

	if function.Complexity > 5 {
		baseCoverage -= float64(function.Complexity-5) * 5.0
	}

	if baseCoverage < 0 {
		baseCoverage = 30.0
	}

	return baseCoverage
}