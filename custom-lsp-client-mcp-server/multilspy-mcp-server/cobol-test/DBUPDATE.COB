       IDENTIFICATION DIVISION.
       PROGRAM-ID. DBUPDATE.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * DATABASE UPDATE MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-UPDATE-STATUS         PIC 9 VALUE 0.

       LINKAGE SECTION.
       01  LS-RECORD-ID             PIC 9(10).
       01  LS-NEW-VALUE             PIC X(100).

       PROCEDURE DIVISION USING LS-RECORD-ID LS-NEW-VALUE.
       UPDATE-MAIN.
           PERFORM CHECK-RECORD-EXISTS
           PERFORM EXECUTE-UPDATE
           PERFORM VERIFY-UPDATE
           GOBACK.

       CHECK-RECORD-EXISTS.
           CALL 'DBSELECT' USING LS-RECORD-ID

           IF RETURN-CODE NOT = 0
               DISPLAY "Record not found"
               CALL 'ERRHANDL' USING RETURN-CODE
           ELSE
               CALL 'LOGGER' USING BY CONTENT "Record exists"
           END-IF.

       EXECUTE-UPDATE.
           IF RETURN-CODE = 0
               CALL 'VALIDATE' USING LS-NEW-VALUE

               IF RETURN-CODE = 0
                   DISPLAY "Updating record..."
                   CALL 'LOGGER' USING BY CONTENT "UPDATE executed"
                   MOVE 0 TO WS-UPDATE-STATUS
                   MOVE 0 TO RETURN-CODE
               ELSE
                   CALL 'ERRHANDL' USING RETURN-CODE
               END-IF
           END-IF.

       VERIFY-UPDATE.
           IF WS-UPDATE-STATUS = 0
               DISPLAY "Update successful"
               CALL 'AUDITLOG' USING LS-RECORD-ID
               MOVE 0 TO RETURN-CODE
           ELSE
               DISPLAY "Update failed"
               CALL 'ERRHANDL' USING WS-UPDATE-STATUS
               MOVE WS-UPDATE-STATUS TO RETURN-CODE
           END-IF.
