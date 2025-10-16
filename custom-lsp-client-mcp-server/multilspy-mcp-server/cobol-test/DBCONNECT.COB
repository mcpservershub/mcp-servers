       IDENTIFICATION DIVISION.
       PROGRAM-ID. DBCONNECT.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * DATABASE CONNECTION MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-DB-HOST               PIC X(50) VALUE 'localhost'.
       01  WS-DB-PORT               PIC 9(5) VALUE 5432.
       01  WS-DB-NAME               PIC X(30) VALUE 'banking_db'.
       01  WS-CONNECTION-STATUS     PIC X(20).

       PROCEDURE DIVISION.
       CONNECT-MAIN.
           PERFORM ESTABLISH-CONNECTION
           PERFORM VERIFY-CONNECTION
           PERFORM LOG-CONNECTION
           GOBACK.

       ESTABLISH-CONNECTION.
           DISPLAY "Connecting to database..."
           DISPLAY "Host: " WS-DB-HOST
           DISPLAY "Database: " WS-DB-NAME

           MOVE "CONNECTED" TO WS-CONNECTION-STATUS
           CALL 'LOGGER' USING BY CONTENT "DB connection established"
           MOVE 0 TO RETURN-CODE.

       VERIFY-CONNECTION.
           IF WS-CONNECTION-STATUS = "CONNECTED"
               DISPLAY "Connection verified"
               CALL 'LOGGER' USING BY CONTENT "Connection OK"
           ELSE
               DISPLAY "Connection failed"
               CALL 'ERRHANDL' USING BY CONTENT 10
               MOVE 10 TO RETURN-CODE
           END-IF.

       LOG-CONNECTION.
           CALL 'AUDITLOG' USING BY CONTENT 0
           CALL 'LOGGER' USING BY CONTENT "Connection logged".
