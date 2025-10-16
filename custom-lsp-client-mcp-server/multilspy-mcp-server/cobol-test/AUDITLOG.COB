       IDENTIFICATION DIVISION.
       PROGRAM-ID. AUDITLOG.
       AUTHOR. COBOL-TEST-SUITE.
      *****************************************************************
      * AUDIT LOGGING MODULE
      *****************************************************************

       ENVIRONMENT DIVISION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-AUDIT-ID              PIC 9(15).
       01  WS-USER-ID               PIC X(20) VALUE 'SYSTEM'.
       01  WS-TIMESTAMP             PIC X(20).
       01  WS-ACTION                PIC X(50).

       LINKAGE SECTION.
       01  LS-ENTITY-ID             PIC 9(10).

       PROCEDURE DIVISION USING LS-ENTITY-ID.
       AUDIT-MAIN.
           PERFORM GENERATE-AUDIT-ID
           PERFORM CAPTURE-AUDIT-DATA
           PERFORM SAVE-AUDIT-RECORD
           PERFORM ARCHIVE-IF-NEEDED
           GOBACK.

       GENERATE-AUDIT-ID.
           ACCEPT WS-TIMESTAMP FROM TIME
           COMPUTE WS-AUDIT-ID = FUNCTION RANDOM(99999999999999).

       CAPTURE-AUDIT-DATA.
           MOVE "Entity operation" TO WS-ACTION
           DISPLAY "Audit: Entity " LS-ENTITY-ID " accessed"
           CALL 'LOGGER' USING BY CONTENT WS-ACTION.

       SAVE-AUDIT-RECORD.
           CALL 'DBINSERT' USING WS-AUDIT-ID
                                 LS-ENTITY-ID
                                 WS-TIMESTAMP
                                 WS-ACTION

           IF RETURN-CODE NOT = 0
               DISPLAY "Audit log save failed"
               CALL 'ERRHANDL' USING RETURN-CODE
           ELSE
               DISPLAY "Audit record saved"
           END-IF.

       ARCHIVE-IF-NEEDED.
           CALL 'DBSELECT' USING WS-AUDIT-ID

           IF RETURN-CODE = 0
               CALL 'REPTGEN' USING WS-AUDIT-ID
           END-IF.
