       IDENTIFICATION DIVISION.
       PROGRAM-ID. REPTGEN.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * REPORT GENERATION MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-REPORT-ID             PIC 9(10).
       01  WS-REPORT-TYPE           PIC X(20).
       01  WS-REPORT-NAME           PIC X(50).
       01  WS-RECORD-COUNT          PIC 9(6) VALUE 0.

       LINKAGE SECTION.
       01  LS-ENTITY-ID             PIC 9(10).

       PROCEDURE DIVISION USING LS-ENTITY-ID.
       REPORT-MAIN.
           PERFORM INITIALIZE-REPORT
           PERFORM GATHER-DATA
           PERFORM GENERATE-REPORT
           PERFORM SAVE-REPORT
           GOBACK.

       INITIALIZE-REPORT.
           DISPLAY "Generating report for entity " LS-ENTITY-ID
           MOVE "TRANSACTION_SUMMARY" TO WS-REPORT-TYPE
           CALL 'LOGGER' USING BY CONTENT "Report generation started".

       GATHER-DATA.
           CALL 'DBSELECT' USING LS-ENTITY-ID

           IF RETURN-CODE = 0
               ADD 1 TO WS-RECORD-COUNT
               DISPLAY "Data gathered: " WS-RECORD-COUNT " records"
               CALL 'AUDITLOG' USING LS-ENTITY-ID
           ELSE
               DISPLAY "No data found"
               CALL 'ERRHANDL' USING RETURN-CODE
           END-IF.

       GENERATE-REPORT.
           IF WS-RECORD-COUNT > 0
               DISPLAY "Generating report..."
               MOVE "Report_" TO WS-REPORT-NAME
               CALL 'VALIDATE' USING WS-REPORT-NAME

               IF RETURN-CODE = 0
                   DISPLAY "Report generated successfully"
                   CALL 'LOGGER' USING BY CONTENT "Report complete"
               ELSE
                   CALL 'ERRHANDL' USING RETURN-CODE
               END-IF
           ELSE
               DISPLAY "No data to report"
               MOVE 1 TO RETURN-CODE
           END-IF.

       SAVE-REPORT.
           IF WS-RECORD-COUNT > 0
               CALL 'DBINSERT' USING WS-REPORT-ID
                                     WS-REPORT-NAME
                                     WS-REPORT-TYPE

               IF RETURN-CODE = 0
                   DISPLAY "Report saved"
                   CALL 'NOTIFIER' USING LS-ENTITY-ID
               ELSE
                   CALL 'ERRHANDL' USING RETURN-CODE
               END-IF
           END-IF.
