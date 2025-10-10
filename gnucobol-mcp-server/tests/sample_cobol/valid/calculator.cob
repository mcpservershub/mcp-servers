       IDENTIFICATION DIVISION.
       PROGRAM-ID. SIMPLE-CALCULATOR.
       AUTHOR. GnuCOBOL MCP Test Suite.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 NUM1            PIC 9(4) VALUE 0.
       01 NUM2            PIC 9(4) VALUE 0.
       01 RESULT          PIC 9(5) VALUE 0.
       01 OPERATION       PIC X(1) VALUE SPACE.

       PROCEDURE DIVISION.
       MAIN-LOGIC.
           DISPLAY "Simple Calculator".
           DISPLAY "Enter first number (0-9999): ".
           ACCEPT NUM1.

           DISPLAY "Enter second number (0-9999): ".
           ACCEPT NUM2.

           DISPLAY "Enter operation (+, -, *, /): ".
           ACCEPT OPERATION.

           EVALUATE OPERATION
               WHEN '+'
                   ADD NUM1 TO NUM2 GIVING RESULT
                   DISPLAY "Result: " RESULT
               WHEN '-'
                   SUBTRACT NUM2 FROM NUM1 GIVING RESULT
                   DISPLAY "Result: " RESULT
               WHEN '*'
                   MULTIPLY NUM1 BY NUM2 GIVING RESULT
                   DISPLAY "Result: " RESULT
               WHEN '/'
                   IF NUM2 = 0
                       DISPLAY "Error: Division by zero"
                   ELSE
                       DIVIDE NUM1 BY NUM2 GIVING RESULT
                       DISPLAY "Result: " RESULT
                   END-IF
               WHEN OTHER
                   DISPLAY "Invalid operation"
           END-EVALUATE.

           STOP RUN.
