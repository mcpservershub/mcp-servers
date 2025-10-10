package utils

import (
	"crypto/md5"
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/mcpservershub/mcpservers/testify-mcp/pkg/types"
)

func GenerateID(input string) string {
	hash := md5.Sum([]byte(input + time.Now().String()))
	return fmt.Sprintf("%x", hash)[:8]
}

func ValidatePackagePath(path string) error {
	if path == "" {
		return fmt.Errorf("package path cannot be empty")
	}

	absPath, err := filepath.Abs(path)
	if err != nil {
		return fmt.Errorf("invalid path: %w", err)
	}

	info, err := os.Stat(absPath)
	if err != nil {
		return fmt.Errorf("path does not exist: %w", err)
	}

	if !info.IsDir() {
		return fmt.Errorf("path is not a directory")
	}

	return nil
}

func FindGoFiles(rootPath string) ([]string, error) {
	var goFiles []string

	err := filepath.Walk(rootPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && strings.HasSuffix(info.Name(), ".go") && !strings.HasSuffix(info.Name(), "_test.go") {
			goFiles = append(goFiles, path)
		}

		return nil
	})

	return goFiles, err
}

func ParseGoFile(filePath string) (*ast.File, *token.FileSet, error) {
	fset := token.NewFileSet()

	src, err := os.ReadFile(filePath)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to read file %s: %w", filePath, err)
	}

	file, err := parser.ParseFile(fset, filePath, src, parser.ParseComments)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to parse file %s: %w", filePath, err)
	}

	return file, fset, nil
}

func ExtractFunctions(file *ast.File, fset *token.FileSet, filePath string) []types.TestableFunction {
	var functions []types.TestableFunction

	packageName := file.Name.Name

	for _, decl := range file.Decls {
		if funcDecl, ok := decl.(*ast.FuncDecl); ok {
			if funcDecl.Name.IsExported() && funcDecl.Recv == nil {
				function := types.TestableFunction{
					PackageName:  packageName,
					FunctionName: funcDecl.Name.Name,
					FilePath:     filePath,
					LineNumber:   fset.Position(funcDecl.Pos()).Line,
					IsPublic:     true,
					Signature:    extractFunctionSignature(funcDecl),
					Parameters:   extractParameters(funcDecl),
					ReturnTypes:  extractReturnTypes(funcDecl),
					Complexity:   calculateComplexity(funcDecl),
				}
				functions = append(functions, function)
			}
		}
	}

	return functions
}

