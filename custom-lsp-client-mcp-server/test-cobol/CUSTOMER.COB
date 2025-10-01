      ******************************************************************
      * CUSTOMER MANAGEMENT SYSTEM - MAIN PROGRAM
      * Author: Test User
      * Date: 2025-01-25
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTOMER-MGMT.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO "CUSTOMER.DAT"
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  CUSTOMER-FILE.
       01  CUSTOMER-RECORD.
           05 CUSTOMER-ID         PIC 9(6).
           05 CUSTOMER-NAME       PIC X(30).
           05 CUSTOMER-ADDRESS    PIC X(50).
           05 CUSTOMER-PHONE      PIC X(15).
           05 CUSTOMER-BALANCE    PIC 9(8)V99.

       WORKING-STORAGE SECTION.
       01  WS-CUSTOMER-RECORD.
           05 WS-CUSTOMER-ID      PIC 9(6).
           05 WS-CUSTOMER-NAME    PIC X(30).
           05 WS-CUSTOMER-ADDRESS PIC X(50).
           05 WS-CUSTOMER-PHONE   PIC X(15).
           05 WS-CUSTOMER-BALANCE PIC 9(8)V99.

       01  WS-EOF-FLAG            PIC X VALUE 'N'.
           88 EOF-REACHED         VALUE 'Y'.

       01  WS-MENU-CHOICE         PIC 9.

       01  WS-MESSAGES.
           05 WS-WELCOME-MSG      PIC X(50) VALUE
              'Welcome to Customer Management System'.
           05 WS-MENU-HEADER      PIC X(40) VALUE
              'Customer Management Menu:'.
           05 WS-GOODBYE-MSG      PIC X(30) VALUE
              'Thank you for using our system!'.

       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           PERFORM INITIALIZE-PROGRAM
           PERFORM DISPLAY-MENU
           PERFORM PROCESS-MENU-CHOICE
           PERFORM CLEANUP-PROGRAM
           STOP RUN.

       INITIALIZE-PROGRAM.
           DISPLAY WS-WELCOME-MSG
           OPEN INPUT CUSTOMER-FILE.

       DISPLAY-MENU.
           DISPLAY ' '
           DISPLAY WS-MENU-HEADER
           DISPLAY '1. Add Customer'
           DISPLAY '2. Display All Customers'
           DISPLAY '3. Search Customer'
           DISPLAY '4. Update Customer'
           DISPLAY '5. Delete Customer'
           DISPLAY '6. Exit'
           DISPLAY 'Enter your choice: ' WITH NO ADVANCING
           ACCEPT WS-MENU-CHOICE.

       PROCESS-MENU-CHOICE.
           EVALUATE WS-MENU-CHOICE
               WHEN 1
                   PERFORM ADD-CUSTOMER
               WHEN 2
                   PERFORM DISPLAY-ALL-CUSTOMERS
               WHEN 3
                   PERFORM SEARCH-CUSTOMER
               WHEN 4
                   PERFORM UPDATE-CUSTOMER
               WHEN 5
                   PERFORM DELETE-CUSTOMER
               WHEN 6
                   PERFORM EXIT-PROGRAM
               WHEN OTHER
                   DISPLAY 'Invalid choice. Please try again.'
                   PERFORM DISPLAY-MENU
                   PERFORM PROCESS-MENU-CHOICE
           END-EVALUATE.

       ADD-CUSTOMER.
           DISPLAY 'Adding new customer...'
           DISPLAY 'Enter Customer ID: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-ID
           DISPLAY 'Enter Customer Name: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-NAME
           DISPLAY 'Enter Customer Address: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-ADDRESS
           DISPLAY 'Enter Customer Phone: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-PHONE
           DISPLAY 'Enter Customer Balance: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-BALANCE
           PERFORM SAVE-CUSTOMER-RECORD
           DISPLAY 'Customer added successfully!'.

       DISPLAY-ALL-CUSTOMERS.
           DISPLAY 'Displaying all customers...'
           PERFORM READ-ALL-CUSTOMERS.

       SEARCH-CUSTOMER.
           DISPLAY 'Enter Customer ID to search: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-ID
           PERFORM FIND-CUSTOMER-BY-ID
           IF CUSTOMER-FOUND
               PERFORM DISPLAY-CUSTOMER-DETAILS
           ELSE
               DISPLAY 'Customer not found!'
           END-IF.

       UPDATE-CUSTOMER.
           DISPLAY 'Enter Customer ID to update: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-ID
           PERFORM FIND-CUSTOMER-BY-ID
           IF CUSTOMER-FOUND
               PERFORM GET-UPDATED-INFO
               PERFORM SAVE-CUSTOMER-RECORD
               DISPLAY 'Customer updated successfully!'
           ELSE
               DISPLAY 'Customer not found!'
           END-IF.

       DELETE-CUSTOMER.
           DISPLAY 'Enter Customer ID to delete: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-ID
           PERFORM REMOVE-CUSTOMER-RECORD
           DISPLAY 'Customer deleted successfully!'.

       SAVE-CUSTOMER-RECORD.
           MOVE WS-CUSTOMER-ID TO CUSTOMER-ID
           MOVE WS-CUSTOMER-NAME TO CUSTOMER-NAME
           MOVE WS-CUSTOMER-ADDRESS TO CUSTOMER-ADDRESS
           MOVE WS-CUSTOMER-PHONE TO CUSTOMER-PHONE
           MOVE WS-CUSTOMER-BALANCE TO CUSTOMER-BALANCE
           WRITE CUSTOMER-RECORD.

       READ-ALL-CUSTOMERS.
           MOVE 'N' TO WS-EOF-FLAG
           PERFORM UNTIL EOF-REACHED
               READ CUSTOMER-FILE
                   AT END
                       SET EOF-REACHED TO TRUE
                   NOT AT END
                       PERFORM DISPLAY-CUSTOMER-DETAILS
               END-READ
           END-PERFORM.

       FIND-CUSTOMER-BY-ID.
      * Implementation for finding customer by ID
           CONTINUE.

       DISPLAY-CUSTOMER-DETAILS.
           DISPLAY 'Customer ID: ' CUSTOMER-ID
           DISPLAY 'Name: ' CUSTOMER-NAME
           DISPLAY 'Address: ' CUSTOMER-ADDRESS
           DISPLAY 'Phone: ' CUSTOMER-PHONE
           DISPLAY 'Balance: ' CUSTOMER-BALANCE
           DISPLAY ' '.

       GET-UPDATED-INFO.
           DISPLAY 'Enter new Customer Name: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-NAME
           DISPLAY 'Enter new Customer Address: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-ADDRESS
           DISPLAY 'Enter new Customer Phone: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-PHONE
           DISPLAY 'Enter new Customer Balance: ' WITH NO ADVANCING
           ACCEPT WS-CUSTOMER-BALANCE.

       REMOVE-CUSTOMER-RECORD.
      * Implementation for removing customer record
           CONTINUE.

       CLEANUP-PROGRAM.
           CLOSE CUSTOMER-FILE
           DISPLAY WS-GOODBYE-MSG.

       EXIT-PROGRAM.
           PERFORM CLEANUP-PROGRAM
           STOP RUN.

      * Additional utility paragraphs
       CUSTOMER-FOUND.
           IF CUSTOMER-ID = WS-CUSTOMER-ID
               CONTINUE
           ELSE
               CONTINUE
           END-IF.