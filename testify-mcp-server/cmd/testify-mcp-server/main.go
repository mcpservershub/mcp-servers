package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"github.com/mark3labs/mcp-go/server"
	testifyserver "github.com/mcpservershub/mcpservers/testify-mcp/pkg/server"
)

var (
	version = "1.0.0"
	name    = "testify-mcp-server"
)

func main() {
	var (
		workDir    = flag.String("work-dir", ".", "Working directory for Go projects")
		dataDir    = flag.String("data-dir", "./data", "Directory to store test data and history")
		port       = flag.Int("port", 0, "Port to listen on (0 for stdio)")
		showVersion = flag.Bool("version", false, "Show version and exit")
		debug      = flag.Bool("debug", false, "Enable debug logging")
	)
	flag.Parse()

	if *showVersion {
		fmt.Printf("%s version %s\n", name, version)
		os.Exit(0)
	}

	if *debug {
		log.SetFlags(log.LstdFlags | log.Lshortfile)
		log.Println("Debug logging enabled")
	}

	workDirAbs, err := filepath.Abs(*workDir)
	if err != nil {
		log.Fatalf("Failed to resolve work directory: %v", err)
	}

	dataDirAbs, err := filepath.Abs(*dataDir)
	if err != nil {
		log.Fatalf("Failed to resolve data directory: %v", err)
	}

	if *debug {
		log.Printf("Work directory: %s", workDirAbs)
		log.Printf("Data directory: %s", dataDirAbs)
	}

	testifyServer := testifyserver.NewTestifyMCPServer(workDirAbs, dataDirAbs)
	mcpServer := testifyServer.CreateMCPServer()

	if *debug {
		log.Printf("Starting %s v%s", name, version)
		if *port > 0 {
			log.Printf("Listening on port %d", *port)
		} else {
			log.Println("Using stdio transport")
		}
	}

	if *port > 0 {
		log.Printf("HTTP transport not yet supported in this version, using stdio")
	}

	if err := server.ServeStdio(mcpServer); err != nil {
		log.Fatalf("Server error: %v", err)
	}

	if *debug {
		log.Println("Server stopped")
	}
}