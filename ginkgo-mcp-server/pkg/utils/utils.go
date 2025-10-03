package utils

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/mcpservershub/mcpservers/ginkgo-mcp/pkg/types"
)

// GenerateID generates a unique ID from input string
func GenerateID(input string) string {
	hash := sha256.Sum256([]byte(input))
	return hex.EncodeToString(hash[:])[:16]
}

// ValidatePackagePath validates if the package path is valid
func ValidatePackagePath(path string) error {
	if path == "" {
		return fmt.Errorf("package path cannot be empty")
	}

	info, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return fmt.Errorf("package path does not exist: %s", path)
		}
		return fmt.Errorf("error accessing package path: %w", err)
	}

	if !info.IsDir() {
		return fmt.Errorf("package path is not a directory: %s", path)
	}

	return nil
}

// FindGoFiles finds all Go files (excluding test files) in the given directory
func FindGoFiles(rootPath string) ([]string, error) {
	var goFiles []string

	err := filepath.Walk(rootPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && strings.HasSuffix(path, ".go") && !strings.HasSuffix(path, "_test.go") {
			goFiles = append(goFiles, path)
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("error walking directory: %w", err)
	}

	return goFiles, nil
}

// FindGinkgoTestFiles finds all Ginkgo test files in the given directory
func FindGinkgoTestFiles(rootPath string) ([]string, error) {
	var testFiles []string

	err := filepath.Walk(rootPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && strings.HasSuffix(path, "_test.go") {
			// Check if it's a Ginkgo test by looking for RunSpecs
			content, readErr := ioutil.ReadFile(path)
			if readErr == nil && strings.Contains(string(content), "RunSpecs") {
				testFiles = append(testFiles, path)
			}
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("error walking directory: %w", err)
	}

	return testFiles, nil
}

// ParseGoFile parses a Go source file and returns the AST
func ParseGoFile(filePath string) (*ast.File, *token.FileSet, error) {
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, filePath, nil, parser.ParseComments)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return file, fset, nil
}

// ExtractFunctions extracts all functions from a Go AST
func ExtractFunctions(file *ast.File, fset *token.FileSet, filePath string) []types.TestableFunction {
	var functions []types.TestableFunction

	ast.Inspect(file, func(n ast.Node) bool {
		funcDecl, ok := n.(*ast.FuncDecl)
		if !ok {
			return true
		}

		// Skip methods (functions with receivers)
		if funcDecl.Recv != nil {
			return true
		}

		function := types.TestableFunction{
			PackageName:  file.Name.Name,
			FunctionName: funcDecl.Name.Name,
			FilePath:     filePath,
			LineNumber:   fset.Position(funcDecl.Pos()).Line,
			IsPublic:     ast.IsExported(funcDecl.Name.Name),
			Complexity:   calculateComplexity(funcDecl),
		}

		// Extract signature
		function.Signature = extractSignature(funcDecl)

		// Extract parameters
		if funcDecl.Type.Params != nil {
			for _, field := range funcDecl.Type.Params.List {
				paramType := extractTypeString(field.Type)
				if len(field.Names) > 0 {
					for _, name := range field.Names {
						function.Parameters = append(function.Parameters, types.Param{
							Name: name.Name,
							Type: paramType,
						})
					}
				} else {
					function.Parameters = append(function.Parameters, types.Param{
						Name: "_",
						Type: paramType,
					})
				}
			}
		}

		// Extract return types
		if funcDecl.Type.Results != nil {
			for _, field := range funcDecl.Type.Results.List {
				returnType := extractTypeString(field.Type)
				function.ReturnTypes = append(function.ReturnTypes, returnType)
			}
		}

		functions = append(functions, function)
		return true
	})

	return functions
}

// extractSignature extracts the function signature as a string
func extractSignature(funcDecl *ast.FuncDecl) string {
	var params []string
	if funcDecl.Type.Params != nil {
		for _, field := range funcDecl.Type.Params.List {
			paramType := extractTypeString(field.Type)
			if len(field.Names) > 0 {
				for _, name := range field.Names {
					params = append(params, fmt.Sprintf("%s %s", name.Name, paramType))
				}
			} else {
				params = append(params, paramType)
			}
		}
	}

	var returns []string
	if funcDecl.Type.Results != nil {
		for _, field := range funcDecl.Type.Results.List {
			returns = append(returns, extractTypeString(field.Type))
		}
	}

	signature := fmt.Sprintf("func %s(%s)", funcDecl.Name.Name, strings.Join(params, ", "))
	if len(returns) > 0 {
		if len(returns) == 1 {
			signature += " " + returns[0]
		} else {
			signature += " (" + strings.Join(returns, ", ") + ")"
		}
	}

	return signature
}

// extractTypeString extracts the type as a string from an AST expression
func extractTypeString(expr ast.Expr) string {
	switch t := expr.(type) {
	case *ast.Ident:
		return t.Name
	case *ast.StarExpr:
		return "*" + extractTypeString(t.X)
	case *ast.ArrayType:
		if t.Len == nil {
			return "[]" + extractTypeString(t.Elt)
		}
		return "[" + extractTypeString(t.Len) + "]" + extractTypeString(t.Elt)
	case *ast.MapType:
		return "map[" + extractTypeString(t.Key) + "]" + extractTypeString(t.Value)
	case *ast.SelectorExpr:
		return extractTypeString(t.X) + "." + t.Sel.Name
	case *ast.InterfaceType:
		if t.Methods == nil || len(t.Methods.List) == 0 {
			return "interface{}"
		}
		return "interface{...}"
	case *ast.FuncType:
		return "func(...)"
	case *ast.ChanType:
		return "chan " + extractTypeString(t.Value)
	default:
		return "unknown"
	}
}

// calculateComplexity calculates cyclomatic complexity of a function
func calculateComplexity(funcDecl *ast.FuncDecl) int {
	complexity := 1

	ast.Inspect(funcDecl, func(n ast.Node) bool {
		switch n.(type) {
		case *ast.IfStmt, *ast.ForStmt, *ast.RangeStmt, *ast.CaseClause, *ast.CommClause:
			complexity++
		case *ast.BinaryExpr:
			if expr, ok := n.(*ast.BinaryExpr); ok {
				if expr.Op == token.LAND || expr.Op == token.LOR {
					complexity++
				}
			}
		}
		return true
	})

	return complexity
}

// ExtractFailurePatterns extracts common patterns from test failures
func ExtractFailurePatterns(testResults []types.TestResult) []types.FailurePattern {
	patternMap := make(map[string]*types.FailurePattern)

	for _, result := range testResults {
		if result.Status != types.TestStatusFailed {
			continue
		}

		// Extract error patterns
		patterns := identifyErrorPatterns(result.Error, result.FailureMessage)

		for _, pattern := range patterns {
			patternID := GenerateID(pattern)

			if existing, found := patternMap[patternID]; found {
				existing.Count++
				existing.LastSeen = result.Timestamp
				existing.Tests = append(existing.Tests, result.SpecName)
			} else {
				patternMap[patternID] = &types.FailurePattern{
					ID:          patternID,
					Pattern:     pattern,
					Description: generatePatternDescription(pattern),
					Count:       1,
					LastSeen:    result.Timestamp,
					Tests:       []string{result.SpecName},
					Suggestions: generateSuggestions(pattern),
				}
			}
		}
	}

	var patterns []types.FailurePattern
	for _, p := range patternMap {
		patterns = append(patterns, *p)
	}

	return patterns
}

// identifyErrorPatterns identifies common error patterns
func identifyErrorPatterns(errorMsg, failureMsg string) []string {
	var patterns []string
	combined := errorMsg + " " + failureMsg

	commonPatterns := []string{
		`panic: runtime error:.*`,
		`nil pointer dereference`,
		`index out of range`,
		`Expected.*to equal.*`,
		`Expected.*to be nil`,
		`timeout`,
		`connection refused`,
		`no such file or directory`,
		`permission denied`,
		`unexpected EOF`,
	}

	for _, pattern := range commonPatterns {
		re := regexp.MustCompile(pattern)
		if re.MatchString(combined) {
			patterns = append(patterns, pattern)
		}
	}

	if len(patterns) == 0 {
		patterns = append(patterns, "generic_failure")
	}

	return patterns
}

// generatePatternDescription generates a human-readable description for a pattern
func generatePatternDescription(pattern string) string {
	descriptions := map[string]string{
		`panic: runtime error:.*`:    "Runtime panic error",
		`nil pointer dereference`:    "Attempted to dereference a nil pointer",
		`index out of range`:         "Array or slice index out of bounds",
		`Expected.*to equal.*`:       "Assertion failure: values not equal",
		`Expected.*to be nil`:        "Assertion failure: expected nil value",
		`timeout`:                    "Operation timed out",
		`connection refused`:         "Network connection was refused",
		`no such file or directory`:  "File or directory not found",
		`permission denied`:          "Insufficient permissions to access resource",
		`unexpected EOF`:             "Unexpected end of file or stream",
		`generic_failure`:            "General test failure",
	}

	if desc, found := descriptions[pattern]; found {
		return desc
	}

	return "Unknown failure pattern"
}

// generateSuggestions generates debugging suggestions for a pattern
func generateSuggestions(pattern string) []string {
	suggestions := map[string][]string{
		`panic: runtime error:.*`: {
			"Check for nil pointer dereferences",
			"Verify array/slice bounds",
			"Review type assertions",
		},
		`nil pointer dereference`: {
			"Initialize all pointers before use",
			"Add nil checks before dereferencing",
			"Use safe navigation patterns",
		},
		`index out of range`: {
			"Validate array/slice lengths before access",
			"Add boundary checks",
			"Review loop conditions",
		},
		`Expected.*to equal.*`: {
			"Review the expected vs actual values",
			"Check calculation logic",
			"Verify test expectations",
		},
		`timeout`: {
			"Increase timeout duration",
			"Optimize slow operations",
			"Check for deadlocks",
		},
		`connection refused`: {
			"Verify service is running",
			"Check network configuration",
			"Validate connection parameters",
		},
		`generic_failure`: {
			"Review test implementation",
			"Check logs for details",
			"Debug the failing scenario",
		},
	}

	if sugg, found := suggestions[pattern]; found {
		return sugg
	}

	return []string{"Review the test failure details", "Check the implementation logic"}
}

// SaveToJSON saves data to a JSON file
func SaveToJSON(data interface{}, filename string) error {
	// Ensure directory exists
	dir := filepath.Dir(filename)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	if err := ioutil.WriteFile(filename, jsonData, 0644); err != nil {
		return fmt.Errorf("failed to write JSON file: %w", err)
	}

	return nil
}

// LoadFromJSON loads data from a JSON file
func LoadFromJSON(filename string, data interface{}) error {
	jsonData, err := ioutil.ReadFile(filename)
	if err != nil {
		if os.IsNotExist(err) {
			return fmt.Errorf("file does not exist: %s", filename)
		}
		return fmt.Errorf("failed to read JSON file: %w", err)
	}

	if err := json.Unmarshal(jsonData, data); err != nil {
		return fmt.Errorf("failed to unmarshal JSON: %w", err)
	}

	return nil
}

// FileExists checks if a file exists
func FileExists(path string) bool {
	_, err := os.Stat(path)
	return !os.IsNotExist(err)
}

// EnsureDir ensures a directory exists
func EnsureDir(path string) error {
	return os.MkdirAll(path, 0755)
}