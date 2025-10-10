       IDENTIFICATION DIVISION.
       PROGRAM-ID. ARRAY-DEMO.
       AUTHOR. GnuCOBOL MCP Test Suite.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 ARRAY-TABLE.
           05 ARRAY-ITEM OCCURS 10 TIMES.
               10 ITEM-NUMBER  PIC 9(3).
               10 ITEM-VALUE   PIC 9(5).

       01 INDEX-VAR        PIC 9(2) VALUE 1.
       01 TOTAL            PIC 9(7) VALUE 0.
       01 AVERAGE          PIC 9(7) VALUE 0.

       PROCEDURE DIVISION.
       MAIN-LOGIC.
           PERFORM INITIALIZE-ARRAY.
           PERFORM DISPLAY-ARRAY.
           PERFORM CALCULATE-STATS.
           STOP RUN.

       INITIALIZE-ARRAY.
           PERFORM VARYING INDEX-VAR FROM 1 BY 1
               UNTIL INDEX-VAR > 10
               MOVE INDEX-VAR TO ITEM-NUMBER(INDEX-VAR)
               COMPUTE ITEM-VALUE(INDEX-VAR) = INDEX-VAR * 100
           END-PERFORM.

       DISPLAY-ARRAY.
           DISPLAY "Array Contents:".
           PERFORM VARYING INDEX-VAR FROM 1 BY 1
               UNTIL INDEX-VAR > 10
               DISPLAY "Item " ITEM-NUMBER(INDEX-VAR)
                   ": " ITEM-VALUE(INDEX-VAR)
           END-PERFORM.

       CALCULATE-STATS.
           MOVE 0 TO TOTAL.
           PERFORM VARYING INDEX-VAR FROM 1 BY 1
               UNTIL INDEX-VAR > 10
               ADD ITEM-VALUE(INDEX-VAR) TO TOTAL
           END-PERFORM.
           DIVIDE TOTAL BY 10 GIVING AVERAGE.
           DISPLAY "Total: " TOTAL.
           DISPLAY "Average: " AVERAGE.
