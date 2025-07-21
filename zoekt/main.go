package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
	s := server.NewMCPServer(
		"zoekt-mcp-server",
		"1.0.0",
	)

	s.AddTool(createIndexTool(), handleIndexTool)
	s.AddTool(createGitIndexTool(), handleGitIndexTool)
	s.AddTool(createSearchTool(), handleSearchTool)

	if err := server.ServeStdio(s); err != nil {
		log.Fatal(err)
	}
}

func createIndexTool() mcp.Tool {
	return mcp.NewTool("zoekt-index",
		mcp.WithDescription("Index a local directory for code search"),
		mcp.WithString("directory", mcp.Required()),
		mcp.WithString("index_dir"),
		mcp.WithString("output_file", mcp.Required()),
		mcp.WithString("language_map"),
		mcp.WithBoolean("incremental"),
	)
}

func createGitIndexTool() mcp.Tool {
	return mcp.NewTool("zoekt-git-index",
		mcp.WithDescription("Index a git repository for code search"),
		mcp.WithString("repository", mcp.Required()),
		mcp.WithString("index_dir"),
		mcp.WithString("output_file", mcp.Required()),
		mcp.WithString("branches"),
		mcp.WithString("branch_prefix"),
		mcp.WithBoolean("submodules"),
		mcp.WithBoolean("incremental"),
	)
}

func createSearchTool() mcp.Tool {
	return mcp.NewTool("zoekt-search",
		mcp.WithDescription("Search indexed repositories using Zoekt query syntax with advanced options"),
		mcp.WithString("query", mcp.Required()),
		mcp.WithString("index_dir"),
		mcp.WithString("output_file", mcp.Required()),
		mcp.WithString("shard"),
		mcp.WithNumber("max_results"),
		mcp.WithBoolean("list_files"),
		mcp.WithBoolean("show_repo"),
		mcp.WithBoolean("symbol_search"),
		mcp.WithBoolean("debug_score"),
		mcp.WithBoolean("verbose"),
	)
}


func handleIndexTool(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	directory, err := request.RequireString("directory")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	outputFile, err := request.RequireString("output_file")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	cmd := []string{"zoekt-index"}

	indexDir := request.GetString("index_dir", "")
	if indexDir != "" {
		cmd = append(cmd, "-index", indexDir)
	} else {
		homeDir, _ := os.UserHomeDir()
		cmd = append(cmd, "-index", filepath.Join(homeDir, ".zoekt"))
	}

	languageMap := request.GetString("language_map", "")
	if languageMap != "" {
		cmd = append(cmd, "-language_map", languageMap)
	}

	incremental := request.GetBool("incremental", false)
	if incremental {
		cmd = append(cmd, "-incremental")
	}

	cmd = append(cmd, directory)

	result, err := executeCommand(cmd, outputFile)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to execute zoekt-index: %v", err)), nil
	}

	return mcp.NewToolResultText(result), nil
}

func handleGitIndexTool(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	repository, err := request.RequireString("repository")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	outputFile, err := request.RequireString("output_file")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	cmd := []string{"zoekt-git-index"}

	indexDir := request.GetString("index_dir", "")
	if indexDir != "" {
		cmd = append(cmd, "-index", indexDir)
	} else {
		homeDir, _ := os.UserHomeDir()
		cmd = append(cmd, "-index", filepath.Join(homeDir, ".zoekt"))
	}

	branches := request.GetString("branches", "")
	if branches != "" {
		cmd = append(cmd, "-branches", branches)
	}

	branchPrefix := request.GetString("branch_prefix", "")
	if branchPrefix != "" {
		cmd = append(cmd, "-prefix", branchPrefix)
	}

	submodules := request.GetBool("submodules", false)
	if submodules {
		cmd = append(cmd, "-submodules=true")
	}

	incremental := request.GetBool("incremental", false)
	if incremental {
		cmd = append(cmd, "-incremental")
	}

	cmd = append(cmd, repository)

	result, err := executeCommand(cmd, outputFile)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to execute zoekt-git-index: %v", err)), nil
	}

	return mcp.NewToolResultText(result), nil
}

func handleSearchTool(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	query, err := request.RequireString("query")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	outputFile, err := request.RequireString("output_file")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	cmd := []string{"zoekt"}

	// Index directory or shard selection
	shard := request.GetString("shard", "")
	if shard != "" {
		cmd = append(cmd, "-shard", shard)
	} else {
		indexDir := request.GetString("index_dir", "")
		if indexDir != "" {
			cmd = append(cmd, "-index_dir", indexDir)
		} else {
			homeDir, _ := os.UserHomeDir()
			cmd = append(cmd, "-index_dir", filepath.Join(homeDir, ".zoekt"))
		}
	}

	// Maximum results
	maxResults := request.GetFloat("max_results", 0)
	if maxResults > 0 {
		cmd = append(cmd, "-max_matches", fmt.Sprintf("%.0f", maxResults))
	}

	// List files only
	listFiles := request.GetBool("list_files", false)
	if listFiles {
		cmd = append(cmd, "-l")
	}

	// Show repository name
	showRepo := request.GetBool("show_repo", false)
	if showRepo {
		cmd = append(cmd, "-r")
	}

	// Symbol search
	symbolSearch := request.GetBool("symbol_search", false)
	if symbolSearch {
		cmd = append(cmd, "-sym")
	}

	// Debug score
	debugScore := request.GetBool("debug_score", false)
	if debugScore {
		cmd = append(cmd, "-debug")
	}

	// Verbose output
	verbose := request.GetBool("verbose", false)
	if verbose {
		cmd = append(cmd, "-v")
	}

	cmd = append(cmd, query)

	result, err := executeCommand(cmd, outputFile)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to execute zoekt search: %v", err)), nil
	}

	return mcp.NewToolResultText(result), nil
}


func executeCommand(cmd []string, outputFile string) (string, error) {
	execCmd := exec.Command(cmd[0], cmd[1:]...)
	
	output, err := execCmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("command failed: %v, output: %s", err, string(output))
	}

	if err := os.WriteFile(outputFile, output, 0644); err != nil {
		return "", fmt.Errorf("failed to write output to file: %v", err)
	}

	result := map[string]interface{}{
		"command":     strings.Join(cmd, " "),
		"output_file": outputFile,
		"status":      "success",
		"preview":     truncateString(string(output), 500),
	}

	jsonResult, _ := json.MarshalIndent(result, "", "  ")
	return string(jsonResult), nil
}

func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}