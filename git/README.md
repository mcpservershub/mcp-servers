# Git MCP Server

## Config to start up the server

```json
{
  "mcpServers": {
    "git": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--mount",
        "type=bind,src=/Users/username/Desktop,dst=/projects/Desktop",
        "--mount",
        "type=bind,src=/path/to/other/allowed/dir,dst=/projects/other/allowed/dir,ro",
        "santoshkal/git-mcp"
      ]
    }
  }
}
```

We need to mount the git directories we intend to work with for allowing access to MCP Server to
work upon the files within.

## Available Tools

1. `git_status`

   - Shows the working tree status
   - Input:
     - `repo_path` (string): Path to Git repository
   - Returns: Current status of working directory as text output

2. `git_diff_unstaged`

   - Shows changes in working directory not yet staged
   - Input:
     - `repo_path` (string): Path to Git repository
   - Returns: Diff output of unstaged changes

3. `git_diff_staged`

   - Shows changes that are staged for commit
   - Input:
     - `repo_path` (string): Path to Git repository
   - Returns: Diff output of staged changes

4. `git_diff`

   - Shows differences between branches or commits
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `target` (string): Target branch or commit to compare with
   - Returns: Diff output comparing current state with target

5. `git_commit`

   - Records changes to the repository
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `message` (string): Commit message
   - Returns: Confirmation with new commit hash

6. `git_add`

   - Adds file contents to the staging area
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `files` (string[]): Array of file paths to stage
   - Returns: Confirmation of staged files

7. `git_reset`

   - Unstages all staged changes
   - Input:
     - `repo_path` (string): Path to Git repository
   - Returns: Confirmation of reset operation

8. `git_log`

   - Shows the commit logs
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `max_count` (number, optional): Maximum number of commits to show (default: 10)
   - Returns: Array of commit entries with hash, author, date, and message

9. `git_create_branch`
   - Creates a new branch
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `branch_name` (string): Name of the new branch
     - `start_point` (string, optional): Starting point for the new branch
   - Returns: Confirmation of branch creation
10. `git_checkout`

- Switches branches
- Inputs:
  - `repo_path` (string): Path to Git repository
  - `branch_name` (string): Name of branch to checkout
- Returns: Confirmation of branch switch

11. `git_show`

- Shows the contents of a commit
- Inputs:
  - `repo_path` (string): Path to Git repository
  - `revision` (string): The revision (commit hash, branch name, tag) to show
- Returns: Contents of the specified commit

12. `git_init`

- Initializes a Git repository
- Inputs:
  - `repo_path` (string): Path to directory to initialize git repo
- Returns: Confirmation of repository initialization
