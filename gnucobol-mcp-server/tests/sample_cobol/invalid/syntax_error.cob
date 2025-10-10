       IDENTIFICATION DIVISION.
       PROGRAM-ID. SYNTAX-ERROR-TEST.

       PROCEDURE DIVISION.
           DISPLAY "Missing period here"
           DISPLAY "This will cause error".
           INVALID-COMMAND-HERE
           STOP RUN.