func extractFunctionSignature(funcDecl *ast.FuncDecl) string {
	var params []string
	if funcDecl.Type.Params != nil {
		for _, param := range funcDecl.Type.Params.List {
			for _, name := range param.Names {
				paramType := getTypeString(param.Type)
				params = append(params, fmt.Sprintf("%s %s", name.Name, paramType))
			}
		}
	}

	var returns []string
	if funcDecl.Type.Results != nil {
		for _, result := range funcDecl.Type.Results.List {
			returns = append(returns, getTypeString(result.Type))
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

func extractParameters(funcDecl *ast.FuncDecl) []types.Param {
	var params []types.Param

	if funcDecl.Type.Params != nil {
		for _, param := range funcDecl.Type.Params.List {
			paramType := getTypeString(param.Type)
			for _, name := range param.Names {
				params = append(params, types.Param{
					Name: name.Name,
					Type: paramType,
				})
			}
		}
	}

	return params
}

func extractReturnTypes(funcDecl *ast.FuncDecl) []string {
	var returns []string

	if funcDecl.Type.Results != nil {
		for _, result := range funcDecl.Type.Results.List {
			returns = append(returns, getTypeString(result.Type))
		}
	}

	return returns
}

func getTypeString(expr ast.Expr) string {
	switch t := expr.(type) {
	case *ast.Ident:
		return t.Name
	case *ast.SelectorExpr:
		return getTypeString(t.X) + "." + t.Sel.Name
	case *ast.ArrayType:
		return "[]" + getTypeString(t.Elt)
	case *ast.MapType:
		return "map[" + getTypeString(t.Key) + "]" + getTypeString(t.Value)
	case *ast.StarExpr:
		return "*" + getTypeString(t.X)
	case *ast.InterfaceType:
		return "interface{}"
	case *ast.ChanType:
		return "chan " + getTypeString(t.Value)
	default:
		return "unknown"
	}
}

func calculateComplexity(funcDecl *ast.FuncDecl) int {
	complexity := 1

	ast.Inspect(funcDecl, func(n ast.Node) bool {
		switch n.(type) {
		case *ast.IfStmt, *ast.ForStmt, *ast.RangeStmt, *ast.SwitchStmt,
			 *ast.TypeSwitchStmt, *ast.SelectStmt:
			complexity++
		case *ast.CaseClause:
			complexity++
		}
		return true
	})

	return complexity
}

func ExtractFailurePatterns(testResults []types.TestResult) []types.FailurePattern {
	patternMap := make(map[string]*types.FailurePattern)

	for _, result := range testResults {
		if result.Status == types.TestStatusFailed && result.Error != "" {
			pattern := extractErrorPattern(result.Error)

			if existing, found := patternMap[pattern]; found {
				existing.Count++
				existing.Tests = append(existing.Tests, result.TestName)
				if result.Timestamp.After(existing.LastSeen) {
					existing.LastSeen = result.Timestamp
				}
			} else {
				patternMap[pattern] = &types.FailurePattern{
					ID:          GenerateID(pattern),
					Pattern:     pattern,
					Description: generatePatternDescription(pattern),
					Count:       1,
					LastSeen:    result.Timestamp,
					Tests:       []string{result.TestName},
					Suggestions: generateSuggestions(pattern),
				}
			}
		}
	}

	var patterns []types.FailurePattern
	for _, pattern := range patternMap {
		patterns = append(patterns, *pattern)
	}

	return patterns
}

func extractErrorPattern(errorMsg string) string {
	errorMsg = strings.ToLower(strings.TrimSpace(errorMsg))

	patterns := []struct {
		regex   *regexp.Regexp
		pattern string
	}{
		{regexp.MustCompile(`panic:.*`), "panic"},
		{regexp.MustCompile(`nil pointer dereference`), "nil_pointer"},
		{regexp.MustCompile(`index out of range`), "index_out_of_range"},
		{regexp.MustCompile(`assertion failed`), "assertion_failed"},
		{regexp.MustCompile(`expected.*got.*`), "expectation_mismatch"},
		{regexp.MustCompile(`timeout`), "timeout"},
		{regexp.MustCompile(`connection.*refused`), "connection_refused"},
		{regexp.MustCompile(`file not found`), "file_not_found"},
		{regexp.MustCompile(`permission denied`), "permission_denied"},
	}

	for _, p := range patterns {
		if p.regex.MatchString(errorMsg) {
			return p.pattern
		}
	}

	return "unknown_error"
}

func generatePatternDescription(pattern string) string {
	descriptions := map[string]string{
		"panic":                "Application panic occurred",
		"nil_pointer":          "Nil pointer dereference",
		"index_out_of_range":   "Array/slice index out of bounds",
		"assertion_failed":     "Test assertion failed",
		"expectation_mismatch": "Expected vs actual value mismatch",
		"timeout":              "Operation timed out",
		"connection_refused":   "Network connection refused",
		"file_not_found":       "File or resource not found",
		"permission_denied":    "Permission denied",
		"unknown_error":        "Unclassified error",
	}

	if desc, found := descriptions[pattern]; found {
		return desc
	}
	return "Unknown error pattern"
}

func generateSuggestions(pattern string) []string {
	suggestions := map[string][]string{
		"panic": {
			"Add panic recovery with defer/recover",
			"Check for nil values before operations",
			"Validate input parameters",
		},
		"nil_pointer": {
			"Add nil checks before dereferencing",
			"Initialize pointers properly",
			"Use safe navigation patterns",
		},
		"index_out_of_range": {
			"Validate array bounds before access",
			"Use range loops instead of index loops",
			"Check slice/array length",
		},
		"assertion_failed": {
			"Review test expectations",
			"Check actual vs expected values",
			"Verify test data setup",
		},
		"expectation_mismatch": {
			"Double-check expected values",
			"Verify function implementation",
			"Review test case inputs",
		},
		"timeout": {
			"Increase timeout duration",
			"Optimize slow operations",
			"Add timeout handling",
		},
		"connection_refused": {
			"Check service availability",
			"Verify network configuration",
			"Add connection retry logic",
		},
		"file_not_found": {
			"Verify file path is correct",
			"Check file permissions",
			"Add file existence validation",
		},
		"permission_denied": {
			"Check file/directory permissions",
			"Run with appropriate privileges",
			"Verify user access rights",
		},
	}

	if suggs, found := suggestions[pattern]; found {
		return suggs
	}
	return []string{"Review error details and context"}
}

func SaveToJSON(data interface{}, filename string) error {
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	err = os.WriteFile(filename, jsonData, 0644)
	if err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	return nil
}

func LoadFromJSON(filename string, data interface{}) error {
	content, err := os.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	err = json.Unmarshal(content, data)
	if err != nil {
		return fmt.Errorf("failed to unmarshal JSON: %w", err)
	}

	return nil
}