      ******************************************************************
      * ERROR CODES COPYBOOK
      * Standard error codes for the application
      * Author: Test User
      * Date: 2025-01-25
      ******************************************************************
       01  ERROR-CODES.
           05 NO-ERROR            PIC 9(2) VALUE 00.
           05 FILE-NOT-FOUND      PIC 9(2) VALUE 10.
           05 RECORD-NOT-FOUND    PIC 9(2) VALUE 11.
           05 DUPLICATE-KEY       PIC 9(2) VALUE 12.
           05 INVALID-DATA        PIC 9(2) VALUE 20.
           05 INVALID-DATE        PIC 9(2) VALUE 21.
           05 INVALID-AMOUNT      PIC 9(2) VALUE 22.
           05 ACCESS-DENIED       PIC 9(2) VALUE 30.
           05 SYSTEM-ERROR        PIC 9(2) VALUE 99.

       01  ERROR-MESSAGES.
           05 MSG-NO-ERROR        PIC X(30) VALUE
              'Operation completed successfully'.
           05 MSG-FILE-NOT-FOUND  PIC X(30) VALUE
              'File not found'.
           05 MSG-RECORD-NOT-FOUND PIC X(30) VALUE
              'Record not found'.
           05 MSG-DUPLICATE-KEY   PIC X(30) VALUE
              'Duplicate key error'.
           05 MSG-INVALID-DATA    PIC X(30) VALUE
              'Invalid data format'.
           05 MSG-INVALID-DATE    PIC X(30) VALUE
              'Invalid date format'.
           05 MSG-INVALID-AMOUNT  PIC X(30) VALUE
              'Invalid amount format'.
           05 MSG-ACCESS-DENIED   PIC X(30) VALUE
              'Access denied'.
           05 MSG-SYSTEM-ERROR    PIC X(30) VALUE
              'System error occurred'.