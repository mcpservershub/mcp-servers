       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTMGMT.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * CUSTOMER MANAGEMENT MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-OPERATION             PIC 9.
       01  WS-CUSTOMER-ID           PIC 9(8).
       01  WS-CUSTOMER-NAME         PIC X(50).
       01  WS-CUSTOMER-ADDRESS      PIC X(100).
       01  WS-VALIDATION-STATUS     PIC 9.

       PROCEDURE DIVISION.
       CUSTOMER-MAIN.
           PERFORM DISPLAY-CUSTOMER-MENU
           PERFORM PROCESS-CUSTOMER-OPERATION
           GOBACK.

       DISPLAY-CUSTOMER-MENU.
           DISPLAY "CUSTOMER MANAGEMENT"
           DISPLAY "1. Add Customer"
           DISPLAY "2. Update Customer"
           DISPLAY "3. Delete Customer"
           DISPLAY "4. View Customer"
           DISPLAY "Enter choice: "
           ACCEPT WS-OPERATION.

       PROCESS-CUSTOMER-OPERATION.
           EVALUATE WS-OPERATION
               WHEN 1
                   PERFORM ADD-NEW-CUSTOMER
               WHEN 2
                   PERFORM UPDATE-CUSTOMER-INFO
               WHEN 3
                   PERFORM DELETE-CUSTOMER-RECORD
               WHEN 4
                   PERFORM VIEW-CUSTOMER-DETAILS
               WHEN OTHER
                   MOVE 99 TO RETURN-CODE
           END-EVALUATE.

       ADD-NEW-CUSTOMER.
           DISPLAY "Enter customer name: "
           ACCEPT WS-CUSTOMER-NAME
           DISPLAY "Enter customer address: "
           ACCEPT WS-CUSTOMER-ADDRESS

           CALL 'VALIDATE' USING WS-CUSTOMER-NAME
           MOVE RETURN-CODE TO WS-VALIDATION-STATUS

           IF WS-VALIDATION-STATUS = 0
               CALL 'DBINSERT' USING WS-CUSTOMER-NAME
                                     WS-CUSTOMER-ADDRESS
               IF RETURN-CODE = 0
                   DISPLAY "Customer added successfully"
                   CALL 'LOGGER' USING BY CONTENT "Customer added"
                   CALL 'NOTIFIER' USING WS-CUSTOMER-ID
                   MOVE 0 TO RETURN-CODE
               ELSE
                   DISPLAY "Failed to add customer"
                   CALL 'ERRHANDL' USING RETURN-CODE
               END-IF
           ELSE
               DISPLAY "Validation failed"
               MOVE 1 TO RETURN-CODE
           END-IF.

       UPDATE-CUSTOMER-INFO.
           DISPLAY "Enter customer ID: "
           ACCEPT WS-CUSTOMER-ID

           CALL 'DBSELECT' USING WS-CUSTOMER-ID

           IF RETURN-CODE = 0
               DISPLAY "Enter new name: "
               ACCEPT WS-CUSTOMER-NAME
               DISPLAY "Enter new address: "
               ACCEPT WS-CUSTOMER-ADDRESS

               CALL 'VALIDATE' USING WS-CUSTOMER-NAME

               IF RETURN-CODE = 0
                   CALL 'DBUPDATE' USING WS-CUSTOMER-ID
                                         WS-CUSTOMER-NAME
                                         WS-CUSTOMER-ADDRESS
                   IF RETURN-CODE = 0
                       DISPLAY "Customer updated"
                       CALL 'AUDITLOG' USING WS-CUSTOMER-ID
                       CALL 'NOTIFIER' USING WS-CUSTOMER-ID
                   ELSE
                       CALL 'ERRHANDL' USING RETURN-CODE
                   END-IF
               END-IF
           ELSE
               DISPLAY "Customer not found"
               MOVE 2 TO RETURN-CODE
           END-IF.

       DELETE-CUSTOMER-RECORD.
           DISPLAY "Enter customer ID: "
           ACCEPT WS-CUSTOMER-ID

           CALL 'DBSELECT' USING WS-CUSTOMER-ID

           IF RETURN-CODE = 0
               DISPLAY "Confirm deletion (Y/N): "
               ACCEPT WS-OPERATION
               IF WS-OPERATION = 1
                   CALL 'DBDELETE' USING WS-CUSTOMER-ID
                   IF RETURN-CODE = 0
                       DISPLAY "Customer deleted"
                       CALL 'AUDITLOG' USING WS-CUSTOMER-ID
                   ELSE
                       CALL 'ERRHANDL' USING RETURN-CODE
                   END-IF
               END-IF
           ELSE
               DISPLAY "Customer not found"
           END-IF.

       VIEW-CUSTOMER-DETAILS.
           DISPLAY "Enter customer ID: "
           ACCEPT WS-CUSTOMER-ID

           CALL 'DBSELECT' USING WS-CUSTOMER-ID

           IF RETURN-CODE = 0
               CALL 'REPTGEN' USING WS-CUSTOMER-ID
           ELSE
               DISPLAY "Customer not found"
               MOVE 2 TO RETURN-CODE
           END-IF.
