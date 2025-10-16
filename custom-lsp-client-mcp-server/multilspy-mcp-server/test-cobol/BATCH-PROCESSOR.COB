       IDENTIFICATION DIVISION.
       PROGRAM-ID. BATCH-PROCESSOR.
      *****************************************************************
      * Batch processor that shares resources with ADVANCED-TEST     *
      * - Shares EXTERNAL data (WS-COUNTER, WS-SHARED-TOTAL)         *
      * - Shares files (CUSTOMER-FILE, TRANSACTION-FILE)             *
      * - Uses same copybooks                                        *
      *****************************************************************

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO "CUSTOMER.DAT"
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL.

           SELECT TRANSACTION-FILE ASSIGN TO "TRANS.DAT"
               ORGANIZATION IS INDEXED
               ACCESS MODE IS RANDOM
               RECORD KEY IS TRANS-ID.

       DATA DIVISION.
       FILE SECTION.
       FD  CUSTOMER-FILE.
       01  CUSTOMER-RECORD.
           COPY CUSTOMER-REC.

       FD  TRANSACTION-FILE.
       01  TRANSACTION-RECORD.
           COPY TRANS-REC.

       WORKING-STORAGE SECTION.
       01  WS-BATCH-ID              PIC X(10).
       01  WS-COUNTER               PIC 9(8) EXTERNAL.
       01  WS-SHARED-TOTAL          PIC 9(10)V99 EXTERNAL.
       01  WS-RECORD-COUNT          PIC 9(6) VALUE ZERO.

       COPY COMMON-VARS.

       LINKAGE SECTION.
       01  LS-BATCH-PARAMS          PIC X(100).

       PROCEDURE DIVISION USING LS-BATCH-PARAMS.

       MAIN-PROCESSING.
           DISPLAY "BATCH-PROCESSOR Starting"
           PERFORM OPEN-FILES
           PERFORM PROCESS-BATCH
           PERFORM CLOSE-FILES
           GOBACK
           .

       OPEN-FILES.
           OPEN INPUT CUSTOMER-FILE
           OPEN OUTPUT TRANSACTION-FILE

           CALL 'LOGGER' USING "FILES-OPENED" LS-BATCH-PARAMS
           .

       PROCESS-BATCH.
           PERFORM UNTIL WS-RECORD-COUNT = 100
               READ CUSTOMER-FILE
                   AT END
                       EXIT PERFORM
                   NOT AT END
                       PERFORM VALIDATE-AND-PROCESS
               END-READ
           END-PERFORM

           DISPLAY "Processed records: " WS-RECORD-COUNT
           DISPLAY "Global counter: " WS-COUNTER
           .

       VALIDATE-AND-PROCESS.
           CALL 'VALIDATE' USING CUSTOMER-RECORD

           CALL 'TRANPROC' USING CUSTOMER-RECORD TRANSACTION-RECORD

           WRITE TRANSACTION-RECORD

           ADD 1 TO WS-RECORD-COUNT
           ADD 1 TO WS-COUNTER
           COMPUTE WS-SHARED-TOTAL = WS-SHARED-TOTAL + 50.25

           CALL 'AUDITLOG' USING "BATCH-RECORD-PROCESSED"
           .

       CLOSE-FILES.
           CLOSE CUSTOMER-FILE
           CLOSE TRANSACTION-FILE

           CALL 'LOGGER' USING "BATCH-COMPLETE" LS-BATCH-PARAMS
           .

       END PROGRAM BATCH-PROCESSOR.
