       IDENTIFICATION DIVISION.
       PROGRAM-ID. DBDELETE.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * DATABASE DELETE MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-DELETE-STATUS         PIC 9 VALUE 0.

       LINKAGE SECTION.
       01  LS-RECORD-ID             PIC 9(10).

       PROCEDURE DIVISION USING LS-RECORD-ID.
       DELETE-MAIN.
           PERFORM CHECK-RECORD-EXISTS
           PERFORM EXECUTE-DELETE
           PERFORM VERIFY-DELETE
           GOBACK.

       CHECK-RECORD-EXISTS.
           CALL 'DBSELECT' USING LS-RECORD-ID

           IF RETURN-CODE NOT = 0
               DISPLAY "Record not found"
               CALL 'ERRHANDL' USING RETURN-CODE
           ELSE
               CALL 'LOGGER' USING BY CONTENT "Record exists"
               CALL 'AUDITLOG' USING LS-RECORD-ID
           END-IF.

       EXECUTE-DELETE.
           IF RETURN-CODE = 0
               DISPLAY "Deleting record..."
               CALL 'LOGGER' USING BY CONTENT "DELETE executed"
               MOVE 0 TO WS-DELETE-STATUS
               MOVE 0 TO RETURN-CODE
           END-IF.

       VERIFY-DELETE.
           IF WS-DELETE-STATUS = 0
               DISPLAY "Delete successful"
               CALL 'AUDITLOG' USING LS-RECORD-ID
               CALL 'NOTIFIER' USING LS-RECORD-ID
               MOVE 0 TO RETURN-CODE
           ELSE
               DISPLAY "Delete failed"
               CALL 'ERRHANDL' USING WS-DELETE-STATUS
               MOVE WS-DELETE-STATUS TO RETURN-CODE
           END-IF.
