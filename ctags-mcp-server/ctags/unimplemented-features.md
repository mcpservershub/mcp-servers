# Unimplemented CTags Features

This document lists CTags features that are not yet implemented in the MCP Server but could be added in the future.

## ✅ Recently Implemented (High Priority)

These features have been implemented:

1. ✅ **Cross-Reference Output** (`-x`) - `generate_cross_reference` tool
2. ✅ **Language Detection** (`--print-language`) - `detect_file_language` tool
3. ✅ **List Supported Languages** (`--list-languages`) - `list_supported_languages` tool
4. ✅ **List Tag Kinds** (`--list-kinds-full`) - `list_language_kinds` tool
5. ✅ **Output Format Selection** (`--output-format`) - Added to `generate_tags` tool

---

## 🌟 Medium Priority Features (Useful)

### 1. **File List Input** (`-L <file>`)
**CTags Help Reference:** Lines 32-34

**Description:** Index only specific files listed in a text file.

**Use Case:** Useful for large projects where you want to cherry-pick specific files to index.

**Example Implementation:**
```python
@mcp.tool()
async def generate_tags_from_file_list(
    file_list_path: str,
    output_file: str = "tags",
    languages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate tags from a list of files specified in a text file.

    Args:
        file_list_path: Path to text file containing list of files (one per line)
        output_file: Output tags file path
        languages: Filter by languages
    """
```

**CTags Command:**
```bash
ctags -L files.txt -f tags
```

---

### 2. **Exclude Exceptions** (`--exclude-exception`)
**CTags Help Reference:** Lines 16-18

**Description:** Re-include specific files that match exclusion patterns.

**Use Case:** Exclude all JSON files except `config.json`.

**Example Implementation:**
```python
@mcp.tool()
async def generate_tags(
    path: str,
    exclude_patterns: Optional[List[str]] = None,
    exclude_exceptions: Optional[List[str]] = None  # NEW PARAMETER
) -> Dict[str, Any]:
```

**CTags Command:**
```bash
ctags -R --exclude='*.json' --exclude-exception='config.json' .
```

---

### 3. **Encoding Support** (`--input-encoding`, `--output-encoding`)
**CTags Help Reference:** Lines 55-61

**Description:** Handle files with different character encodings.

**Use Case:** Legacy COBOL files often use ISO-8859-1 or EBCDIC encodings.

**Example Implementation:**
```python
@mcp.tool()
async def generate_tags(
    path: str,
    input_encoding: str = "UTF-8",  # NEW PARAMETER
    output_encoding: str = "UTF-8"  # NEW PARAMETER
) -> Dict[str, Any]:
```

**CTags Command:**
```bash
ctags -R --input-encoding=ISO-8859-1 --output-encoding=UTF-8 .
```

---

### 4. **Symbolic Link Following** (`--links`)
**CTags Help Reference:** Lines 25-26

**Description:** Control whether symbolic links should be followed during recursive scanning.

**Use Case:** Projects with symlinked directories.

**Example Implementation:**
```python
@mcp.tool()
async def generate_tags(
    path: str,
    follow_symlinks: bool = True  # NEW PARAMETER
) -> Dict[str, Any]:
```

**CTags Command:**
```bash
ctags -R --links=yes .
# or
ctags -R --links=no .
```

---

### 5. **Verbose Mode and Statistics** (`--verbose`, `--totals`)
**CTags Help Reference:** Lines 224-227

**Description:** Get detailed statistics about tag generation.

**Use Case:** Understand how many files/tags were processed, debug issues.

**Example Output:**
```json
{
  "success": true,
  "tags_file": "./tags",
  "statistics": {
    "files_scanned": 150,
    "tags_generated": 5432,
    "languages_detected": ["COBOL", "Python", "JavaScript"],
    "processing_time": "2.5s"
  }
}
```

**CTags Command:**
```bash
ctags -R --totals=extra .
```

---

### 6. **Tag Relative Paths** (`--tag-relative`)
**CTags Help Reference:** Lines 116-119

**Description:** Store file paths relative to tags file location.

**Use Case:** Makes tags files portable across different machines/directories.

**Example Implementation:**
```python
@mcp.tool()
async def generate_tags(
    path: str,
    tag_relative: str = "no"  # NEW PARAMETER: "yes", "no", "always", "never"
) -> Dict[str, Any]:
```

**CTags Command:**
```bash
ctags -R --tag-relative=yes .
```

---

## 💎 Low Priority Features (Advanced)

