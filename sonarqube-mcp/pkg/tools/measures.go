package tools

import (
	"context"
	"fmt"
	"net/url"
	"os"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"

	"github.com/intelops/sonarqube-mcp/pkg/utils"
)

func AddMeasures(s *server.MCPServer) {
	measureTool := mcp.NewTool("sonar_measures",
		mcp.WithDescription("Fetch measure for metrics from Sonar scan results"),
		mcp.WithString("projectKey",
			mcp.Description("Project or applucation identification key. eg my_project"),
			mcp.Required(),
		),
		mcp.WithString("outputFile",
			mcp.Description("output path to store the fetched measures JSON file"),
			mcp.DefaultString(""),
			mcp.Required(),
		),
		mcp.WithArray("metricKeys",
			mcp.Description("Comma saperated list of metric keys, eg: complexity,violations,security"),
			mcp.DefaultArray([]any{}),
			mcp.Required(),
		),
	)

	// Add tool to the server

	s.AddTool(measureTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		args := request.GetArguments()

		projectKey, ok := args["projectKey"].(string)
		if !ok {
			return nil, fmt.Errorf("missing projectKey parameter")
		}
		outputFile, ok := args["outputPath"].(string)
		if !ok {
			return nil, fmt.Errorf("missing outputFile parameter")
		}
		metricKeys := args["metricKeys"].([]any)

		measures, err := fetchMeasures(projectKey, metricKeys, outputFile)
		if err != nil {
			return mcp.NewToolResultErrorFromErr("unable to fetch measures", err), nil
		}
		return mcp.NewToolResultText(measures), nil
	})
}

func fetchMeasures(projectKey string, metricKeys []any, outputFile string) (string, error) {
	mks := utils.InterfacesToStringsOrEmpty(metricKeys)

	encodedMetrics := ""
	if len(mks) > 0 {
		csv := strings.Join(mks, ",")
		encodedMetrics = url.QueryEscape(csv)
	}

	base := SONARQUBE_URL + "api/measures/component?"
	params := fmt.Sprintf("metricKeys=%s&component=%s", encodedMetrics, url.QueryEscape(projectKey))
	fullURL := base + params
	body, err := utils.MakeGetRequest(fullURL)
	if err != nil {
		return "", err
	}

	// Write raw JSON bytes to disk
	if err := os.WriteFile(outputFile, body, 0o644); err != nil {
		return "", fmt.Errorf("failed to write JSON to %s: %w", outputFile, err)
	}
	return fmt.Sprintf("Written Measures output to: %s", outputFile), nil
}
