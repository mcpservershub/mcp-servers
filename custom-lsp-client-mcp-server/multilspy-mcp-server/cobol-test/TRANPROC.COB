       IDENTIFICATION DIVISION.
       PROGRAM-ID. TRANPROC.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * TRANSACTION PROCESSING MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-TRANSACTION-ID        PIC 9(12).
       01  WS-TIMESTAMP             PIC X(20).
       01  WS-STATUS                PIC X(10).

       LINKAGE SECTION.
       01  LS-ACCOUNT-NUMBER        PIC 9(10).
       01  LS-AMOUNT                PIC 9(7)V99.

       PROCEDURE DIVISION USING LS-ACCOUNT-NUMBER LS-AMOUNT.
       TRANSACTION-MAIN.
           PERFORM VALIDATE-TRANSACTION
           PERFORM PROCESS-TRANSACTION
           PERFORM LOG-TRANSACTION
           GOBACK.

       VALIDATE-TRANSACTION.
           CALL 'VALIDATE' USING LS-AMOUNT

           IF RETURN-CODE NOT = 0
               DISPLAY "Transaction validation failed"
               CALL 'ERRHANDL' USING RETURN-CODE
               MOVE 1 TO RETURN-CODE
           ELSE
               CALL 'LOGGER' USING BY CONTENT "Transaction validated"
           END-IF.

       PROCESS-TRANSACTION.
           IF RETURN-CODE = 0
               CALL 'DBSELECT' USING LS-ACCOUNT-NUMBER

               IF RETURN-CODE = 0
                   CALL 'DBUPDATE' USING LS-ACCOUNT-NUMBER
                                         LS-AMOUNT

                   IF RETURN-CODE = 0
                       DISPLAY "Transaction processed"
                       MOVE "SUCCESS" TO WS-STATUS
                       CALL 'AUDITLOG' USING LS-ACCOUNT-NUMBER
                   ELSE
                       DISPLAY "Transaction failed"
                       MOVE "FAILED" TO WS-STATUS
                       CALL 'ERRHANDL' USING RETURN-CODE
                   END-IF
               ELSE
                   DISPLAY "Account not found"
                   MOVE "ERROR" TO WS-STATUS
                   CALL 'ERRHANDL' USING RETURN-CODE
               END-IF
           END-IF.

       LOG-TRANSACTION.
           CALL 'AUDITLOG' USING LS-ACCOUNT-NUMBER
           CALL 'LOGGER' USING BY CONTENT WS-STATUS

           IF WS-STATUS = "SUCCESS"
               CALL 'NOTIFIER' USING LS-ACCOUNT-NUMBER
               CALL 'REPTGEN' USING LS-ACCOUNT-NUMBER
           END-IF.
