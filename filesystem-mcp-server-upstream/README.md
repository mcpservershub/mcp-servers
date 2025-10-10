# MCP Filesystem Server

This MCP server provides secure access to the local filesystem via the Model Context Protocol (MCP).

## Components

### Tools

#### File Operations

- **read_file**

  - Read the complete contents of a file from the file system
  - Parameters: `path` (required): Path to the file to read

- **read_multiple_files**

  - Read the contents of multiple files in a single operation
  - Parameters: `paths` (required): List of file paths to read

- **write_file**

  - Create a new file or overwrite an existing file with new content
  - Parameters: `path` (required): Path where to write the file, `content` (required): Content to write to the file

- **copy_file**

  - Copy files and directories
  - Parameters: `source` (required): Source path of the file or directory, `destination` (required): Destination path

- **move_file**

  - Move or rename files and directories
  - Parameters: `source` (required): Source path of the file or directory, `destination` (required): Destination path

- **delete_file**

  - Delete a file or directory from the file system
  - Parameters: `path` (required): Path to the file or directory to delete, `recursive` (optional): Whether to recursively delete directories (default: false)

- **modify_file**
  - Update file by finding and replacing text using string matching or regex
  - Parameters: `path` (required): Path to the file to modify, `find` (required): Text to search for, `replace` (required): Text to replace with, `all_occurrences` (optional): Replace all occurrences (default: true), `regex` (optional): Treat find pattern as regex (default: false)

#### Directory Operations

- **list_directory**

  - Get a detailed listing of all files and directories in a specified path
  - Parameters: `path` (required): Path of the directory to list

- **create_directory**

  - Create a new directory or ensure a directory exists
  - Parameters: `path` (required): Path of the directory to create

- **tree**
  - Returns a hierarchical JSON representation of a directory structure
  - Parameters: `path` (required): Path of the directory to traverse, `depth` (optional): Maximum depth to traverse (default: 3), `follow_symlinks` (optional): Whether to follow symbolic links (default: false)

#### Search and Information

- **search_files**

  - Recursively search for files and directories matching a pattern
  - Parameters: `path` (required): Starting path for the search, `pattern` (required): Search pattern to match against file names

- **search_within_files**

  - Search for text within file contents across directory trees
  - Parameters: `path` (required): Starting directory for the search, `substring` (required): Text to search for within file contents, `depth` (optional): Maximum directory depth to search, `max_results` (optional): Maximum number of results to return (default: 1000)

- **get_file_info**

  - Retrieve detailed metadata about a file or directory
  - Parameters: `path` (required): Path to the file or directory

- **list_allowed_directories**
  - Returns the list of directories that this server is allowed to access
  - Parameters: None

## Features

- Secure access to specified directories
- Path validation to prevent directory traversal attacks
- Symlink resolution with security checks
- MIME type detection
- Support for text, binary, and image files
- Size limits for inline content and base64 encoding

## Config to start the Filesystem Server

We need to mount the directries we wish to work with as _allowed-directories_, so that MCP Server
has access to those files witin the directory. While starting up the container, it takes the path of
the allowed directories as an arg.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--volume=/allowed/directory/in/host:/allowed/directory/in/container",
        "santoshkal/filesystem-server",
        "/allowed/directory/in/container"
      ]
    }
  }
}
```

---
*Last updated: 2025-07-29 16:13:12 UTC*
