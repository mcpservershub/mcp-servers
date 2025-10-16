       IDENTIFICATION DIVISION.
       PROGRAM-ID. FILE-OPERATIONS.
       AUTHOR. GnuCOBOL MCP Test Suite.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO "customers.dat"
               ORGANIZATION IS LINE SEQUENTIAL
               FILE STATUS IS WS-FILE-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD CUSTOMER-FILE.
       01 CUSTOMER-RECORD.
           05 CUSTOMER-ID      PIC 9(5).
           05 CUSTOMER-NAME    PIC X(30).
           05 CUSTOMER-BALANCE PIC 9(7)V99.

       WORKING-STORAGE SECTION.
       01 WS-FILE-STATUS       PIC XX.
       01 WS-EOF               PIC X VALUE 'N'.
       01 WS-RECORD-COUNT      PIC 9(5) VALUE 0.

       PROCEDURE DIVISION.
       MAIN-LOGIC.
           PERFORM OPEN-FILE.
           PERFORM READ-FILE UNTIL WS-EOF = 'Y'.
           PERFORM CLOSE-FILE.
           DISPLAY "Total records processed: " WS-RECORD-COUNT.
           STOP RUN.

       OPEN-FILE.
           OPEN INPUT CUSTOMER-FILE.
           IF WS-FILE-STATUS NOT = '00'
               DISPLAY "Error opening file: " WS-FILE-STATUS
               STOP RUN
           END-IF.

       READ-FILE.
           READ CUSTOMER-FILE
               AT END
                   MOVE 'Y' TO WS-EOF
               NOT AT END
                   ADD 1 TO WS-RECORD-COUNT
                   PERFORM PROCESS-RECORD
           END-READ.

       PROCESS-RECORD.
           DISPLAY "Customer: " CUSTOMER-ID " " CUSTOMER-NAME.
           DISPLAY "Balance: $" CUSTOMER-BALANCE.

       CLOSE-FILE.
           CLOSE CUSTOMER-FILE.
           IF WS-FILE-STATUS NOT = '00'
               DISPLAY "Error closing file: " WS-FILE-STATUS
           END-IF.
