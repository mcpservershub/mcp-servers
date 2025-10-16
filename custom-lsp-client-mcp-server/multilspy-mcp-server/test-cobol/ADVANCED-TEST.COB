       IDENTIFICATION DIVISION.
       PROGRAM-ID. ADVANCED-TEST.
      *****************************************************************
      * Test program demonstrating all CFG relationship types        *
      * - COPY statements (copybooks)                                *
      * - Dynamic CALL statements                                    *
      * - ENTRY statements (alternative entry points)                *
      * - EXTERNAL data (shared memory)                              *
      * - File sharing (SELECT statements)                           *
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
       01  WS-PROGRAM-NAME          PIC X(20).
       01  WS-COUNTER               PIC 9(8) EXTERNAL.
       01  WS-SHARED-TOTAL          PIC 9(10)V99 EXTERNAL.
       01  WS-STATUS-CODE           PIC XX.

       COPY COMMON-VARS.
       COPY ERROR-CODES IN ERRORLIB.

       LINKAGE SECTION.
       01  LS-INPUT-PARM            PIC X(100).
       01  LS-OUTPUT-PARM           PIC X(200).

       PROCEDURE DIVISION USING LS-INPUT-PARM LS-OUTPUT-PARM.

       MAIN-SECTION SECTION.

       MAIN-PARA.
           DISPLAY "Starting ADVANCED-TEST Program"
           PERFORM INITIALIZE-PROGRAM
           PERFORM PROCESS-SELECTION
           PERFORM CLEANUP-PROGRAM
           GOBACK
           .

       INITIALIZE-PROGRAM.
           DISPLAY "Initializing..."
           MOVE "ADVANCED-TEST" TO WS-PROGRAM-NAME
           ADD 1 TO WS-COUNTER

      *    Static CALL to external program
           CALL 'LOGGER' USING WS-PROGRAM-NAME WS-STATUS-CODE

      *    Open shared files
           OPEN INPUT CUSTOMER-FILE
           OPEN I-O TRANSACTION-FILE
           .

       PROCESS-SELECTION.
           DISPLAY "Enter processing option: "
           ACCEPT WS-STATUS-CODE

           EVALUATE WS-STATUS-CODE
               WHEN "01"
                   PERFORM DYNAMIC-CALL-HANDLER
               WHEN "02"
                   PERFORM DIRECT-PROCESSING
               WHEN "03"
                   PERFORM ALTERNATE-ENTRY-DEMO
               WHEN OTHER
                   DISPLAY "Invalid option"
           END-EVALUATE
           .

       DYNAMIC-CALL-HANDLER.
      *    Dynamic CALL using variable
           DISPLAY "Enter program name to call: "
           ACCEPT WS-PROGRAM-NAME
           CALL WS-PROGRAM-NAME USING LS-INPUT-PARM LS-OUTPUT-PARM

           IF RETURN-CODE NOT = ZERO
               CALL 'ERRHANDL' USING WS-STATUS-CODE
           END-IF
           .

       DIRECT-PROCESSING.
           CALL 'VALIDATE' USING LS-INPUT-PARM
           CALL 'DBINSERT' USING CUSTOMER-RECORD
           CALL 'AUDITLOG' USING WS-PROGRAM-NAME WS-STATUS-CODE

           ADD 1 TO WS-COUNTER
           COMPUTE WS-SHARED-TOTAL = WS-SHARED-TOTAL + 100.50
           .

       ALTERNATE-ENTRY-DEMO.
      *    Demonstrate calling this program at alternate entry point
           DISPLAY "Demonstrating alternate entry point"
           CALL 'ADVANCED-TEST' USING "PROCESS-BATCH" LS-OUTPUT-PARM
           .

      *    Alternative entry point for batch processing
       ENTRY 'PROCESS-BATCH' USING LS-INPUT-PARM LS-OUTPUT-PARM.
           DISPLAY "Entered via PROCESS-BATCH entry point"
           PERFORM READ-AND-PROCESS-BATCH
           EXIT PROGRAM
           .

       READ-AND-PROCESS-BATCH.
           DISPLAY "Processing batch records..."

           READ CUSTOMER-FILE
               AT END
                   MOVE "99" TO WS-STATUS-CODE
               NOT AT END
                   CALL 'TRANPROC' USING CUSTOMER-RECORD TRANSACTION-RECORD
                   ADD 1 TO WS-COUNTER
           END-READ

           READ TRANSACTION-FILE
               INVALID KEY
                   CALL 'ERRHANDL' USING "FILE-ERROR"
               NOT INVALID KEY
                   CALL 'REPTGEN' USING TRANSACTION-RECORD
           END-READ
           .

       CLEANUP-PROGRAM.
           DISPLAY "Cleaning up..."

           CLOSE CUSTOMER-FILE
           CLOSE TRANSACTION-FILE

           CALL 'LOGGER' USING "CLEANUP-COMPLETE" WS-STATUS-CODE

           DISPLAY "External counter value: " WS-COUNTER
           DISPLAY "Shared total: " WS-SHARED-TOTAL
           .

       END PROGRAM ADVANCED-TEST.
