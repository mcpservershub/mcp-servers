       IDENTIFICATION DIVISION.
       PROGRAM-ID. INVALID-PICTURE.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       * Invalid PICTURE clauses
       01 BAD-PIC-1    PIC 9(999999999).
       01 BAD-PIC-2    PIC XYZ.
       01 BAD-PIC-3    PIC 9A9.
       01 BAD-PIC-4    PIC.

       PROCEDURE DIVISION.
           DISPLAY "This won't compile".
           STOP RUN.
