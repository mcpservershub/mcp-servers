       IDENTIFICATION DIVISION.
       PROGRAM-ID. MAINPROG.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * MAIN BANKING APPLICATION - ORCHESTRATES ALL OPERATIONS
      *****************************************************************

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-USER-CHOICE           PIC 9.
       01  WS-CUSTOMER-ID           PIC 9(8).
       01  WS-ACCOUNT-NUMBER        PIC 9(10).
       01  WS-TRANSACTION-AMOUNT    PIC 9(7)V99.
       01  WS-CONTINUE-FLAG         PIC X VALUE 'Y'.
       01  WS-RETURN-CODE           PIC 99.

       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           PERFORM INITIALIZE-SYSTEM
           PERFORM UNTIL WS-CONTINUE-FLAG = 'N'
               PERFORM DISPLAY-MAIN-MENU
               PERFORM PROCESS-USER-SELECTION
           END-PERFORM
           PERFORM CLEANUP-SYSTEM
           STOP RUN.

       INITIALIZE-SYSTEM.
           DISPLAY "==================================="
           DISPLAY "  BANKING SYSTEM v1.0"
           DISPLAY "==================================="
           CALL 'DBCONNECT'
           IF RETURN-CODE NOT = 0
               DISPLAY "ERROR: Database connection failed"
               MOVE 'N' TO WS-CONTINUE-FLAG
           ELSE
               CALL 'LOGGER' USING BY CONTENT "System initialized"
           END-IF.

       DISPLAY-MAIN-MENU.
           DISPLAY " "
           DISPLAY "MAIN MENU:"
           DISPLAY "1. Customer Management"
           DISPLAY "2. Account Operations"
           DISPLAY "3. Transaction Processing"
           DISPLAY "4. Reports"
           DISPLAY "5. Exit"
           DISPLAY "Enter choice (1-5): "
           ACCEPT WS-USER-CHOICE.

       PROCESS-USER-SELECTION.
           EVALUATE WS-USER-CHOICE
               WHEN 1
                   PERFORM HANDLE-CUSTOMER-OPS
               WHEN 2
                   PERFORM HANDLE-ACCOUNT-OPS
               WHEN 3
                   PERFORM HANDLE-TRANSACTIONS
               WHEN 4
                   PERFORM HANDLE-REPORTS
               WHEN 5
                   MOVE 'N' TO WS-CONTINUE-FLAG
               WHEN OTHER
                   DISPLAY "Invalid choice. Try again."
                   CALL 'LOGGER' USING BY CONTENT "Invalid menu choice"
           END-EVALUATE.

       HANDLE-CUSTOMER-OPS.
           DISPLAY "Customer Management Module"
           CALL 'CUSTMGMT'
           MOVE RETURN-CODE TO WS-RETURN-CODE
           IF WS-RETURN-CODE NOT = 0
               DISPLAY "Customer operation failed"
               CALL 'LOGGER' USING BY CONTENT "CUSTMGMT error"
           END-IF.

       HANDLE-ACCOUNT-OPS.
           DISPLAY "Account Operations Module"
           DISPLAY "Enter account number: "
           ACCEPT WS-ACCOUNT-NUMBER
           CALL 'ACCTOPER' USING WS-ACCOUNT-NUMBER
           MOVE RETURN-CODE TO WS-RETURN-CODE
           IF WS-RETURN-CODE = 0
               CALL 'LOGGER' USING BY CONTENT "Account op successful"
           ELSE
               CALL 'ERRHANDL' USING WS-RETURN-CODE
           END-IF.

       HANDLE-TRANSACTIONS.
           DISPLAY "Transaction Processing"
           DISPLAY "Enter account number: "
           ACCEPT WS-ACCOUNT-NUMBER
           DISPLAY "Enter transaction amount: "
           ACCEPT WS-TRANSACTION-AMOUNT
           CALL 'TRANPROC' USING WS-ACCOUNT-NUMBER
                                 WS-TRANSACTION-AMOUNT
           MOVE RETURN-CODE TO WS-RETURN-CODE
           IF WS-RETURN-CODE = 0
               CALL 'AUDITLOG' USING WS-ACCOUNT-NUMBER
               CALL 'NOTIFIER' USING WS-CUSTOMER-ID
           ELSE
               CALL 'ERRHANDL' USING WS-RETURN-CODE
           END-IF.

       HANDLE-REPORTS.
           DISPLAY "Report Generation"
           CALL 'REPTGEN'
           IF RETURN-CODE NOT = 0
               CALL 'ERRHANDL' USING RETURN-CODE
           END-IF.

       CLEANUP-SYSTEM.
           DISPLAY "Shutting down system..."
           CALL 'LOGGER' USING BY CONTENT "System shutdown"
           CALL 'DBCLOSE'
           DISPLAY "System shutdown complete.".
