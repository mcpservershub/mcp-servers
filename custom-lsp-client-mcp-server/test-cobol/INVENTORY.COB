      ******************************************************************
      * INVENTORY MANAGEMENT SYSTEM - SUBPROGRAM
      * Author: Test User
      * Date: 2025-01-25
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. INVENTORY-MGMT.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT INVENTORY-FILE ASSIGN TO "INVENTORY.DAT"
               ORGANIZATION IS INDEXED
               ACCESS MODE IS DYNAMIC
               RECORD KEY IS ITEM-ID.

       DATA DIVISION.
       FILE SECTION.
       FD  INVENTORY-FILE.
       01  INVENTORY-RECORD.
           05 ITEM-ID             PIC 9(8).
           05 ITEM-NAME           PIC X(40).
           05 ITEM-CATEGORY       PIC X(20).
           05 QUANTITY-ON-HAND    PIC 9(6).
           05 UNIT-PRICE          PIC 9(6)V99.
           05 REORDER-LEVEL       PIC 9(4).
           05 SUPPLIER-CODE       PIC X(10).

       WORKING-STORAGE SECTION.
       01  WS-INVENTORY-RECORD.
           05 WS-ITEM-ID          PIC 9(8).
           05 WS-ITEM-NAME        PIC X(40).
           05 WS-ITEM-CATEGORY    PIC X(20).
           05 WS-QUANTITY-ON-HAND PIC 9(6).
           05 WS-UNIT-PRICE       PIC 9(6)V99.
           05 WS-REORDER-LEVEL    PIC 9(4).
           05 WS-SUPPLIER-CODE    PIC X(10).

       01  WS-INVENTORY-STATUS    PIC XX.
           88 RECORD-FOUND        VALUE "00".
           88 RECORD-NOT-FOUND    VALUE "23".

       01  WS-CALCULATIONS.
           05 WS-TOTAL-VALUE      PIC 9(10)V99.
           05 WS-ITEM-VALUE       PIC 9(8)V99.
           05 WS-LOW-STOCK-COUNT  PIC 9(4) VALUE ZERO.

       01  WS-REPORT-TOTALS.
           05 WS-TOTAL-ITEMS      PIC 9(6) VALUE ZERO.
           05 WS-TOTAL-INVENTORY-VALUE PIC 9(12)V99 VALUE ZERO.

       LINKAGE SECTION.
       01  LS-FUNCTION-CODE       PIC X(2).
       01  LS-ITEM-DATA.
           05 LS-ITEM-ID          PIC 9(8).
           05 LS-ITEM-NAME        PIC X(40).
           05 LS-QUANTITY         PIC 9(6).
           05 LS-UNIT-PRICE       PIC 9(6)V99.

       PROCEDURE DIVISION USING LS-FUNCTION-CODE LS-ITEM-DATA.
       MAIN-INVENTORY-PROGRAM.
           PERFORM INITIALIZE-INVENTORY
           EVALUATE LS-FUNCTION-CODE
               WHEN "AD"
                   PERFORM ADD-INVENTORY-ITEM
               WHEN "UP"
                   PERFORM UPDATE-INVENTORY-ITEM
               WHEN "IN"
                   PERFORM INQUIRE-INVENTORY-ITEM
               WHEN "DE"
                   PERFORM DELETE-INVENTORY-ITEM
               WHEN "LS"
                   PERFORM LIST-LOW-STOCK-ITEMS
               WHEN "RP"
                   PERFORM GENERATE-INVENTORY-REPORT
               WHEN OTHER
                   DISPLAY "Invalid function code: " LS-FUNCTION-CODE
           END-EVALUATE
           PERFORM CLOSE-INVENTORY-FILES
           GOBACK.

       INITIALIZE-INVENTORY.
           OPEN I-O INVENTORY-FILE.

       ADD-INVENTORY-ITEM.
           MOVE LS-ITEM-ID TO WS-ITEM-ID
           MOVE LS-ITEM-NAME TO WS-ITEM-NAME
           MOVE LS-QUANTITY TO WS-QUANTITY-ON-HAND
           MOVE LS-UNIT-PRICE TO WS-UNIT-PRICE

           DISPLAY "Enter Item Category: " WITH NO ADVANCING
           ACCEPT WS-ITEM-CATEGORY
           DISPLAY "Enter Reorder Level: " WITH NO ADVANCING
           ACCEPT WS-REORDER-LEVEL
           DISPLAY "Enter Supplier Code: " WITH NO ADVANCING
           ACCEPT WS-SUPPLIER-CODE

           PERFORM WRITE-INVENTORY-RECORD
           DISPLAY "Item " WS-ITEM-ID " added successfully".

       UPDATE-INVENTORY-ITEM.
           MOVE LS-ITEM-ID TO ITEM-ID
           READ INVENTORY-FILE
               INVALID KEY
                   DISPLAY "Item " LS-ITEM-ID " not found"
               NOT INVALID KEY
                   IF LS-QUANTITY NOT = ZERO
                       ADD LS-QUANTITY TO QUANTITY-ON-HAND
                   END-IF
                   IF LS-UNIT-PRICE NOT = ZERO
                       MOVE LS-UNIT-PRICE TO UNIT-PRICE
                   END-IF
                   REWRITE INVENTORY-RECORD
                   DISPLAY "Item " LS-ITEM-ID " updated successfully"
           END-READ.

       INQUIRE-INVENTORY-ITEM.
           MOVE LS-ITEM-ID TO ITEM-ID
           READ INVENTORY-FILE
               INVALID KEY
                   DISPLAY "Item " LS-ITEM-ID " not found"
               NOT INVALID KEY
                   PERFORM DISPLAY-ITEM-DETAILS
           END-READ.

       DELETE-INVENTORY-ITEM.
           MOVE LS-ITEM-ID TO ITEM-ID
           READ INVENTORY-FILE
               INVALID KEY
                   DISPLAY "Item " LS-ITEM-ID " not found"
               NOT INVALID KEY
                   DELETE INVENTORY-FILE
                   DISPLAY "Item " LS-ITEM-ID " deleted successfully"
           END-READ.

       LIST-LOW-STOCK-ITEMS.
           DISPLAY "LOW STOCK REPORT"
           DISPLAY "=================="
           START INVENTORY-FILE KEY IS >= ITEM-ID
           PERFORM UNTIL WS-INVENTORY-STATUS NOT = "00"
               READ INVENTORY-FILE NEXT RECORD
                   AT END
                       MOVE "10" TO WS-INVENTORY-STATUS
                   NOT AT END
                       IF QUANTITY-ON-HAND <= REORDER-LEVEL
                           PERFORM DISPLAY-LOW-STOCK-ITEM
                           ADD 1 TO WS-LOW-STOCK-COUNT
                       END-IF
               END-READ
           END-PERFORM
           DISPLAY "Total low stock items: " WS-LOW-STOCK-COUNT.

       GENERATE-INVENTORY-REPORT.
           DISPLAY "INVENTORY VALUATION REPORT"
           DISPLAY "=========================="
           START INVENTORY-FILE KEY IS >= ITEM-ID
           PERFORM UNTIL WS-INVENTORY-STATUS NOT = "00"
               READ INVENTORY-FILE NEXT RECORD
                   AT END
                       MOVE "10" TO WS-INVENTORY-STATUS
                   NOT AT END
                       PERFORM CALCULATE-ITEM-VALUE
                       PERFORM DISPLAY-ITEM-SUMMARY
                       ADD 1 TO WS-TOTAL-ITEMS
                       ADD WS-ITEM-VALUE TO WS-TOTAL-INVENTORY-VALUE
               END-READ
           END-PERFORM
           PERFORM DISPLAY-REPORT-TOTALS.

       WRITE-INVENTORY-RECORD.
           MOVE WS-ITEM-ID TO ITEM-ID
           MOVE WS-ITEM-NAME TO ITEM-NAME
           MOVE WS-ITEM-CATEGORY TO ITEM-CATEGORY
           MOVE WS-QUANTITY-ON-HAND TO QUANTITY-ON-HAND
           MOVE WS-UNIT-PRICE TO UNIT-PRICE
           MOVE WS-REORDER-LEVEL TO REORDER-LEVEL
           MOVE WS-SUPPLIER-CODE TO SUPPLIER-CODE
           WRITE INVENTORY-RECORD
               INVALID KEY
                   DISPLAY "Error writing inventory record"
           END-WRITE.

       DISPLAY-ITEM-DETAILS.
           DISPLAY "Item ID: " ITEM-ID
           DISPLAY "Item Name: " ITEM-NAME
           DISPLAY "Category: " ITEM-CATEGORY
           DISPLAY "Quantity on Hand: " QUANTITY-ON-HAND
           DISPLAY "Unit Price: " UNIT-PRICE
           DISPLAY "Reorder Level: " REORDER-LEVEL
           DISPLAY "Supplier Code: " SUPPLIER-CODE
           DISPLAY " ".

       DISPLAY-LOW-STOCK-ITEM.
           DISPLAY ITEM-ID " " ITEM-NAME " " QUANTITY-ON-HAND
                   " (Reorder: " REORDER-LEVEL ")".

       CALCULATE-ITEM-VALUE.
           MULTIPLY QUANTITY-ON-HAND BY UNIT-PRICE GIVING WS-ITEM-VALUE.

       DISPLAY-ITEM-SUMMARY.
           DISPLAY ITEM-ID " " ITEM-NAME " " WS-ITEM-VALUE.

       DISPLAY-REPORT-TOTALS.
           DISPLAY "===================="
           DISPLAY "Total Items: " WS-TOTAL-ITEMS
           DISPLAY "Total Inventory Value: " WS-TOTAL-INVENTORY-VALUE.

       CLOSE-INVENTORY-FILES.
           CLOSE INVENTORY-FILE.