### 7. **Tag Roles** (`--roles-<LANG>`)
**CTags Help Reference:** Lines 114-115

**Description:** Track HOW symbols are used (defined, referenced, called, etc.).

**Use Case:** Advanced reference tracking - distinguish between where a function is defined vs. where it's called.

**Complexity:** High - requires understanding CTags role system.

---

### 8. **Custom Regex Parsers** (`--regex-<LANG>`, `--mline-regex-<LANG>`)
**CTags Help Reference:** Lines 136-139

**Description:** Define custom patterns to find tags in unsupported or custom languages.

**Use Case:** Support domain-specific languages (DSLs) or custom file formats.

**Example:**
```bash
ctags --regex-MyLang='/^function\s+(\w+)/\1/f/' .
```

**Complexity:** Very High - requires regex expertise and understanding of CTags parser system.

---

### 9. **Custom Language Definition** (`--langdef`)
**CTags Help Reference:** Lines 132-139

**Description:** Define entirely new languages with custom parsing rules.

**Use Case:** Create parsers for proprietary or uncommon languages.

**Complexity:** Very High - essentially creating a new language parser.

---

### 10. **Language-Specific Parameters** (`--param-<LANG>`)
**CTags Help Reference:** Lines 154-155

**Description:** Set language-specific parameters for parsing.

**Use Case:** Fine-tune how CTags parses specific languages.

**Example:**
```bash
ctags --param-Python.kinds=+i .
```

---

### 11. **Kind Filtering** (`--kinds-<LANG>`)
**CTags Help Reference:** Lines 104-105

**Description:** Only generate tags for specific kinds of symbols.

**Use Case:** Only index functions, skip variables to reduce tags file size.

**Example Implementation:**
```python
@mcp.tool()
async def generate_tags(
    path: str,
    kind_filter: Optional[Dict[str, List[str]]] = None  # NEW PARAMETER
    # Example: {"Python": ["function", "class"], "COBOL": ["paragraph"]}
) -> Dict[str, Any]:
```

**CTags Command:**
```bash
ctags -R --kinds-Python=+fc --kinds-COBOL=+p .
```

---

### 12. **Extras and Fields Customization** (`--extras`, `--fields`)
**CTags Help Reference:** Lines 94-103

**Description:** Control what extra information is included in tags.

**Use Case:** Include/exclude specific metadata like line numbers, signatures, scopes.

**Example:**
```bash
ctags -R --fields=+n+S+K --extras=+q .
```

---

### 13. **Describe Language Parser** (`--describe-language`)
**CTags Help Reference:** Lines 210-211

**Description:** Get detailed information about how CTags parses a language.

**Use Case:** Debug or understand parser behavior.

**Example Implementation:**
```python
@mcp.tool()
async def describe_language_parser(
    language: str
) -> Dict[str, Any]:
    """
    Get detailed information about how CTags parses a specific language.
    """
```

---

### 14. **Filter Mode** (`--filter`)
**CTags Help Reference:** Lines 19-24

**Description:** Behave as a Unix filter, reading filenames from stdin.

**Use Case:** Integration with Unix pipelines.

**Complexity:** Medium - requires handling stdin/stdout streams.

---

### 15. **Different Tag File Formats** (`--format`)
**CTags Help Reference:** Lines 44-47

**Description:** Generate tags in format 1 vs format 2.

**Use Case:** Compatibility with older editors.

---

## 📊 Summary

### Implemented (5 features)
- ✅ Cross-reference output
- ✅ Language detection
- ✅ List supported languages
- ✅ List tag kinds per language
- ✅ Output format selection

### Not Implemented (15 features)
- **Medium Priority (6):** File list input, exclude exceptions, encoding support, symlink handling, statistics, relative paths
- **Low Priority (9):** Tag roles, custom parsers, language definitions, parameters, kind filtering, extras/fields, describe language, filter mode, format selection

### Recommendation for Next Implementation

If you want to add more features, implement in this order:

1. **Statistics/Verbose mode** - Very useful for debugging
2. **File list input** - Practical for selective indexing
3. **Exclude exceptions** - Completes the exclusion feature set
4. **Encoding support** - Important for legacy codebases
5. **Relative paths** - Makes tags files portable

---

## Notes

- Most of these features involve adding parameters to existing tools rather than creating entirely new tools
- The "High Priority" features have already been implemented
- "Medium Priority" features are practical and commonly used
- "Low Priority" features are advanced and rarely needed for typical use cases
