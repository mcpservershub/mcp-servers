      ******************************************************************
      * CUSTOMER RECORD COPYBOOK
      * Defines the standard customer record layout
      * Author: Test User
      * Date: 2025-01-25
      ******************************************************************
       01  CUSTOMER-RECORD.
           05 CUSTOMER-ID         PIC 9(6).
           05 CUSTOMER-NAME       PIC X(30).
           05 CUSTOMER-ADDRESS.
               10 STREET-ADDRESS  PIC X(30).
               10 CITY            PIC X(20).
               10 STATE           PIC X(2).
               10 ZIP-CODE        PIC X(10).
           05 CUSTOMER-PHONE      PIC X(15).
           05 CUSTOMER-EMAIL      PIC X(50).
           05 CUSTOMER-BALANCE    PIC S9(8)V99 COMP-3.
           05 CUSTOMER-STATUS     PIC X.
               88 ACTIVE-CUSTOMER VALUE 'A'.
               88 INACTIVE-CUSTOMER VALUE 'I'.
               88 SUSPENDED-CUSTOMER VALUE 'S'.
           05 DATE-OPENED         PIC 9(8).
           05 LAST-ACTIVITY-DATE  PIC 9(8).
           05 CREDIT-LIMIT        PIC S9(7)V99 COMP-3.