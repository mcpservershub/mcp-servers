package main

import (
	"flag"
	"os"

	"github.com/mark3labs/mcp-go/server"
	log "github.com/sirupsen/logrus"

	"github.com/intelops/sonarqube-mcp/pkg/tools"
)

var (
	version                  = "v1.0.0"
	transport, port, baseURL string
)

func main() {
	flag.StringVar(&transport, "t", "stdio", "Transport type (stdio or sse)")
	flag.StringVar(&port, "p", "2222", "Port for SSE transport")
	flag.StringVar(&baseURL, "b", "http://localhost:2222", "Base URL for SSE transport")
	flag.Parse()

	if envPort, ok := os.LookupEnv("PORT"); ok {
		port = envPort
	}

	if envBaseURL, ok := os.LookupEnv("BASE_URL"); ok {
		baseURL = envBaseURL
	}

	// -- build your MCP server
	mcpServer := server.NewMCPServer(
		"SonarQube MCP Server",
		version,
		server.WithLogging(),
		server.WithRecovery(),
		server.WithToolCapabilities(false),
	)

	// -- register tools in one shot (needs tools package to export ServerTool values)
	tools.AddProjects(mcpServer)
	tools.AddDuplications(mcpServer)
	tools.AddIssues(mcpServer)
	tools.AddHotspots(mcpServer)
	tools.AddMeasures(mcpServer)
	// -- pick transport
	if transport == "sse" {
		sseServer := server.NewSSEServer(mcpServer, server.WithBaseURL(baseURL))
		sseEndpoint := "0.0.0.0:" + port
		log.Infof("SonarQube MCP Server running on %s", sseEndpoint)
		if err := sseServer.Start(sseEndpoint); err != nil {
			log.Fatalf("Sonar MCP Server (SSE) error: %v", err)
		}
		log.Infof("SonarQube SSE MCP Server started on %v:%v", baseURL, port)
	} else {
		if err := server.ServeStdio(mcpServer); err != nil {
			log.Fatalf("error starting SonarQube MCP Server: %v", err)
		}
		log.Info("SonarQube STDIO MCP Server started ...")
	}
	log.Info("SonarQube MCP Server started ...")
}
