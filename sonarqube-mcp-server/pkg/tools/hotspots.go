package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/intelops/sonarqube-mcp/pkg/utils"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

type TextRange struct {
	StartLine   int `json:"startLine"`
	EndLine     int `json:"endLine"`
	StartOffset int `json:"startOffset"`
	EndOffset   int `json:"endOffset"`
}
type Hotspot struct {
	Key                      string    `json:"key"`
	Component                string    `json:"component"`
	Project                  string    `json:"project"`
	SecurityCategory         string    `json:"securityCategory"`
	VulnerabilityProbability string    `json:"vulnerabilityProbability"`
	Status                   string    `json:"status"`
	Line                     int       `json:"line"`
	Message                  string    `json:"message"`
	Assignee                 string    `json:"assignee"`
	Author                   string    `json:"author"`
	CreationDate             string    `json:"creationDate"`
	UpdateDate               string    `json:"updateDate"`
	TextRange                TextRange `json:"textRange"`
	RuleKey                  string    `json:"ruleKey"`
}
type HotspotsResponse struct {
	Paging     Paging      `json:"paging"`
	Hotspots   []Hotspot   `json:"hotspots"`
	Components []Component `json:"components"`
}

func AddHotspots(s *server.MCPServer) {
	// create a new MCP tool for searching security hotspots
	hotspotsTool := mcp.NewTool("sonar_hotspots",
		mcp.WithDescription("Search and get security hotpots in the source files of a specified Sonar project."),
		mcp.WithString("projectKey",
			mcp.Description("Key of the project or application, e.g. my_project."),
			mcp.Required(),
		),
		mcp.WithArray("files",
			mcp.Description("Array or list of file paths. Returns only hotspots found in those files, e.g. src/foo/Bar.php. This parameter is optional."),
			mcp.DefaultArray([]string{}),
		),
		mcp.WithString("status",
			mcp.Description("The status of the security hotspot, only these are returned, e.g. TO_REVIEW, REVIEWED. This parameter is optional."),
			mcp.DefaultString(""),
			mcp.Enum("TO_REVIEW", "REVIEWED"),
		),
	)

	// add the tool to the server
	s.AddTool(hotspotsTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		// extract the parameters from the request
		args := request.GetArguments()

		projectKey, ok := args["projectKey"].(string)
		if !ok {
			return nil, fmt.Errorf("missing projectKey parameter")
		}
		files := args["files"].([]any)
		status := args["status"].(string)

		// call the Sonarcloud API to get the hotspots
		duplications, err := searchHotspots(projectKey, files, status)
		if err != nil {
			return mcp.NewToolResultErrorFromErr("unable to retrieve security hotspots.", err), nil
		}

		return mcp.NewToolResultText(duplications), nil
	})
}

func searchHotspots(projectKey string, files []any, status string) (string, error) {
	filesParam := ""
	fs := utils.InterfacesToStringsOrEmpty(files)

	if len(files) > 0 {
		filesParam = fmt.Sprintf("&files=%s", strings.Join(fs, ","))
	}
	statusParam := ""
	if status != "" {
		statusParam = fmt.Sprintf("&status=%s", status)
	}

	url := fmt.Sprintf(SONARQUBE_URL+"api/hotspots/search?projectKey=%s%s%s", projectKey, filesParam, statusParam)

	body, err := utils.MakeGetRequest(url)
	if err != nil {
		return "", err
	}

	var response HotspotsResponse
	err = json.Unmarshal(body, &response)
	if err != nil {
		return "", fmt.Errorf("failed to unmarshal response body: %w", err)
	}

	return utils.PrettyPrint(response)
}
