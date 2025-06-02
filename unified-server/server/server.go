package main

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"strings"

	img "github.com/docker/docker/api/types/image"
	"github.com/docker/docker/client"
	"github.com/google/uuid"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	log "github.com/sirupsen/logrus"
)

// ToolHandler defines the signature for our tool functions.
type ToolHandler func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error)

// jsonRPCRequest is the structure expected for incoming JSON‑RPC requests.
// We use the JSON‑RPC "method" value to populate the MCP
// CallToolRequest’s Params.Name field.
type jsonRPCRequest struct {
	JSONRPC string `json:"jsonrpc"`
	Method  string `json:"method"`
	Params  struct {
		Arguments map[string]interface{} `json:"arguments"`
	} `json:"params"`
	ID interface{} `json:"id"`
}

func (jsonrpcrequest *jsonRPCRequest) Read(p []byte) (n int, err error) {
	panic("not implemented") // TODO: Implement
}

// jsonRPCResponse defines the structure we return for JSON‑RPC responses.
type jsonRPCResponse struct {
	JSONRPC string      `json:"jsonrpc"`
	Result  interface{} `json:"result,omitempty"`
	Error   string      `json:"error,omitempty"`
	ID      interface{} `json:"id"`
}

type sseSession struct {
	sessionID           string
	notificationChannel chan mcp.JSONRPCNotification
	initialized         bool
}

var (
	mcpServer    *server.MCPServer
	toolHandlers = map[string]ToolHandler{}
)

// Implement the ClientSession interface
func (s *sseSession) SessionID() string {
	return s.sessionID
}

func (s *sseSession) NotificationChannel() chan<- mcp.JSONRPCNotification {
	return s.notificationChannel
}

func (s *sseSession) Initialize() {
	s.initialized = true
}

func (s sseSession) Initialized() bool {
	return s.initialized
}

