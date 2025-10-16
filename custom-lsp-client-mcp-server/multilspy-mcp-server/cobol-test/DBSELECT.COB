       IDENTIFICATION DIVISION.
       PROGRAM-ID. DBSELECT.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * DATABASE SELECT/READ MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-QUERY-STATUS          PIC 9 VALUE 0.
       01  WS-RECORD-FOUND          PIC X VALUE 'N'.

       LINKAGE SECTION.
       01  LS-RECORD-ID             PIC 9(10).

       PROCEDURE DIVISION USING LS-RECORD-ID.
       SELECT-MAIN.
           PERFORM EXECUTE-SELECT
           PERFORM CHECK-RESULT
           GOBACK.

       EXECUTE-SELECT.
           DISPLAY "Selecting record ID: " LS-RECORD-ID

           CALL 'LOGGER' USING BY CONTENT "SELECT query executed"

           MOVE 'Y' TO WS-RECORD-FOUND
           MOVE 0 TO RETURN-CODE.

       CHECK-RESULT.
           IF WS-RECORD-FOUND = 'Y'
               DISPLAY "Record found"
               CALL 'AUDITLOG' USING LS-RECORD-ID
               MOVE 0 TO RETURN-CODE
           ELSE
               DISPLAY "Record not found"
               CALL 'ERRHANDL' USING BY CONTENT 2
               MOVE 2 TO RETURN-CODE
           END-IF.
