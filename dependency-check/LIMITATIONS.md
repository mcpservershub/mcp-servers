# Dependency Check MCP Server Limitations

## Language Support

OWASP Dependency Check primarily analyzes **compiled artifacts** and **lock files**, not source code or dependency manifests alone.

### Fully Supported Languages (with artifacts):
- **Java/JVM**: JAR, WAR, EAR files (not just pom.xml)
- **.NET**: DLL, EXE assemblies
- **JavaScript/Node.js**: package-lock.json, yarn.lock (with RetireJS)
- **Ruby**: Gemfile.lock (with experimental flag)
- **Python**: Requirements.txt, wheel files (with experimental flag)

### Limited or No Support:
- **Go**: Go modules (go.mod/go.sum) are NOT natively supported by Dependency Check
- **PHP**: Limited support via Composer
- **Rust**: No native support for Cargo.toml/Cargo.lock

## Why Go Shows 0 Dependencies

Dependency Check does not have a native Go analyzer. The tool is designed to analyze:
1. Compiled binaries and packages
2. Lock files with exact versions
3. Known artifact formats

Go's `go.mod` and `go.sum` files are not recognized by Dependency Check's analyzers.

## Workarounds for Go Projects

1. **Use a dedicated Go security scanner** like:
   - `nancy` (Sonatype)
   - `gosec`
   - `govulncheck`

2. **Generate SBOMs** (Software Bill of Materials) in CycloneDX or SPDX format and scan those

3. **Use GitHub's dependency scanning** or other CI/CD security tools

## Output File Permissions

When running in a container, output files are created as root. To fix permissions:

```bash
# Run container with user mapping
docker run --user $(id -u):$(id -g) ...

# Or fix permissions after scan
sudo chown -R $USER:$USER ./output/
```

## Recommendations

1. For Go projects, consider using specialized Go security tools
2. For best results with Dependency Check, ensure you're scanning:
   - Compiled artifacts (JARs, DLLs, etc.)
   - Lock files (package-lock.json, Gemfile.lock)
   - Not just source code or manifest files

3. Enable experimental analyzers for broader language support:
   ```json
   {
     "enable_experimental": true
   }
   ```