# Context7 MCP Server Output Format Analysis

## Overview
The Context7 MCP Server follows the Model Context Protocol (MCP) standard for output formatting. All tool responses are wrapped in a specific JSON structure that the MCP protocol defines.

## MCP Response Structure
All tool outputs follow this general MCP response format:
```json
{
  "content": [
    {
      "type": "text",
      "text": "<actual tool output>"
    }
  ]
}
```

## Tool Output Formats

### 1. resolve-library-id Tool

#### Output Structure:
The tool returns a formatted text string with the following structure:

```
Available Libraries (top matches):

Each result includes:
- Library ID: Context7-compatible identifier (format: /org/project)
- Name: Library or package name
- Description: Short summary
- Code Snippets: Number of available code examples
- Trust Score: Authority indicator
- Versions: List of versions if available. Use one of those versions if and only if the user explicitly provides a version in their query.

For best results, select libraries based on name match, trust score, snippet coverage, and relevance to your use case.

----------

[SEARCH RESULTS]
```

#### Search Results Format:
Each library result is formatted as:
```
- Title: [library title]
- Context7-compatible library ID: [/org/project format]
- Description: [short description]
- Code Snippets: [number] (only shown if available)
- Trust Score: [number] (only shown if available)
- Versions: [version1, version2, ...] (only shown if available)
----------
```

#### Example Output:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Available Libraries (top matches):\n\nEach result includes:\n- Library ID: Context7-compatible identifier (format: /org/project)\n- Name: Library or package name\n- Description: Short summary\n- Code Snippets: Number of available code examples\n- Trust Score: Authority indicator\n- Versions: List of versions if available. Use one of those versions if and only if the user explicitly provides a version in their query.\n\nFor best results, select libraries based on name match, trust score, snippet coverage, and relevance to your use case.\n\n----------\n\n- Title: React\n- Context7-compatible library ID: /facebook/react\n- Description: A JavaScript library for building user interfaces\n- Code Snippets: 1250\n- Trust Score: 10\n- Versions: v18.2.0, v17.0.2\n----------\n- Title: React Native\n- Context7-compatible library ID: /facebook/react-native\n- Description: Build mobile apps with React\n- Code Snippets: 890\n- Trust Score: 9"
    }
  ]
}
```

### 2. get-library-docs Tool

#### Output Structure:
The tool returns the raw documentation text fetched from the Context7 API, wrapped in the MCP response format.

#### Example Output:
```json
{
  "content": [
    {
      "type": "text",
      "text": "# React Hooks Documentation\n\n## useState\n\nThe useState Hook lets you add state to functional components...\n\n```javascript\nconst [state, setState] = useState(initialState);\n```\n\n## useEffect\n\nThe Effect Hook lets you perform side effects in function components..."
    }
  ]
}
```

## Error Handling Output Formats

### 1. When no results are found (resolve-library-id):
```json
{
  "content": [
    {
      "type": "text",
      "text": "Failed to retrieve library documentation data from Context7"
    }
  ]
}
```

### 2. When documentation is not found (get-library-docs):
```json
{
  "content": [
    {
      "type": "text",
      "text": "Documentation not found or not finalized for this library. This might have happened because you used an invalid Context7-compatible library ID. To get a valid Context7-compatible library ID, use the 'resolve-library-id' with the package name you wish to retrieve documentation for."
    }
  ]
}
```

### 3. When file writing fails (with output_file parameter):
```json
{
  "content": [
    {
      "type": "text",
      "text": "Error writing to file: [error message]\n\n[original tool output]"
    }
  ]
}
```

## STDOUT Communication

When running in STDIO mode, the server communicates using JSON-RPC messages over standard input/output:

1. **Server Ready Message** (to stderr):
   ```
   Context7 Documentation MCP Server running on stdio
   ```

2. **Tool Responses** (to stdout):
   - All responses are JSON-RPC formatted
   - Include the MCP response structure shown above
   - Are line-delimited JSON messages

3. **Error Messages** (to stderr):
   - Rate limiting errors
   - Connection failures
   - File writing errors (when using output_file)

## Key Observations:

1. **Plain Text Format**: Both tools return plain text content, not structured JSON data
2. **Human-Readable**: The output is optimized for human reading and LLM consumption
3. **Conditional Fields**: Some fields (Code Snippets, Trust Score, Versions) are only shown when available
4. **Separator Lines**: Results are separated by "----------" for clarity
5. **File Output**: When output_file is specified, the exact same text content is written to the file
6. **Error Preservation**: Even when file writing fails, the original content is still returned

This format ensures compatibility with MCP clients while providing clear, readable documentation and search results.