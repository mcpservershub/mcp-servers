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

type Rule struct {
	Key      string `json:"key"`
	Name     string `json:"name"`
	Status   string `json:"status"`
	Lang     string `json:"lang"`
	LangName string `json:"langName"`
}

type User struct {
	Login  string `json:"login"`
	Name   string `json:"name"`
	Active bool   `json:"active"`
	Avatar string `json:"avatar"`
}

type Comment struct {
	Key       string `json:"key"`
	Login     string `json:"login"`
	HtmlText  string `json:"htmlText"`
	Markdown  string `json:"markdown"`
	Updatable bool   `json:"updatable"`
	CreatedAt string `json:"createdAt"`
}

type Impact struct {
	SoftwareQuality string `json:"softwareQuality"`
	Severity        string `json:"severity"`
}
type Flow struct {
	Locations []Location `json:"locations"`
}
type Location struct {
	TextRange TextRange `json:"textRange"`
	Msg       string    `json:"msg"`
}
type Issue struct {
	Key                        string            `json:"key"`
	Component                  string            `json:"component"`
	Project                    string            `json:"project"`
	Rule                       string            `json:"rule"`
	IssueStatus                string            `json:"issueStatus"`
	Status                     string            `json:"status"`
	Resolution                 string            `json:"resolution"`
	Severity                   string            `json:"severity"`
	Message                    string            `json:"message"`
	Line                       int               `json:"line"`
	Hash                       string            `json:"hash"`
	Author                     string            `json:"author"`
	Effort                     string            `json:"effort"`
	CreationDate               string            `json:"creationDate"`
	UpdateDate                 string            `json:"updateDate"`
	Tags                       []string          `json:"tags"`
	Type                       string            `json:"type"`
	Comments                   []Comment         `json:"comments"`
	Attr                       map[string]string `json:"attr"`
	Transitions                []string          `json:"transitions"`
	Actions                    []string          `json:"actions"`
	TextRange                  TextRange         `json:"textRange"`
	Flows                      []Flow            `json:"flows"`
	RuleDescriptionContextKey  string            `json:"ruleDescriptionContextKey"`
	CleanCodeAttributeCategory string            `json:"cleanCodeAttributeCategory"`
	CleanCodeAttribute         string            `json:"cleanCodeAttribute"`
	Impacts                    []Impact          `json:"impacts"`
}

type IssuesResponse struct {
	Paging     Paging      `json:"paging"`
	Issues     []Issue     `json:"issues,omitempty"`
	Components []Component `json:"components,omitempty"`
	Rules      []Rule      `json:"rules,omitempty"`
	Users      []User      `json:"users,omitempty"`
}

func AddIssues(s *server.MCPServer) {
	// create a new MCP tool for searching Sonar issues
	issuesTool := mcp.NewTool("sonar_issues",
		mcp.WithDescription("Search and get all issues for a specified Sonar project."),
		mcp.WithString("projectKey",
			mcp.Description("Key of the project or application, e.g. my_project."),
			mcp.DefaultString(""),
			mcp.Required(),
		),
		mcp.WithString("organization",
			mcp.Description("The Sonar cloud organization key or name, e.g. my_organization."),
			mcp.DefaultString(""),
		),
		mcp.WithString("branch",
			mcp.Description("The SCM branch key or name (optional), e.g. feature/my_branch"),
			mcp.DefaultString("main"),
		),
		mcp.WithArray("impactSeverities",
			mcp.Description("The severity of the issues to be retrieved. Possible values: BLOCKER, HIGH, MEDIUM, LOW, INFO."),
			mcp.DefaultArray([]string{"BLOCKER", "HIGH"}),
			mcp.Enum("BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO"),
		),
		mcp.WithArray("issueStatus",
			mcp.Description("The status of the issues to be retrieved. Possible values: OPEN, CONFIRMED, FALSE_POSITIVE, ACCEPTED, FIXED."),
			mcp.DefaultArray([]string{"OPEN"}),
			mcp.Enum("OPEN", "CONFIRMED", "FALSE_POSITIVE", "ACCEPTED", "FIXED"),
		),
		mcp.WithString("resolved",
			mcp.Description("The resolved status of the issues to be retrieved. Possible values: true, false, yes, no."),
			mcp.DefaultString(""),
			mcp.Enum("true", "false", "yes", "no"),
		),
	)

	// add the tool to the server
	s.AddTool(issuesTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		// extract the parameters from the request
		args := request.GetArguments()

		projectKey := args["projectKey"].(string)
		organization := args["organization"].(string)
		branch := args["branch"].(string)
		issueStatus := args["issueStatus"].([]interface{})
		impactSeverities := args["impactSeverities"].([]interface{})
		resolved := args["resolved"].(string)

		// call the Sonarcloud API to get the issues
		issues, err := searchIssues(organization, projectKey, branch, issueStatus, resolved, impactSeverities)
		if err != nil {
			return mcp.NewToolResultErrorFromErr("unable to retrieve issues.", err), nil
		}

		return mcp.NewToolResultText(issues), nil
	})
}

func searchIssues(organization string, projectKey string, branch string, issueStatus []interface{}, resolved string, impactSeverities []interface{}) (string, error) {
	organizationParam := ""
	if organization != "" {
		organizationParam = fmt.Sprintf("&organization=%s", organization)
	}
	branchParam := ""
	if branch != "" {
		branchParam = fmt.Sprintf("&branch=%s", branch)
	}
	issueStatusParam := ""
	if len(issueStatus) > 0 {
		is := utils.InterfacesToStringsOrEmpty(issueStatus)
		// join the issue statuses with commas
		issueStatusParam = fmt.Sprintf("&issueStatuses=%s", strings.Join(is, ","))
	}
	resolvedParam := ""
	if resolved != "" {
		resolvedParam = fmt.Sprintf("&resolved=%s", resolved)
	}
	impactSeveritiesParam := ""
	if len(impactSeverities) > 0 {
		imps := utils.InterfacesToStringsOrEmpty(impactSeverities)
		// join the impact severities with commas
		impactSeveritiesParam = fmt.Sprintf("&impactSeverities=%s", strings.Join(imps, ","))
	}

	// construct the URL for the Sonarcloud API
	url := fmt.Sprintf(SONARQUBE_URL+"api/issues/search?projectKey=%s%s%s%s%s%s",
		projectKey, organizationParam, branchParam, issueStatusParam, resolvedParam, impactSeveritiesParam)

	body, err := utils.MakeGetRequest(url)
	if err != nil {
		return "", err
	}

	var response IssuesResponse
	err = json.Unmarshal(body, &response)
	if err != nil {
		return "", fmt.Errorf("failed to unmarshal response body: %w", err)
	}

	// check if the response contains issues
	if len(response.Issues) == 0 {
		return "No issues found.", nil
	}

	return utils.PrettyPrint(response.Issues)
}
