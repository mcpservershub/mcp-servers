       IDENTIFICATION DIVISION.
       PROGRAM-ID. MALFORMED-STRUCTURE.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 PARENT-VAR.
           05 CHILD-VAR PIC X(10).
           * Invalid level number
           02 WRONG-LEVEL PIC 9(5).

       PROCEDURE DIVISION.
           * Unclosed IF statement
           IF CHILD-VAR = "TEST"
               DISPLAY "Inside IF"
           * Missing END-IF

           * Unclosed PERFORM
           PERFORM VARYING CHILD-VAR FROM 1 BY 1
               DISPLAY CHILD-VAR
           * Missing END-PERFORM

           STOP RUN.
