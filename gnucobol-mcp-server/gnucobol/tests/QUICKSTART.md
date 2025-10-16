# GnuCOBOL MCP Server - Testing Quick Start

## 🚀 Get Started in 5 Minutes

### 1. Install Prerequisites (2 minutes)

```bash
# Install GnuCOBOL
sudo apt-get update && sudo apt-get install -y gnucobol

# Verify installation
cobc --version
```

### 2. Setup Python Environment (1 minute)

```bash
# From project root
cd /home/santosh/gnucobol

# Create virtual environment
python3.12 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Run Tests (2 minutes)

```bash
# Run all tests
pytest tests/test_gnucobol_mcp.py -v

# Expected output: ~30-40 tests pass in 15-30 seconds
```

## ✅ Quick Validation

### Test Individual COBOL Files

```bash
# Valid COBOL - should succeed
cobc -x tests/sample_cobol/valid/hello.cob
./hello

# Invalid COBOL - should fail with errors
cobc -fsyntax-only tests/sample_cobol/invalid/syntax_error.cob
```

### Test Specific Test Classes

```bash
# Test compilation only (fast)
pytest tests/test_gnucobol_mcp.py::TestCompileCobol -v

# Test syntax checking only
pytest tests/test_gnucobol_mcp.py::TestSyntaxCheck -v
```

## 🧪 Test MCP Server with Inspector

### 1. Install MCP Inspector

```bash
# Install Node.js if needed
node --version || curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Run inspector (no installation needed)
npx @modelcontextprotocol/inspector
```

### 2. Connect to Server

In the inspector web interface:
- **Command**: `/home/santosh/gnucobol/.venv/bin/python -m gnucobol_mcp`
- Click "Connect"

### 3. Test Tools

Try this in the inspector:

**Tool**: `compile_cobol`
**Input**:
```json
{
  "source_code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. TEST.\n       PROCEDURE DIVISION.\n           DISPLAY \"Works!\".\n           STOP RUN."
}
```

## 📊 Test Coverage

```bash
# Generate coverage report
pytest tests/test_gnucobol_mcp.py --cov=gnucobol_mcp --cov-report=html

# View report
open htmlcov/index.html
```

## 🐛 Troubleshooting

### Tests fail: "cobc: command not found"
→ Install GnuCOBOL: `sudo apt-get install gnucobol`

### Tests fail: "No module named 'pytest'"
→ Install dev dependencies: `pip install -e ".[dev]"`

### Tests timeout
→ Normal on first run; subsequent runs will be faster

## 📚 Next Steps

1. ✅ Read [tests/README.md](./README.md) for detailed documentation
2. ✅ Review [MCP_INSPECTOR_GUIDE.md](./MCP_INSPECTOR_GUIDE.md) for Inspector testing
3. ✅ Explore sample COBOL files in `tests/sample_cobol/`
4. ✅ Run `pytest -v` to see all test details

## 🎯 Success Criteria

You're ready to proceed if:
- ✅ All pytest tests pass
- ✅ `cobc --version` shows GnuCOBOL installed
- ✅ Sample COBOL files compile successfully
- ✅ MCP Inspector can connect to server

---

**Time to completion: ~5 minutes**
