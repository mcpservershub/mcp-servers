# COBOL Banking System - Test Suite

This directory contains a comprehensive COBOL banking system with **extensive inter-program CALL relationships** to test CFG generation and call graph visualization.

## System Architecture

### Main Programs

1. **MAINPROG.COB** - Main orchestrator
   - Entry point for the banking system
   - Calls: DBCONNECT, LOGGER, CUSTMGMT, ACCTOPER, TRANPROC, REPTGEN, ERRHANDL, NOTIFIER, AUDITLOG, DBCLOSE

2. **CUSTMGMT.COB** - Customer management
   - Calls: VALIDATE, DBINSERT, LOGGER, NOTIFIER, DBSELECT, DBUPDATE, AUDITLOG, ERRHANDL, DBDELETE, REPTGEN

3. **ACCTOPER.COB** - Account operations
   - Calls: VALIDATE, DBINSERT, AUDITLOG, NOTIFIER, REPTGEN, ERRHANDL, DBSELECT, TRANPROC, DBDELETE, LOGGER

4. **TRANPROC.COB** - Transaction processing
   - Calls: VALIDATE, ERRHANDL, LOGGER, DBSELECT, DBUPDATE, AUDITLOG, NOTIFIER, REPTGEN

### Utility Modules

5. **VALIDATE.COB** - Data validation
   - Calls: LOGGER, ERRHANDL

6. **LOGGER.COB** - System logging
   - Calls: DBINSERT, ERRHANDL, DBSELECT

7. **ERRHANDL.COB** - Error handling
   - Calls: LOGGER, AUDITLOG, NOTIFIER, REPTGEN

8. **AUDITLOG.COB** - Audit logging
   - Calls: LOGGER, DBINSERT, ERRHANDL, DBSELECT, REPTGEN

9. **NOTIFIER.COB** - Notification service
   - Calls: LOGGER, DBSELECT, AUDITLOG, ERRHANDL, VALIDATE, DBINSERT

10. **REPTGEN.COB** - Report generation
    - Calls: LOGGER, DBSELECT, AUDITLOG, ERRHANDL, VALIDATE, DBINSERT, NOTIFIER

### Database Modules

11. **DBCONNECT.COB** - Database connection
    - Calls: LOGGER, ERRHANDL, AUDITLOG

12. **DBCLOSE.COB** - Database disconnection
    - Calls: LOGGER, ERRHANDL, AUDITLOG

13. **DBSELECT.COB** - Database SELECT operations
    - Calls: LOGGER, AUDITLOG, ERRHANDL

14. **DBINSERT.COB** - Database INSERT operations
    - Calls: VALIDATE, LOGGER, AUDITLOG, ERRHANDL

15. **DBUPDATE.COB** - Database UPDATE operations
    - Calls: DBSELECT, VALIDATE, LOGGER, AUDITLOG, ERRHANDL

16. **DBDELETE.COB** - Database DELETE operations
    - Calls: DBSELECT, LOGGER, AUDITLOG, NOTIFIER, ERRHANDL

## Call Graph Statistics

- **Total Programs**: 16
- **Programs with CALL statements**: 16 (100%)
- **Total CALL relationships**: 70+
- **Deepest call chain**: MAINPROG → ACCTOPER → TRANPROC → DBUPDATE → DBSELECT → AUDITLOG (6 levels)
- **Most called programs**: LOGGER (12 callers), ERRHANDL (11 callers), AUDITLOG (10 callers)

## Testing the CFG Tools

### Generate Individual CFGs
```python
cobol_generate_cfg_file(
    file_path="complete-cobol/MAINPROG.COB",
    output_format="dot",
    output_file="output/mainprog.dot"
)
```

### Generate Project-Wide CFG (Separate Files)
```python
cobol_generate_cfg_project(
    file_pattern="complete-cobol/**/*.COB",
    output_format="dot",
    output_dir="output/complete-cobol",
    generate_combined=False
)
```

### Generate Combined Call Graph
```python
cobol_generate_cfg_project(
    file_pattern="complete-cobol/**/*.COB",
    output_format="dot",
    output_dir="output/complete-cobol",
    generate_combined=True
)
```

## Expected Outputs

1. **Individual CFG files** - One .dot file per program showing internal control flow
2. **call_graph.json** - JSON file with all inter-program CALL relationships
3. **project_combined.dot** - Unified visualization showing:
   - All 16 programs as subgraph clusters
   - Internal PERFORM statements (dashed lines)
   - Inter-program CALL statements (bold red lines)
   - External programs not in project (yellow hexagons)

## Call Patterns to Observe

- **Utility Pattern**: Most programs call LOGGER, ERRHANDL, AUDITLOG
- **Database Pattern**: Business logic calls DB modules (DBSELECT, DBINSERT, DBUPDATE, DBDELETE)
- **Notification Pattern**: Successful operations trigger NOTIFIER
- **Validation Pattern**: Data operations call VALIDATE before execution
- **Report Pattern**: Completed operations call REPTGEN
