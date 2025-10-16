       IDENTIFICATION DIVISION.
       PROGRAM-ID. VALIDATE.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * DATA VALIDATION UTILITY MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-VALIDATION-RESULT     PIC 9 VALUE 0.

       LINKAGE SECTION.
       01  LS-DATA-TO-VALIDATE      PIC X(100).

       PROCEDURE DIVISION USING LS-DATA-TO-VALIDATE.
       VALIDATE-MAIN.
           PERFORM CHECK-NOT-EMPTY
           PERFORM CHECK-FORMAT
           PERFORM CHECK-LENGTH

           IF WS-VALIDATION-RESULT = 0
               DISPLAY "Validation passed"
               CALL 'LOGGER' USING BY CONTENT "Validation OK"
               MOVE 0 TO RETURN-CODE
           ELSE
               DISPLAY "Validation failed"
               CALL 'LOGGER' USING BY CONTENT "Validation failed"
               CALL 'ERRHANDL' USING WS-VALIDATION-RESULT
               MOVE WS-VALIDATION-RESULT TO RETURN-CODE
           END-IF

           GOBACK.

       CHECK-NOT-EMPTY.
           IF LS-DATA-TO-VALIDATE = SPACES
               MOVE 1 TO WS-VALIDATION-RESULT
               DISPLAY "Error: Empty data"
           END-IF.

       CHECK-FORMAT.
           IF WS-VALIDATION-RESULT = 0
               IF LS-DATA-TO-VALIDATE NOT ALPHABETIC
                   IF LS-DATA-TO-VALIDATE NOT NUMERIC
                       DISPLAY "Warning: Mixed format"
                   END-IF
               END-IF
           END-IF.

       CHECK-LENGTH.
           IF WS-VALIDATION-RESULT = 0
               IF FUNCTION LENGTH(LS-DATA-TO-VALIDATE) < 1
                   MOVE 2 TO WS-VALIDATION-RESULT
                   DISPLAY "Error: Invalid length"
               END-IF
           END-IF.
