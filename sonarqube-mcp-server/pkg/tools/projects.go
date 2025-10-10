package tools

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/intelops/sonarqube-mcp/pkg/utils"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	log "github.com/sirupsen/logrus"
)

type Projects struct {
	Organization     string `json:"organization"`
	Key              string `json:"key"`
	Name             string `json:"name"`
	Qualifier        string `json:"qualifier"`
	Visibility       string `json:"visibility"`
	LastAnalysisDate string `json:"lastAnalysisDate"`
	Revision         string `json:"revision"`
}

type Paging struct {
	PageIndex int `json:"pageIndex"`
	PageSize  int `json:"pageSize"`
	Total     int `json:"total"`
}
type ProjectsResponse struct {
	Paging     Paging     `json:"paging"`
	Components []Projects `json:"components"`
}

func AddProjects(s *server.MCPServer) {
	// create a new MCP tool for listing Sonar projects
	projectsTool := mcp.NewTool("sonar_projects",
		mcp.WithDescription("List all Sonar projects for a given organization."),
		mcp.WithString("organization",
			mcp.Description("The Sonar cloud organization name, e.g. my_organization."),
			mcp.Required(),
		),
	)

	// Add Project tool to the server
	s.AddTool(projectsTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		args := request.GetArguments()
		// Extract the organization name from the request
		org, ok := args["organization"].(string)
		if !ok {
			return nil, fmt.Errorf("missing organization parameter")
		}

		// Make a call to Sonarcloud API to get projects
		projects, err := searchProjects(org)
		if err != nil {
			return mcp.NewToolResultErrorFromErr("unable to retrieve sonar projects.", err), nil
		}

		// Return the projects as result
		return mcp.NewToolResultText(projects), nil
	})
}

func searchProjects(organization string) (string, error) {
	url := fmt.Sprintf(SONARQUBE_URL+"api/projects/search?organization=%s", organization)
	log.Infof("Making request to: %v", url)

	body, err := utils.MakeGetRequest(url)
	if err != nil {
		return "", err
	}

	var projectsResponse ProjectsResponse
	err = json.Unmarshal(body, &projectsResponse)
	if err != nil {
		return "", fmt.Errorf("failed to unmarshal response body: %w", err)
	}

	return utils.PrettyPrint(projectsResponse.Components)
}
