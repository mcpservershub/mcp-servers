       IDENTIFICATION DIVISION.
       PROGRAM-ID. DBCLOSE.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * DATABASE DISCONNECTION MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-CONNECTION-STATUS     PIC X(20) VALUE 'CONNECTED'.

       PROCEDURE DIVISION.
       DISCONNECT-MAIN.
           PERFORM CLOSE-CONNECTION
           PERFORM VERIFY-CLOSURE
           PERFORM LOG-CLOSURE
           GOBACK.

       CLOSE-CONNECTION.
           DISPLAY "Closing database connection..."

           MOVE "DISCONNECTED" TO WS-CONNECTION-STATUS
           CALL 'LOGGER' USING BY CONTENT "DB connection closed"
           MOVE 0 TO RETURN-CODE.

       VERIFY-CLOSURE.
           IF WS-CONNECTION-STATUS = "DISCONNECTED"
               DISPLAY "Connection closed successfully"
               CALL 'LOGGER' USING BY CONTENT "Closure verified"
           ELSE
               DISPLAY "Warning: Connection may still be open"
               CALL 'ERRHANDL' USING BY CONTENT 11
           END-IF.

       LOG-CLOSURE.
           CALL 'AUDITLOG' USING BY CONTENT 0
           CALL 'LOGGER' USING BY CONTENT "Closure logged".
