package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/mark3labs/mcp-go/server"
	mcpserver "github.com/mcpservershub/mcpservers/testify-mcp/pkg/server"
)

func main() {
	// Parse command-line flags
	workDir := flag.String("work-dir", "/workspace", "Working directory for test execution")
	dataDir := flag.String("data-dir", "/app/data", "Data directory for storing analysis results")
	debug := flag.Bool("debug", false, "Enable debug logging")
	flag.Parse()

	// Set up logging
	if *debug {
		log.SetFlags(log.LstdFlags | log.Lshortfile)
		log.Println("Debug mode enabled")
	}

	// Ensure directories exist
	if err := ensureDir(*workDir); err != nil {
		log.Fatalf("Failed to create work directory: %v", err)
	}
	if err := ensureDir(*dataDir); err != nil {
		log.Fatalf("Failed to create data directory: %v", err)
	}

	log.Printf("Starting Testify MCP Server...")
	log.Printf("Work directory: %s", *workDir)
	log.Printf("Data directory: %s", *dataDir)

	// Create and configure the Testify MCP server
	testifyServer := mcpserver.NewTestifyMCPServer(*workDir, *dataDir)
	mcpSrv := testifyServer.CreateMCPServer()

	// Start the MCP server
	if err := server.ServeStdio(mcpSrv); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

// ensureDir creates a directory if it doesn't exist
func ensureDir(dir string) error {
	info, err := os.Stat(dir)
	if os.IsNotExist(err) {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
		return nil
	}
	if err != nil {
		return fmt.Errorf("failed to stat directory %s: %w", dir, err)
	}
	if !info.IsDir() {
		return fmt.Errorf("%s exists but is not a directory", dir)
	}
	return nil
}
