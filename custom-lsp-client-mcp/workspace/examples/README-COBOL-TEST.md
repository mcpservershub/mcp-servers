# COBOL Test Code for Universal CTags MCP Server

This directory contains sample COBOL programs to test the Universal CTags MCP Server functionality.

## File Structure

```
test-cobol/
├── CUSTOMER.COB          # Main customer management program
├── INVENTORY.COB         # Inventory management subprogram
├── UTILITIES.COB         # Common utility subroutines
├── copybooks/
│   ├── CUSTOMER-RECORD.CPY  # Customer record layout copybook
│   └── ERROR-CODES.CPY      # Error codes and messages copybook
└── README-COBOL-TEST.md     # This file
```

## COBOL Programs Description

### CUSTOMER.COB
- **Program-ID**: CUSTOMER-MGMT
- **Purpose**: Main program for customer management system
- **Key Features**:
  - Menu-driven interface
  - Customer CRUD operations
  - File I/O with sequential file organization
  - Multiple paragraphs and sections

### INVENTORY.COB
- **Program-ID**: INVENTORY-MGMT
- **Purpose**: Inventory management subprogram
- **Key Features**:
  - Indexed file organization
  - Dynamic access mode
  - Linkage section for parameter passing
  - Report generation functionality

### UTILITIES.COB
- **Program-ID**: UTILITIES
- **Purpose**: Common utility subroutines
- **Key Features**:
  - Date/time formatting
  - String manipulation functions
  - Data validation routines
  - Multiple utility functions via function codes

### Copybooks
- **CUSTOMER-RECORD.CPY**: Standard customer record layout with hierarchical structure
- **ERROR-CODES.CPY**: Application error codes and messages

## Testing with Universal CTags MCP Server

### Step 1: Build and Run the Container
```bash
# Build the container with Dockerfile.cgr
docker build -f Dockerfile.cgr -t ctags-mcp-server .

# Run the container with test-cobol directory mounted
docker run -it -p 3000:3000 -v $(pwd)/test-cobol:/workspace/cobol ctags-mcp-server
```

### Step 2: Generate CTags for COBOL Code
Use the MCP Inspector to call the `generate_tags` tool:
```json
{
  "name": "generate_tags",
  "arguments": {
    "paths": ["/workspace/cobol"],
    "output_file": "/workspace/cobol.tags",
    "languages": ["Cobol"],
    "recursive": true
  }
}
```

### Step 3: Test MCP Tools with COBOL Code

#### Test 1: Find Symbol (Program Names)
```json
{
  "name": "find_symbol",
  "arguments": {
    "symbol_name": "CUSTOMER-MGMT",
    "tags_file": "/workspace/cobol.tags"
  }
}
```

#### Test 2: List Symbols in File
```json
{
  "name": "list_symbols_in_file",
  "arguments": {
    "file_path": "/workspace/cobol/CUSTOMER.COB",
    "tags_file": "/workspace/cobol.tags"
  }
}
```

#### Test 3: Get File Outline
```json
{
  "name": "get_file_outline",
  "arguments": {
    "file_path": "/workspace/cobol/INVENTORY.COB",
    "tags_file": "/workspace/cobol.tags"
  }
}
```

#### Test 4: Find References (Paragraph Names)
```json
{
  "name": "find_references",
  "arguments": {
    "symbol_name": "DISPLAY-MENU",
    "tags_file": "/workspace/cobol.tags"
  }
}
```

#### Test 5: Go to Definition
```json
{
  "name": "go_to_definition",
  "arguments": {
    "symbol_name": "INITIALIZE-PROGRAM",
    "file_path": "/workspace/cobol/CUSTOMER.COB",
    "tags_file": "/workspace/cobol.tags"
  }
}
```

## Expected CTags Output

Universal CTags should identify these COBOL elements:
- **Programs**: CUSTOMER-MGMT, INVENTORY-MGMT, UTILITIES
- **Paragraphs**: MAIN-PROGRAM, DISPLAY-MENU, ADD-CUSTOMER, etc.
- **Data Items**: CUSTOMER-RECORD, WS-CUSTOMER-RECORD, etc.
- **File Definitions**: CUSTOMER-FILE, INVENTORY-FILE
- **Level Numbers**: 01, 05, 10 data structures
- **Copybooks**: CUSTOMER-RECORD, ERROR-CODES

## COBOL-Specific Testing Notes

1. **Case Sensitivity**: COBOL is typically case-insensitive, test both upper and lower case symbol searches
2. **Hyphenated Names**: Test symbols with hyphens like "CUSTOMER-MGMT"
3. **Hierarchical Data**: Test navigation through nested data structures
4. **Copybook Inclusion**: Verify copybook symbols are properly indexed
5. **Multiple Programs**: Test symbols across different program units

## Troubleshooting

- If CTags doesn't recognize COBOL files, ensure file extensions are `.COB`, `.CBL`, or `.cob`
- Some legacy COBOL features might not be fully supported by Universal CTags
- Verify that the `--languages=Cobol` parameter is working correctly