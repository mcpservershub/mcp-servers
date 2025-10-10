      ******************************************************************
      * UTILITIES - COMMON SUBROUTINES
      * Author: Test User
      * Date: 2025-01-25
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. UTILITIES.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-DATE-WORK-AREAS.
           05 WS-CURRENT-DATE     PIC 9(8).
           05 WS-FORMATTED-DATE   PIC X(10).
           05 WS-DATE-PARTS REDEFINES WS-CURRENT-DATE.
               10 WS-YEAR         PIC 9(4).
               10 WS-MONTH        PIC 9(2).
               10 WS-DAY          PIC 9(2).

       01  WS-TIME-WORK-AREAS.
           05 WS-CURRENT-TIME     PIC 9(8).
           05 WS-FORMATTED-TIME   PIC X(8).
           05 WS-TIME-PARTS REDEFINES WS-CURRENT-TIME.
               10 WS-HOUR         PIC 9(2).
               10 WS-MINUTE       PIC 9(2).
               10 WS-SECOND       PIC 9(2).
               10 WS-HUNDREDTHS   PIC 9(2).

       01  WS-VALIDATION-FIELDS.
           05 WS-INPUT-FIELD      PIC X(30).
           05 WS-NUMERIC-TEST     PIC 9(10).
           05 WS-VALIDATION-RESULT PIC X.
               88 VALID-INPUT     VALUE 'Y'.
               88 INVALID-INPUT   VALUE 'N'.

       01  WS-STRING-WORK-AREAS.
           05 WS-SOURCE-STRING    PIC X(100).
           05 WS-TARGET-STRING    PIC X(100).
           05 WS-STRING-LENGTH    PIC 9(3).
           05 WS-CHAR-POSITION    PIC 9(3).

       LINKAGE SECTION.
       01  LS-FUNCTION-CODE       PIC X(2).
       01  LS-INPUT-DATA          PIC X(100).
       01  LS-OUTPUT-DATA         PIC X(100).
       01  LS-RETURN-CODE         PIC 9(2).

       PROCEDURE DIVISION USING LS-FUNCTION-CODE LS-INPUT-DATA
                               LS-OUTPUT-DATA LS-RETURN-CODE.

       MAIN-UTILITIES-PROGRAM.
           INITIALIZE LS-RETURN-CODE
           EVALUATE LS-FUNCTION-CODE
               WHEN "DT"
                   PERFORM GET-CURRENT-DATE-TIME
               WHEN "VN"
                   PERFORM VALIDATE-NUMERIC-INPUT
               WHEN "UC"
                   PERFORM CONVERT-TO-UPPERCASE
               WHEN "LC"
                   PERFORM CONVERT-TO-LOWERCASE
               WHEN "TR"
                   PERFORM TRIM-STRING
               WHEN "LN"
                   PERFORM GET-STRING-LENGTH
               WHEN "PD"
                   PERFORM PAD-STRING
               WHEN OTHER
                   MOVE 99 TO LS-RETURN-CODE
                   DISPLAY "Invalid utility function: " LS-FUNCTION-CODE
           END-EVALUATE
           GOBACK.

       GET-CURRENT-DATE-TIME.
           ACCEPT WS-CURRENT-DATE FROM DATE YYYYMMDD
           ACCEPT WS-CURRENT-TIME FROM TIME
           PERFORM FORMAT-DATE
           PERFORM FORMAT-TIME
           STRING WS-FORMATTED-DATE " " WS-FORMATTED-TIME
               DELIMITED BY SIZE
               INTO LS-OUTPUT-DATA
           END-STRING
           MOVE 00 TO LS-RETURN-CODE.

       FORMAT-DATE.
           STRING WS-MONTH "/" WS-DAY "/" WS-YEAR
               DELIMITED BY SIZE
               INTO WS-FORMATTED-DATE
           END-STRING.

       FORMAT-TIME.
           STRING WS-HOUR ":" WS-MINUTE ":" WS-SECOND
               DELIMITED BY SIZE
               INTO WS-FORMATTED-TIME
           END-STRING.

       VALIDATE-NUMERIC-INPUT.
           MOVE LS-INPUT-DATA TO WS-INPUT-FIELD
           PERFORM TRIM-INPUT-FIELD
           IF WS-INPUT-FIELD IS NUMERIC
               SET VALID-INPUT TO TRUE
               MOVE 00 TO LS-RETURN-CODE
               MOVE "VALID" TO LS-OUTPUT-DATA
           ELSE
               SET INVALID-INPUT TO TRUE
               MOVE 01 TO LS-RETURN-CODE
               MOVE "INVALID" TO LS-OUTPUT-DATA
           END-IF.

       TRIM-INPUT-FIELD.
           INSPECT WS-INPUT-FIELD REPLACING LEADING SPACES BY LOW-VALUES
           INSPECT WS-INPUT-FIELD REPLACING TRAILING SPACES BY LOW-VALUES
           INSPECT WS-INPUT-FIELD REPLACING LOW-VALUES BY SPACES.

       CONVERT-TO-UPPERCASE.
           MOVE LS-INPUT-DATA TO WS-SOURCE-STRING
           INSPECT WS-SOURCE-STRING CONVERTING
               "abcdefghijklmnopqrstuvwxyz" TO
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
           MOVE WS-SOURCE-STRING TO LS-OUTPUT-DATA
           MOVE 00 TO LS-RETURN-CODE.

       CONVERT-TO-LOWERCASE.
           MOVE LS-INPUT-DATA TO WS-SOURCE-STRING
           INSPECT WS-SOURCE-STRING CONVERTING
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ" TO
               "abcdefghijklmnopqrstuvwxyz"
           MOVE WS-SOURCE-STRING TO LS-OUTPUT-DATA
           MOVE 00 TO LS-RETURN-CODE.

       TRIM-STRING.
           MOVE LS-INPUT-DATA TO WS-SOURCE-STRING
           INSPECT WS-SOURCE-STRING
               REPLACING LEADING SPACES BY LOW-VALUES
           INSPECT WS-SOURCE-STRING
               REPLACING TRAILING SPACES BY LOW-VALUES
           INSPECT WS-SOURCE-STRING
               REPLACING LOW-VALUES BY SPACES
           MOVE WS-SOURCE-STRING TO LS-OUTPUT-DATA
           MOVE 00 TO LS-RETURN-CODE.

       GET-STRING-LENGTH.
           MOVE LS-INPUT-DATA TO WS-SOURCE-STRING
           PERFORM VARYING WS-CHAR-POSITION FROM 100 BY -1
               UNTIL WS-CHAR-POSITION = 0
                  OR WS-SOURCE-STRING(WS-CHAR-POSITION:1) NOT = SPACE
           END-PERFORM
           MOVE WS-CHAR-POSITION TO WS-STRING-LENGTH
           MOVE WS-STRING-LENGTH TO LS-OUTPUT-DATA
           MOVE 00 TO LS-RETURN-CODE.

       PAD-STRING.
      * Pad string to specified length (passed in first 3 chars of input)
           MOVE LS-INPUT-DATA(1:3) TO WS-STRING-LENGTH
           MOVE LS-INPUT-DATA(4:) TO WS-SOURCE-STRING
           IF WS-STRING-LENGTH > LENGTH OF WS-SOURCE-STRING
               MOVE WS-STRING-LENGTH TO WS-STRING-LENGTH
           END-IF
           MOVE SPACES TO WS-TARGET-STRING
           MOVE WS-SOURCE-STRING TO WS-TARGET-STRING
           MOVE WS-TARGET-STRING TO LS-OUTPUT-DATA
           MOVE 00 TO LS-RETURN-CODE.