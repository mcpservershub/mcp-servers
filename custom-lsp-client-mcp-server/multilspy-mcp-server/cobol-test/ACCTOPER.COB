       IDENTIFICATION DIVISION.
       PROGRAM-ID. ACCTOPER.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * ACCOUNT OPERATIONS MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-ACCOUNT-NUMBER        PIC 9(10).
       01  WS-ACCOUNT-TYPE          PIC X(10).
       01  WS-BALANCE               PIC 9(10)V99.
       01  WS-OPERATION             PIC 9.
       01  WS-AMOUNT                PIC 9(7)V99.

       LINKAGE SECTION.
       01  LS-ACCOUNT-NUMBER        PIC 9(10).

       PROCEDURE DIVISION USING LS-ACCOUNT-NUMBER.
       ACCOUNT-MAIN.
           MOVE LS-ACCOUNT-NUMBER TO WS-ACCOUNT-NUMBER
           PERFORM DISPLAY-ACCOUNT-MENU
           PERFORM PROCESS-ACCOUNT-OPERATION
           GOBACK.

       DISPLAY-ACCOUNT-MENU.
           DISPLAY "ACCOUNT OPERATIONS"
           DISPLAY "1. Open Account"
           DISPLAY "2. Close Account"
           DISPLAY "3. Check Balance"
           DISPLAY "4. Deposit"
           DISPLAY "5. Withdraw"
           DISPLAY "Enter choice: "
           ACCEPT WS-OPERATION.

       PROCESS-ACCOUNT-OPERATION.
           EVALUATE WS-OPERATION
               WHEN 1
                   PERFORM OPEN-NEW-ACCOUNT
               WHEN 2
                   PERFORM CLOSE-ACCOUNT
               WHEN 3
                   PERFORM CHECK-BALANCE
               WHEN 4
                   PERFORM DEPOSIT-FUNDS
               WHEN 5
                   PERFORM WITHDRAW-FUNDS
               WHEN OTHER
                   MOVE 99 TO RETURN-CODE
           END-EVALUATE.

       OPEN-NEW-ACCOUNT.
           DISPLAY "Enter account type (SAVINGS/CHECKING): "
           ACCEPT WS-ACCOUNT-TYPE

           CALL 'VALIDATE' USING WS-ACCOUNT-TYPE

           IF RETURN-CODE = 0
               CALL 'DBINSERT' USING WS-ACCOUNT-NUMBER
                                     WS-ACCOUNT-TYPE

               IF RETURN-CODE = 0
                   DISPLAY "Account opened successfully"
                   CALL 'AUDITLOG' USING WS-ACCOUNT-NUMBER
                   CALL 'NOTIFIER' USING WS-ACCOUNT-NUMBER
                   CALL 'REPTGEN' USING WS-ACCOUNT-NUMBER
                   MOVE 0 TO RETURN-CODE
               ELSE
                   CALL 'ERRHANDL' USING RETURN-CODE
               END-IF
           ELSE
               DISPLAY "Invalid account type"
               MOVE 1 TO RETURN-CODE
           END-IF.

       CLOSE-ACCOUNT.
           CALL 'DBSELECT' USING WS-ACCOUNT-NUMBER

           IF RETURN-CODE = 0
               CALL 'TRANPROC' USING WS-ACCOUNT-NUMBER
                                     WS-BALANCE

               IF RETURN-CODE = 0
                   CALL 'DBDELETE' USING WS-ACCOUNT-NUMBER
                   DISPLAY "Account closed"
                   CALL 'AUDITLOG' USING WS-ACCOUNT-NUMBER
               ELSE
                   CALL 'ERRHANDL' USING RETURN-CODE
               END-IF
           ELSE
               DISPLAY "Account not found"
           END-IF.

       CHECK-BALANCE.
           CALL 'DBSELECT' USING WS-ACCOUNT-NUMBER

           IF RETURN-CODE = 0
               DISPLAY "Current balance: " WS-BALANCE
               CALL 'LOGGER' USING BY CONTENT "Balance checked"
               MOVE 0 TO RETURN-CODE
           ELSE
               DISPLAY "Account not found"
               MOVE 2 TO RETURN-CODE
           END-IF.

       DEPOSIT-FUNDS.
           DISPLAY "Enter deposit amount: "
           ACCEPT WS-AMOUNT

           CALL 'VALIDATE' USING WS-AMOUNT

           IF RETURN-CODE = 0
               CALL 'TRANPROC' USING WS-ACCOUNT-NUMBER
                                     WS-AMOUNT

               IF RETURN-CODE = 0
                   DISPLAY "Deposit successful"
                   CALL 'AUDITLOG' USING WS-ACCOUNT-NUMBER
                   CALL 'NOTIFIER' USING WS-ACCOUNT-NUMBER
                   CALL 'REPTGEN' USING WS-ACCOUNT-NUMBER
               ELSE
                   CALL 'ERRHANDL' USING RETURN-CODE
               END-IF
           ELSE
               DISPLAY "Invalid amount"
           END-IF.

       WITHDRAW-FUNDS.
           DISPLAY "Enter withdrawal amount: "
           ACCEPT WS-AMOUNT

           CALL 'VALIDATE' USING WS-AMOUNT

           IF RETURN-CODE = 0
               CALL 'DBSELECT' USING WS-ACCOUNT-NUMBER

               IF RETURN-CODE = 0
                   IF WS-BALANCE >= WS-AMOUNT
                       CALL 'TRANPROC' USING WS-ACCOUNT-NUMBER
                                             WS-AMOUNT
                       IF RETURN-CODE = 0
                           DISPLAY "Withdrawal successful"
                           CALL 'AUDITLOG' USING WS-ACCOUNT-NUMBER
                           CALL 'NOTIFIER' USING WS-ACCOUNT-NUMBER
                       ELSE
                           CALL 'ERRHANDL' USING RETURN-CODE
                       END-IF
                   ELSE
                       DISPLAY "Insufficient funds"
                       MOVE 3 TO RETURN-CODE
                   END-IF
               END-IF
           ELSE
               DISPLAY "Invalid amount"
           END-IF.
