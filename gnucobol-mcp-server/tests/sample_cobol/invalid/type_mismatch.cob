       IDENTIFICATION DIVISION.
       PROGRAM-ID. TYPE-MISMATCH.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 NUMERIC-VAR     PIC 9(5) VALUE 12345.
       01 ALPHA-VAR       PIC X(10) VALUE "HELLO".

       PROCEDURE DIVISION.
           * Type mismatch: trying to add alphanumeric to numeric
           ADD ALPHA-VAR TO NUMERIC-VAR.

           * Invalid numeric value
           MOVE "ABC" TO NUMERIC-VAR.

           STOP RUN.