func main() {
	log.SetLevel(log.TraceLevel)
	hooks := &server.Hooks{}

	hooks.AddAfterCallTool(func(
		ctx context.Context,
		id any,
		req *mcp.CallToolRequest,
		res *mcp.CallToolResult,
	) {
		log.Infof("✅ Tool '%v' completed: %v",
			req.Params.Name,
			res,
		)
	})

	// 2) log *every* MCP method (initialize, list_tools, tools/call, etc.)
	hooks.AddBeforeAny(func(ctx context.Context, id any, method mcp.MCPMethod, message any) {
		log.Debugf("⮑ Incoming RPC: %s  payload=%#v", method, message)
	}) // :contentReference[oaicite:0]{index=0}

	// 3) narrow in on tool‐calls if you like
	hooks.AddBeforeCallTool(func(ctx context.Context, id any, req *mcp.CallToolRequest) {
		log.Infof("🔧 Calling tool: %s  args=%v", req.Params.Name, req.Params.Arguments)
	})

	// Create and configure the MCP server.
	mcpServer = server.NewMCPServer(
		"MCP Tool STDIO Server",
		"v1.0.0",
		server.WithResourceCapabilities(true, true),
		server.WithLogging(),
		server.WithHooks(hooks),
		server.WithPromptCapabilities(false),
	)
	mcpServer.AddNotificationHandler("notifications/error", handleNotification)

	hooks.AddAfterInitialize(func(ctx context.Context, id any, msg *mcp.InitializeRequest, res *mcp.InitializeResult) {
		// We need to send UserAgent details as well
		sessionID := uuid.New().String()
		session := &sseSession{
			sessionID:           sessionID,
			notificationChannel: make(chan mcp.JSONRPCNotification, 10),
		}
		ctx = mcpServer.WithContext(context.Background(), session)

		if err := mcpServer.RegisterSession(ctx, session); err != nil {
			log.Printf("Failed to register session : %v", err)
		}
		err := mcpServer.SendNotificationToSpecificClient(session.SessionID(), "notification/update", map[string]any{"Message:": "New notification"})
		defer mcpServer.UnregisterSession(ctx, session.SessionID())

		if err != nil {
			log.Printf("Failed to send notifications: %v", err)
		}
	})

	// Tool registrations

	// --- Register the MarkitDown tool ---

	markItDownTool := mcp.NewTool("to-markdown",
		mcp.WithDescription("Converts the provided input file to Markdown"),
		mcp.WithString("input",
			mcp.Required(),
			mcp.Description("The path to the input file"),
		),
		mcp.WithString("output",
			mcp.Required(),
			mcp.Description("The path to the output file"),
		),
	)
	MarkItDownHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		// Validate the "input" and "output" arguments.
		input, ok := req.Params.Arguments["input"].(string)
		if !ok || input == "" {
			return mcp.NewToolResultText("invalid or missing input parameter"), nil
		}
		output, ok := req.Params.Arguments["output"].(string)
		if !ok || output == "" {
			return mcp.NewToolResultText("invalid or missing output parameter"), nil
		}
		// TODO: Implememt the MarkitDown CLI Command using exec.Command() to run the tool
		cmd := exec.Command("markitdown", input, "-o", output)
		outBytes, err := cmd.CombinedOutput()
		if err != nil {
			return mcp.NewToolResultText(fmt.Sprintf("failed to run markitdown: %v\nOutput: %s", err, string(outBytes))), nil
		}

		return mcp.NewToolResultText(fmt.Sprintf("Conversion successful. Output:\n%s", output)), nil
	}

	mcpServer.AddTool(markItDownTool, MarkItDownHandler)
	toolHandlers["to-markdown"] = MarkItDownHandler

	// Register ast-grep tool
	searchCodeTool := mcp.NewTool("ast-grep",
		mcp.WithDescription("Search for code in a file"),
		mcp.WithString("pattern",
			mcp.Required(),
			mcp.Description("The pattern to search for"),
		),
		mcp.WithString("new-pattern",
			mcp.Required(),
			mcp.Description("The pattern to replace with"),
		),
		mcp.WithString("language",
			mcp.Required(),
			mcp.Description("The language to search in"),
		),
		mcp.WithString("path",
			mcp.Required(),
			mcp.Description("The path to the file/directory to search in"),
		),
	)
	searchCodeHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		// 1. Validate
		pattern, ok := req.Params.Arguments["pattern"].(string)
		if !ok || pattern == "" {
			return mcp.NewToolResultText("invalid or missing 'pattern' parameter"), nil
		}
		newPattern, ok := req.Params.Arguments["new-pattern"].(string)
		if !ok || newPattern == "" {
			return mcp.NewToolResultText("invalid or missing 'new-pattern' parameter"), nil
		}
		lang, ok := req.Params.Arguments["language"].(string)
		if !ok || lang == "" {
			return mcp.NewToolResultText("invalid or missing 'language' parameter"), nil
		}
		pathParam, ok := req.Params.Arguments["path"].(string)
		if !ok || pathParam == "" {
			return mcp.NewToolResultText("invalid or missing 'path' parameter"), nil
		}

		// 2. Split paths (comma or space)
		var paths []string
		if strings.Contains(pathParam, ",") {
			for _, p := range strings.Split(pathParam, ",") {
				if t := strings.TrimSpace(p); t != "" {
					paths = append(paths, t)
				}
			}
		} else {
			paths = strings.Fields(pathParam)
		}

		// 3. Build CLI args
		args := []string{
			"--pattern", pattern,
			"--rewrite", newPattern,
			"--lang", lang,
			"-U",
		}
		args = append(args, paths...)

		//  Run ast-grep
		outBytes, err := exec.Command("ast-grep", args...).CombinedOutput()
		out := strings.TrimSpace(string(outBytes))

		// If the CLI itself errored *and* produced no output, treat as “no matches”
		if err != nil && out == "" {
			msg := fmt.Sprintf("No occurrences of '%s' found in %v", pattern, paths)
			return mcp.NewToolResultText(msg), nil
		}
		// If the CLI errored *with* some output, return that as the text
		if err != nil {
			return mcp.NewToolResultText(fmt.Sprintf("ast-grep error: %v\n\n%s", err, out)), nil
		}
		// If CLI succeeded but no matches, still say so
		if out == "" {
			msg := fmt.Sprintf("No occurrences of '%s' found in %v", pattern, paths)
			return mcp.NewToolResultText(msg), nil
		}
		// Otherwise return the real diff/matches
		return mcp.NewToolResultText(out), nil
	}

	mcpServer.AddTool(searchCodeTool, searchCodeHandler)
	toolHandlers["ast-grep"] = searchCodeHandler

	// Add Mirrord tool
	mirrordTool := mcp.NewTool("mirrord-exec",
		mcp.WithDescription("Run `mirrord exec` using a given config file"),
		mcp.WithString("config",
			mcp.Required(),
			mcp.Description("Path to the mirrord JSON config file"),
		),
	)

	mirrordHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		// Validate config param
		cfg, ok := req.Params.Arguments["config"].(string)
		if !ok || cfg == "" {
			return mcp.NewToolResultText("invalid or missing 'config' parameter"), nil
		}

		// Build and run: mirrord exec --config=<cfg>
		cmd := exec.Command("mirrord", "exec", "--config="+cfg)
		out, err := cmd.CombinedOutput()
		text := string(out)

		if err != nil {
			return mcp.NewToolResultText(
				fmt.Sprintf("mirrord exec failed: %v\n\n%s", err, text),
			), nil
		}
		return mcp.NewToolResultText(text), nil
	}

	mcpServer.AddTool(mirrordTool, mirrordHandler)
	toolHandlers["mirrord-exec"] = mirrordHandler

	// --- Register the pull_image tool ---
	PullImageTool := mcp.NewTool("pull_image",
		mcp.WithDescription("Pull an image from Docker Hub"),
		mcp.WithString("image",
			mcp.Description("Name of the Docker image to pull (e.g., 'nginx:latest')"),
		),
	)
	PullImageHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		// Validate the "image" argument.
		image, ok := req.Params.Arguments["image"].(string)
		if !ok || image == "" {
			return mcp.NewToolResultText("invalid or missing image parameter"), nil
		}
		fmt.Fprintf(os.Stderr, "[DEBUG] Invoking tool 'pull_image' with image: %s\n", image)

		// Use the Docker client to pull the image.
		cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
		if err != nil {
			return nil, fmt.Errorf("failed to create Docker client: %v", err)
		}
		out, err := cli.ImagePull(ctx, image, img.PullOptions{})
		if err != nil {
			return nil, fmt.Errorf("failed to pull image: %v", err)
		}
		defer out.Close()
		// Log the Docker pull progress.
		_, err = io.Copy(os.Stderr, out)
		if err != nil {
			return nil, fmt.Errorf("error reading Docker pull response: %v", err)
		}
		return mcp.NewToolResultText(fmt.Sprintf("Image '%s' pulled successfully", image)), nil
	}
	mcpServer.AddTool(PullImageTool, PullImageHandler)
	toolHandlers["pull_image"] = PullImageHandler

	// --- Register the get_pods tool ---
	getPodsTool := mcp.NewTool("get_pods",
		mcp.WithDescription("Get Kubernetes Pods from the cluster"),
	)
	getPodsHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		fmt.Fprintln(os.Stderr, "[DEBUG] Invoking tool 'get_pods'")
		cmd := exec.Command("kubectl", "get", "pods")
		output, err := cmd.CombinedOutput()
		if err != nil {
			return nil, fmt.Errorf("failed to get pods: %v, output: %s", err, string(output))
		}
		return mcp.NewToolResultText(string(output)), nil
	}
	mcpServer.AddTool(getPodsTool, getPodsHandler)
	toolHandlers["get_pods"] = getPodsHandler

	// --- Register the git_init tool ---
	gitInitTool := mcp.NewTool("git_init",
		mcp.WithDescription("Initialize a Git repository in the provided project directory"),
		mcp.WithString("directory",
			mcp.Description("Path to the project directory"),
		),
	)
	gitInitHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		directory, ok := req.Params.Arguments["directory"].(string)
		if !ok || directory == "" {
			return nil, fmt.Errorf("invalid or missing directory parameter")
		}
		fmt.Fprintf(os.Stderr, "[DEBUG] Invoking tool 'git_init' with directory: %s\n", directory)
		cmd := exec.Command("git", "init", directory)
		output, err := cmd.CombinedOutput()
		if err != nil {
			return nil, fmt.Errorf("failed to initialize git repository: %v, output: %s", err, string(output))
		}
		return mcp.NewToolResultText(string(output)), nil
	}
	mcpServer.AddTool(gitInitTool, gitInitHandler)
	toolHandlers["git_init"] = gitInitHandler

	// --- Register the create_table in Postgres tool ---
	createTableTool := mcp.NewTool("create_table",
		mcp.WithDescription("Create a database table in a local Postgres DB instance"),
		mcp.WithString("table_name",
			mcp.Description("Name of the table to create"),
		),
		mcp.WithString("headers",
			mcp.Required(),
			mcp.Description("Comma separated column definitions (e.g., 'id SERIAL PRIMARY KEY, name TEXT')"),
		),
		mcp.WithString("values",
			mcp.Description("Comma separated list of values to insert (e.g., '1, \"John\"')"),
		),
	)
	createTableHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		tableName, ok := req.Params.Arguments["table_name"].(string)
		if !ok || tableName == "" {
			return nil, fmt.Errorf("invalid or missing table_name parameter")
		}
		headers, ok := req.Params.Arguments["headers"].(string)
		if !ok || headers == "" {
			return nil, fmt.Errorf("invalid or missing headers parameter")
		}
		values, ok := req.Params.Arguments["values"].(string)
		if !ok {
			return nil, fmt.Errorf("invalid or missing values parameter")
		}
		fmt.Fprintf(os.Stderr, "[DEBUG] Invoking tool 'create_table' with table: %s\n", tableName)
		sqlCmd := fmt.Sprintf("CREATE TABLE %s (%s); INSERT INTO %s VALUES (%s);", tableName, headers, tableName, values)
		cmd := exec.Command("psql", "-d", "postgres", "-c", sqlCmd)
		output, err := cmd.CombinedOutput()
		if err != nil {
			return nil, fmt.Errorf("failed to create table: %v, output: %s", err, string(output))
		}
		return mcp.NewToolResultText(string(output)), nil
	}
	mcpServer.AddTool(createTableTool, createTableHandler)
	toolHandlers["create_table"] = createTableHandler

	// Register read query using SELECT tool in Sqlite

	readQueryTool := mcp.NewTool("read-query",
		mcp.WithDescription("Execute a SELECT query on a SQLite DB (returns CSV)"),
		mcp.WithString("db",
			mcp.Required(),
			mcp.Description("Path to the .db file"),
		),
		mcp.WithString("query",
			mcp.Required(),
			mcp.Description("The SELECT SQL to run"),
		),
	)
	readQueryHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		db, _ := req.Params.Arguments["db"].(string)
		q, _ := req.Params.Arguments["query"].(string)
		cmd := exec.Command("sqlite3", "-csv", db, q)
		out, err := cmd.CombinedOutput()
		if err != nil {
			return mcp.NewToolResultText(
				fmt.Sprintf("read-query failed: %v\n\n%s", err, string(out)),
			), nil
		}
		return mcp.NewToolResultText(string(out)), nil
	}
	mcpServer.AddTool(readQueryTool, readQueryHandler)
	toolHandlers["read-query"] = readQueryHandler

	// write-query too in Sqlite using INSERT/UPDATE/DELETE
	writeQueryTool := mcp.NewTool("write-query",
		mcp.WithDescription("Execute INSERT/UPDATE/DELETE on a SQLite DB"),
		mcp.WithString("db",
			mcp.Required(),
			mcp.Description("Path to the .db file"),
		),
		mcp.WithString("query",
			mcp.Required(),
			mcp.Description("The non-SELECT SQL to run"),
		),
	)
	writeQueryHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		db, _ := req.Params.Arguments["db"].(string)
		q, _ := req.Params.Arguments["query"].(string)
		cmd := exec.Command("sqlite3", db, q)
		out, err := cmd.CombinedOutput()
		if err != nil {
			return mcp.NewToolResultText(
				fmt.Sprintf("write-query failed: %v\n\n%s", err, string(out)),
			), nil
		}
		return mcp.NewToolResultText("OK"), nil
	}
	mcpServer.AddTool(writeQueryTool, writeQueryHandler)
	toolHandlers["write-query"] = writeQueryHandler

	//  create-table tool in Sqlite wraps write-query for a CREATE TABLE statement
	createSQLTableTool := mcp.NewTool("create-SQLtable",
		mcp.WithDescription("Create a new table in the SQLite DB"),
		mcp.WithString("db",
			mcp.Required(),
			mcp.Description("Path to the .db file"),
		),
		mcp.WithString("definition",
			mcp.Required(),
			mcp.Description("SQL table definition, e.g. `CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);`"),
		),
	)
	createSQLTableHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		db, _ := req.Params.Arguments["db"].(string)
		def, _ := req.Params.Arguments["definition"].(string)
		cmd := exec.Command("sqlite3", db, def)
		out, err := cmd.CombinedOutput()
		if err != nil {
			return mcp.NewToolResultText(
				fmt.Sprintf("create-table failed: %v\n\n%s", err, string(out)),
			), nil
		}
		return mcp.NewToolResultText("Table created"), nil
	}
	mcpServer.AddTool(createSQLTableTool, createSQLTableHandler)
	toolHandlers["create-table"] = createSQLTableHandler

	// list-tables tool in Sqlite query
	listTablesTool := mcp.NewTool("list-tables",
		mcp.WithDescription("List all tables in the SQLite DB"),
		mcp.WithString("db",
			mcp.Required(),
			mcp.Description("Path to the .db file"),
		),
	)
	listTablesHandler := func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		db, _ := req.Params.Arguments["db"].(string)
		sql := `SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;`
		cmd := exec.Command("sqlite3", "-csv", db, sql)
		out, err := cmd.CombinedOutput()
		if err != nil {
			return mcp.NewToolResultText(
				fmt.Sprintf("list-tables failed: %v\n\n%s", err, string(out)),
			), nil
		}
		return mcp.NewToolResultText(fmt.Sprintf("'%v' DB contains '%v' table.", db, string(out))), nil
	}
	mcpServer.AddTool(listTablesTool, listTablesHandler)
	toolHandlers["list-tables"] = listTablesHandler

	// Setup the Server

	addr := ":1234"
	// sse := server.NewSSEServer(mcpServer, server.WithMessageEndpoint("/rpc"), server.WithSSEEndpoint("/sse"))
	sseServer := server.NewSSEServer(mcpServer, server.WithBaseURL("http://localhost:1234"), server.WithMessageEndpoint("/rpc"), server.WithSSEEndpoint("/sse"), server.WithHTTPServer(&http.Server{
		Addr: addr,
	}),
	)

	// mux := http.NewServeMux()
	// mux.Handle("/sse", sse.SSEHandler())
	// mux.Handle("/rpc", sse.MessageHandler())
	//
	log.Printf("▶️  Starting MCP HTTP/SSE server 1 on %s ...", addr)
	if err := http.ListenAndServe(addr, sseServer); err != nil {
		log.Fatalf("❌  Failed to start server1: %v", err)
	}
}

func handleNotification(ctx context.Context, notification mcp.JSONRPCNotification) {
	fmt.Printf("Received notification from client: %s\n", notification.Method)
}
