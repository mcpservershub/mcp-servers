       IDENTIFICATION DIVISION.
       PROGRAM-ID. ERRHANDL.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * ERROR HANDLING MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-ERROR-MESSAGE         PIC X(100).
       01  WS-ERROR-SEVERITY        PIC X(10).

       LINKAGE SECTION.
       01  LS-ERROR-CODE            PIC 99.

       PROCEDURE DIVISION USING LS-ERROR-CODE.
       ERROR-MAIN.
           PERFORM DETERMINE-ERROR-MESSAGE
           PERFORM LOG-ERROR
           PERFORM NOTIFY-ADMINISTRATOR
           GOBACK.

       DETERMINE-ERROR-MESSAGE.
           EVALUATE LS-ERROR-CODE
               WHEN 1
                   MOVE "Validation error" TO WS-ERROR-MESSAGE
                   MOVE "WARNING" TO WS-ERROR-SEVERITY
               WHEN 2
                   MOVE "Record not found" TO WS-ERROR-MESSAGE
                   MOVE "ERROR" TO WS-ERROR-SEVERITY
               WHEN 3
                   MOVE "Insufficient funds" TO WS-ERROR-MESSAGE
                   MOVE "WARNING" TO WS-ERROR-SEVERITY
               WHEN 10
                   MOVE "Database connection failed" TO WS-ERROR-MESSAGE
                   MOVE "CRITICAL" TO WS-ERROR-SEVERITY
               WHEN OTHER
                   MOVE "Unknown error" TO WS-ERROR-MESSAGE
                   MOVE "ERROR" TO WS-ERROR-SEVERITY
           END-EVALUATE

           DISPLAY "ERROR [" LS-ERROR-CODE "]: " WS-ERROR-MESSAGE.

       LOG-ERROR.
           CALL 'LOGGER' USING BY CONTENT WS-ERROR-MESSAGE
           CALL 'AUDITLOG' USING LS-ERROR-CODE

           IF RETURN-CODE NOT = 0
               DISPLAY "Critical: Unable to log error"
           END-IF.

       NOTIFY-ADMINISTRATOR.
           IF WS-ERROR-SEVERITY = "CRITICAL"
               CALL 'NOTIFIER' USING LS-ERROR-CODE
               CALL 'REPTGEN' USING LS-ERROR-CODE
           END-IF.
