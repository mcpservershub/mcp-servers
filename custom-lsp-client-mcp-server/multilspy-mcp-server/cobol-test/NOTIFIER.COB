       IDENTIFICATION DIVISION.
       PROGRAM-ID. NOTIFIER.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * NOTIFICATION SERVICE MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-NOTIFICATION-ID       PIC 9(12).
       01  WS-NOTIFICATION-TYPE     PIC X(20).
       01  WS-RECIPIENT             PIC X(50).
       01  WS-MESSAGE               PIC X(200).

       LINKAGE SECTION.
       01  LS-ENTITY-ID             PIC 9(10).

       PROCEDURE DIVISION USING LS-ENTITY-ID.
       NOTIFIER-MAIN.
           PERFORM PREPARE-NOTIFICATION
           PERFORM SEND-EMAIL
           PERFORM SEND-SMS
           PERFORM LOG-NOTIFICATION
           GOBACK.

       PREPARE-NOTIFICATION.
           MOVE "TRANSACTION_ALERT" TO WS-NOTIFICATION-TYPE
           MOVE "Transaction processed for entity" TO WS-MESSAGE
           DISPLAY "Preparing notification for " LS-ENTITY-ID
           CALL 'LOGGER' USING BY CONTENT "Notification prepared".

       SEND-EMAIL.
           CALL 'DBSELECT' USING LS-ENTITY-ID

           IF RETURN-CODE = 0
               DISPLAY "Email sent to " WS-RECIPIENT
               CALL 'AUDITLOG' USING LS-ENTITY-ID
           ELSE
               DISPLAY "Failed to send email"
               CALL 'ERRHANDL' USING RETURN-CODE
           END-IF.

       SEND-SMS.
           CALL 'VALIDATE' USING WS-RECIPIENT

           IF RETURN-CODE = 0
               DISPLAY "SMS sent to " WS-RECIPIENT
               CALL 'AUDITLOG' USING LS-ENTITY-ID
           ELSE
               DISPLAY "Failed to send SMS"
               CALL 'ERRHANDL' USING RETURN-CODE
           END-IF.

       LOG-NOTIFICATION.
           CALL 'LOGGER' USING BY CONTENT "Notification sent"
           CALL 'DBINSERT' USING WS-NOTIFICATION-ID
                                 LS-ENTITY-ID
                                 WS-MESSAGE.
