       IDENTIFICATION DIVISION.
       PROGRAM-ID. DBINSERT.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * DATABASE INSERT MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-INSERT-STATUS         PIC 9 VALUE 0.

       LINKAGE SECTION.
       01  LS-DATA-FIELD1           PIC X(100).
       01  LS-DATA-FIELD2           PIC X(100).

       PROCEDURE DIVISION USING LS-DATA-FIELD1 LS-DATA-FIELD2.
       INSERT-MAIN.
           PERFORM VALIDATE-DATA
           PERFORM EXECUTE-INSERT
           PERFORM VERIFY-INSERT
           GOBACK.

       VALIDATE-DATA.
           CALL 'VALIDATE' USING LS-DATA-FIELD1

           IF RETURN-CODE NOT = 0
               DISPLAY "Data validation failed"
               CALL 'ERRHANDL' USING RETURN-CODE
               MOVE 1 TO RETURN-CODE
           ELSE
               CALL 'LOGGER' USING BY CONTENT "Data validated"
           END-IF.

       EXECUTE-INSERT.
           IF RETURN-CODE = 0
               DISPLAY "Inserting data..."
               CALL 'LOGGER' USING BY CONTENT "INSERT executed"
               MOVE 0 TO WS-INSERT-STATUS
               MOVE 0 TO RETURN-CODE
           END-IF.

       VERIFY-INSERT.
           IF WS-INSERT-STATUS = 0
               DISPLAY "Insert successful"
               CALL 'AUDITLOG' USING BY CONTENT 0
               MOVE 0 TO RETURN-CODE
           ELSE
               DISPLAY "Insert failed"
               CALL 'ERRHANDL' USING WS-INSERT-STATUS
               MOVE WS-INSERT-STATUS TO RETURN-CODE
           END-IF.
