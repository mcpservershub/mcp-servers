       IDENTIFICATION DIVISION.
       PROGRAM-ID. LOGGER.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * SYSTEM LOGGING UTILITY MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-LOG-FILE              PIC X(50) VALUE 'system.log'.
       01  WS-TIMESTAMP             PIC X(20).
       01  WS-LOG-LEVEL             PIC X(10) VALUE 'INFO'.

       LINKAGE SECTION.
       01  LS-MESSAGE               PIC X(200).

       PROCEDURE DIVISION USING LS-MESSAGE.
       LOGGER-MAIN.
           PERFORM GET-TIMESTAMP
           PERFORM WRITE-LOG-ENTRY
           PERFORM CHECK-LOG-SIZE
           GOBACK.

       GET-TIMESTAMP.
           ACCEPT WS-TIMESTAMP FROM TIME
           DISPLAY "LOG [" WS-TIMESTAMP "]: " LS-MESSAGE.

       WRITE-LOG-ENTRY.
           CALL 'DBINSERT' USING WS-TIMESTAMP
                                 LS-MESSAGE

           IF RETURN-CODE NOT = 0
               DISPLAY "Warning: Log write failed"
               CALL 'ERRHANDL' USING RETURN-CODE
           END-IF.

       CHECK-LOG-SIZE.
           CALL 'DBSELECT' USING WS-LOG-FILE

           IF RETURN-CODE = 0
               DISPLAY "Log size checked"
           END-IF.
