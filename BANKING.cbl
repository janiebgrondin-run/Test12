      *================================================================*
      * PROGRAM : BANKING-SYSTEM                                      *
      * AUTHOR  : BANK OF COBOL - DATA PROCESSING DEPT               *
      * PURPOSE : IN-MEMORY BANKING DATABASE - 1000 CLIENT ACCOUNTS  *
      * OPS     : DEPOSITS AND WITHDRAWALS ONLY                       *
      * RULES   : ALL BUSINESS RULES ARE HARDCODED IN WS-RULES       *
      *================================================================*
       IDENTIFICATION DIVISION.
       PROGRAM-ID. BANKING-SYSTEM.
       AUTHOR. BANK-OF-COBOL-DP.
       DATE-WRITTEN. 2024-01-15.

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SOURCE-COMPUTER. IBM-MAINFRAME.
       OBJECT-COMPUTER. IBM-MAINFRAME.

       DATA DIVISION.
       WORKING-STORAGE SECTION.

      *================================================================*
      *  HARDCODED BUSINESS RULES                                      *
      *================================================================*
       01  WS-RULES.
           05  BR-MIN-BALANCE         PIC 9(8)V99  VALUE  100.00.
           05  BR-MAX-WD-SINGLE       PIC 9(8)V99  VALUE  10000.00.
           05  BR-MAX-DEP-SINGLE      PIC 9(8)V99  VALUE  50000.00.
           05  BR-MAX-WD-DAILY        PIC 9(8)V99  VALUE  20000.00.
           05  BR-MAX-DEP-DAILY       PIC 9(8)V99  VALUE  100000.00.
           05  BR-MIN-TX-AMOUNT       PIC 9(8)V99  VALUE  1.00.
           05  BR-INITIAL-BALANCE     PIC 9(8)V99  VALUE  500.00.
           05  BR-VIP-THRESHOLD       PIC 9(8)V99  VALUE  50000.00.
           05  BR-VIP-MAX-WD-SINGLE   PIC 9(8)V99  VALUE  50000.00.
           05  BR-VIP-MAX-DEP-SINGLE  PIC 9(8)V99  VALUE  250000.00.
           05  BR-VIP-MAX-WD-DAILY    PIC 9(8)V99  VALUE  100000.00.
           05  BR-VIP-MAX-DEP-DAILY   PIC 9(8)V99  VALUE  500000.00.
           05  BR-MAX-CLIENTS         PIC 9(4)     VALUE  1000.
           05  BR-MAX-TX-LOG          PIC 9(5)     VALUE  5000.
           05  BR-FIRST-CLIENT-ID     PIC 9(6)     VALUE  100001.

      *================================================================*
      *  CLIENT DATABASE - 1000 ACCOUNT RECORDS (IN-MEMORY)           *
      *================================================================*
       01  WS-CLIENT-DB.
           05  DB-CLIENT-COUNT        PIC 9(4)   VALUE 0.
           05  DB-ENTRY OCCURS 1000 TIMES
                        INDEXED BY DB-IDX.
               10  DB-CLIENT-ID       PIC 9(6).
               10  DB-LAST-NAME       PIC X(15).
               10  DB-FIRST-NAME      PIC X(10).
               10  DB-BALANCE         PIC S9(10)V99.
               10  DB-STATUS          PIC X(1).
                   88  DB-ACTIVE      VALUE 'A'.
                   88  DB-FROZEN      VALUE 'F'.
                   88  DB-CLOSED      VALUE 'C'.
               10  DB-ACCT-TYPE       PIC X(1).
                   88  DB-REGULAR     VALUE 'R'.
                   88  DB-VIP         VALUE 'V'.
               10  DB-DAILY-WD        PIC 9(10)V99.
               10  DB-DAILY-DEP       PIC 9(10)V99.
               10  DB-OPEN-DATE       PIC X(10).
               10  DB-TX-COUNT        PIC 9(6).
               10  DB-LAST-TX-DATE    PIC X(10).
               10  DB-LAST-TX-TYPE    PIC X(1).
               10  DB-LAST-TX-AMT     PIC 9(10)V99.

      *================================================================*
      *  TRANSACTION LOG - CIRCULAR BUFFER (5000 ENTRIES)             *
      *================================================================*
       01  WS-TX-LOG.
           05  TX-TOTAL-COUNT         PIC 9(5)  VALUE 0.
           05  TX-NEXT-ID             PIC 9(8)  VALUE 1.
           05  TX-ENTRY OCCURS 5000 TIMES
                        INDEXED BY TX-IDX.
               10  TX-ID              PIC 9(8).
               10  TX-DATE            PIC X(10).
               10  TX-TIME            PIC X(8).
               10  TX-CLIENT-ID       PIC 9(6).
               10  TX-TYPE            PIC X(1).
                   88  TX-DEPOSIT     VALUE 'D'.
                   88  TX-WITHDRAWAL  VALUE 'W'.
               10  TX-AMOUNT          PIC 9(10)V99.
               10  TX-BAL-AFTER       PIC S9(10)V99.
               10  TX-RESULT          PIC X(2).
                   88  TX-APPROVED    VALUE 'OK'.
                   88  TX-REJECTED    VALUE 'RJ'.
               10  TX-REJECT-REASON   PIC X(30).

      *================================================================*
      *  WORK FIELDS                                                    *
      *================================================================*
       01  WS-WORK.
           05  WW-SEARCH-ID           PIC 9(6)      VALUE 0.
           05  WW-FOUND-IDX           PIC 9(4)      VALUE 0.
           05  WW-FOUND-FLAG          PIC X(1)      VALUE 'N'.
           05  WW-AMOUNT              PIC 9(10)V99  VALUE 0.
           05  WW-NEW-BALANCE         PIC S9(10)V99 VALUE 0.
           05  WW-RESULT              PIC X(2)      VALUE SPACES.
           05  WW-ERROR-MSG           PIC X(60)     VALUE SPACES.
           05  WW-MENU-CHOICE         PIC X(1)      VALUE SPACES.
           05  WW-RUN-FLAG            PIC X(1)      VALUE 'Y'.
           05  WW-LOOP-CTR            PIC 9(4)      VALUE 0.
           05  WW-INIT-CTR            PIC 9(4)      VALUE 0.
           05  WW-LN-SEED             PIC 9(2)      VALUE 0.
           05  WW-FN-SEED             PIC 9(2)      VALUE 0.
           05  WW-BAL-SEED            PIC 9(10)V99  VALUE 0.
           05  WW-MOD-RESULT          PIC 9(4)      VALUE 0.
           05  WW-TX-SLOT             PIC 9(5)      VALUE 0.
           05  WW-AVAIL-WD            PIC 9(10)V99  VALUE 0.
           05  WW-AVAIL-DEP           PIC 9(10)V99  VALUE 0.
           05  WW-CURRENT-OP          PIC X(1)      VALUE SPACES.
           05  WW-DATE-SIM            PIC X(10)     VALUE '2024-01-15'.
           05  WW-TIME-SIM            PIC X(8)      VALUE '09:00:00'.
           05  WW-TOTAL-DEP-DAY       PIC 9(12)V99  VALUE 0.
           05  WW-TOTAL-WD-DAY        PIC 9(12)V99  VALUE 0.
           05  WW-PAGE-LIMIT          PIC 9(4)      VALUE 20.
           05  WW-PAGE-START          PIC 9(4)      VALUE 1.
           05  WW-PAGE-END            PIC 9(4)      VALUE 0.
           05  WW-STATUS-LABEL        PIC X(8)      VALUE SPACES.
           05  WW-TYPE-LABEL          PIC X(8)      VALUE SPACES.

       01  WS-DISPLAY.
           05  WD-BALANCE             PIC $$$,$$$,$$9.99.
           05  WD-AMOUNT              PIC $$$,$$$,$$9.99.
           05  WD-DAILY-WD            PIC $$$,$$$,$$9.99.
           05  WD-DAILY-DEP           PIC $$$,$$$,$$9.99.
           05  WD-SEP-LINE            PIC X(65) VALUE ALL '='.
           05  WD-DASH-LINE           PIC X(65) VALUE ALL '-'.

      *================================================================*
      *  NAME SEED TABLES FOR PROCEDURAL CLIENT GENERATION            *
      *================================================================*
       01  WS-LNAME-TABLE.
           05  LT-ENTRY OCCURS 20 TIMES.
               10  LT-VALUE           PIC X(15).

       01  WS-FNAME-TABLE.
           05  FT-ENTRY OCCURS 20 TIMES.
               10  FT-VALUE           PIC X(10).

      *================================================================*
       PROCEDURE DIVISION.
      *================================================================*

      *----------------------------------------------------------------*
       0000-MAIN.
           PERFORM 1000-INITIALIZE
           PERFORM 2000-MAIN-MENU
               UNTIL WW-RUN-FLAG = 'N'
           PERFORM 9999-END-PROGRAM
           STOP RUN
           .

      *================================================================*
      *  INITIALIZATION                                                 *
      *================================================================*

       1000-INITIALIZE.
           PERFORM 1100-LOAD-NAME-TABLES
           PERFORM 1200-POPULATE-CLIENTS
           PERFORM 1300-DISPLAY-WELCOME
           .

      *----------------------------------------------------------------*
       1100-LOAD-NAME-TABLES.
           MOVE 'SMITH          '  TO LT-VALUE(1)
           MOVE 'JOHNSON        '  TO LT-VALUE(2)
           MOVE 'WILLIAMS       '  TO LT-VALUE(3)
           MOVE 'JONES          '  TO LT-VALUE(4)
           MOVE 'BROWN          '  TO LT-VALUE(5)
           MOVE 'DAVIS          '  TO LT-VALUE(6)
           MOVE 'MILLER         '  TO LT-VALUE(7)
           MOVE 'WILSON         '  TO LT-VALUE(8)
           MOVE 'MOORE          '  TO LT-VALUE(9)
           MOVE 'TAYLOR         '  TO LT-VALUE(10)
           MOVE 'ANDERSON       '  TO LT-VALUE(11)
           MOVE 'THOMAS         '  TO LT-VALUE(12)
           MOVE 'JACKSON        '  TO LT-VALUE(13)
           MOVE 'WHITE          '  TO LT-VALUE(14)
           MOVE 'HARRIS         '  TO LT-VALUE(15)
           MOVE 'MARTIN         '  TO LT-VALUE(16)
           MOVE 'GARCIA         '  TO LT-VALUE(17)
           MOVE 'MARTINEZ       '  TO LT-VALUE(18)
           MOVE 'ROBINSON       '  TO LT-VALUE(19)
           MOVE 'CLARK          '  TO LT-VALUE(20)
           MOVE 'JAMES     '       TO FT-VALUE(1)
           MOVE 'JOHN      '       TO FT-VALUE(2)
           MOVE 'ROBERT    '       TO FT-VALUE(3)
           MOVE 'MICHAEL   '       TO FT-VALUE(4)
           MOVE 'WILLIAM   '       TO FT-VALUE(5)
           MOVE 'DAVID     '       TO FT-VALUE(6)
           MOVE 'RICHARD   '       TO FT-VALUE(7)
           MOVE 'JOSEPH    '       TO FT-VALUE(8)
           MOVE 'THOMAS    '       TO FT-VALUE(9)
           MOVE 'CHARLES   '       TO FT-VALUE(10)
           MOVE 'MARY      '       TO FT-VALUE(11)
           MOVE 'PATRICIA  '       TO FT-VALUE(12)
           MOVE 'LINDA     '       TO FT-VALUE(13)
           MOVE 'BARBARA   '       TO FT-VALUE(14)
           MOVE 'ELIZABETH '       TO FT-VALUE(15)
           MOVE 'JENNIFER  '       TO FT-VALUE(16)
           MOVE 'MARIA     '       TO FT-VALUE(17)
           MOVE 'SUSAN     '       TO FT-VALUE(18)
           MOVE 'MARGARET  '       TO FT-VALUE(19)
           MOVE 'DOROTHY   '       TO FT-VALUE(20)
           .

      *----------------------------------------------------------------*
       1200-POPULATE-CLIENTS.
           MOVE BR-MAX-CLIENTS TO DB-CLIENT-COUNT
           PERFORM VARYING WW-INIT-CTR FROM 1 BY 1
               UNTIL WW-INIT-CTR > 1000
               PERFORM 1210-INIT-ONE-CLIENT
           END-PERFORM
           .

      *----------------------------------------------------------------*
       1210-INIT-ONE-CLIENT.
           COMPUTE DB-CLIENT-ID(WW-INIT-CTR) = 100000 + WW-INIT-CTR
           COMPUTE WW-LN-SEED =
               FUNCTION MOD(WW-INIT-CTR - 1, 20) + 1
           MOVE LT-VALUE(WW-LN-SEED) TO DB-LAST-NAME(WW-INIT-CTR)
           COMPUTE WW-FN-SEED =
               FUNCTION MOD(WW-INIT-CTR + 6, 20) + 1
           MOVE FT-VALUE(WW-FN-SEED) TO DB-FIRST-NAME(WW-INIT-CTR)
           COMPUTE WW-BAL-SEED = 500.00 + (WW-INIT-CTR * 99.50)
           MOVE WW-BAL-SEED TO DB-BALANCE(WW-INIT-CTR)
           MOVE WW-DATE-SIM TO DB-OPEN-DATE(WW-INIT-CTR)
           MOVE ZEROS TO DB-DAILY-WD(WW-INIT-CTR)
           MOVE ZEROS TO DB-DAILY-DEP(WW-INIT-CTR)
           MOVE ZEROS TO DB-TX-COUNT(WW-INIT-CTR)
           MOVE WW-DATE-SIM TO DB-LAST-TX-DATE(WW-INIT-CTR)
           MOVE SPACES TO DB-LAST-TX-TYPE(WW-INIT-CTR)
           MOVE ZEROS TO DB-LAST-TX-AMT(WW-INIT-CTR)
           COMPUTE WW-MOD-RESULT = FUNCTION MOD(WW-INIT-CTR, 100)
           EVALUATE TRUE
               WHEN WW-MOD-RESULT = 0
                   MOVE 'F' TO DB-STATUS(WW-INIT-CTR)
               WHEN OTHER
                   COMPUTE WW-MOD-RESULT =
                       FUNCTION MOD(WW-INIT-CTR, 50)
                   IF WW-MOD-RESULT = 0
                       MOVE 'C' TO DB-STATUS(WW-INIT-CTR)
                   ELSE
                       MOVE 'A' TO DB-STATUS(WW-INIT-CTR)
                   END-IF
           END-EVALUATE
           IF DB-BALANCE(WW-INIT-CTR) > BR-VIP-THRESHOLD
               MOVE 'V' TO DB-ACCT-TYPE(WW-INIT-CTR)
           ELSE
               MOVE 'R' TO DB-ACCT-TYPE(WW-INIT-CTR)
           END-IF
           .

      *----------------------------------------------------------------*
       1300-DISPLAY-WELCOME.
           DISPLAY WD-SEP-LINE
           DISPLAY '  BANK OF COBOL  -  CORE BANKING SYSTEM  v1.0 '
           DISPLAY '  ESTABLISHED 1959  -  MAINFRAME DIVISION      '
           DISPLAY WD-SEP-LINE
           DISPLAY '  DATABASE LOADED: ' DB-CLIENT-COUNT
               ' CLIENT ACCOUNTS'
           DISPLAY '  AUTHORIZED OPS : DEPOSIT  |  WITHDRAWAL'
           DISPLAY WD-SEP-LINE
           .

      *================================================================*
      *  MAIN MENU                                                      *
      *================================================================*

       2000-MAIN-MENU.
           DISPLAY ' '
           DISPLAY WD-DASH-LINE
           DISPLAY '  MAIN MENU'
           DISPLAY WD-DASH-LINE
           DISPLAY '  1. DEPOSIT'
           DISPLAY '  2. WITHDRAWAL'
           DISPLAY '  3. BALANCE INQUIRY'
           DISPLAY '  4. CLIENT ACCOUNT DETAIL'
           DISPLAY '  5. LIST CLIENTS (20 AT A TIME)'
           DISPLAY '  6. DAILY SUMMARY REPORT'
           DISPLAY '  7. RESET DAILY LIMITS (END OF DAY)'
           DISPLAY '  8. TRANSACTION LOG (LAST 20)'
           DISPLAY '  X. EXIT'
           DISPLAY WD-DASH-LINE
           DISPLAY '  CHOICE: ' WITH NO ADVANCING
           ACCEPT WW-MENU-CHOICE
           EVALUATE WW-MENU-CHOICE
               WHEN '1'
                   PERFORM 3000-PROCESS-DEPOSIT
               WHEN '2'
                   PERFORM 4000-PROCESS-WITHDRAWAL
               WHEN '3'
                   PERFORM 5000-BALANCE-INQUIRY
               WHEN '4'
                   PERFORM 6000-ACCOUNT-DETAIL
               WHEN '5'
                   PERFORM 7000-LIST-CLIENTS
               WHEN '6'
                   PERFORM 8000-DAILY-SUMMARY
               WHEN '7'
                   PERFORM 9500-RESET-DAILY-LIMITS
               WHEN '8'
                   PERFORM 9600-SHOW-TX-LOG
               WHEN 'X'
                   MOVE 'N' TO WW-RUN-FLAG
               WHEN 'x'
                   MOVE 'N' TO WW-RUN-FLAG
               WHEN OTHER
                   DISPLAY '  *** INVALID CHOICE ***'
           END-EVALUATE
           .

      *================================================================*
      *  DEPOSIT PROCESSING                                             *
      *================================================================*

       3000-PROCESS-DEPOSIT.
           MOVE 'D' TO WW-CURRENT-OP
           DISPLAY WD-DASH-LINE
           DISPLAY '  DEPOSIT'
           DISPLAY WD-DASH-LINE
           DISPLAY '  CLIENT ID (0=CANCEL): ' WITH NO ADVANCING
           ACCEPT WW-SEARCH-ID
           IF WW-SEARCH-ID = 0
               DISPLAY '  OPERATION CANCELLED.'
               EXIT PARAGRAPH
           END-IF
           PERFORM 9000-FIND-CLIENT
           IF WW-FOUND-FLAG = 'N'
               DISPLAY '  *** CLIENT NOT FOUND: ' WW-SEARCH-ID
               EXIT PARAGRAPH
           END-IF
           PERFORM 9100-SHOW-CLIENT-HEADER
           MOVE DB-BALANCE(WW-FOUND-IDX) TO WD-BALANCE
           DISPLAY '  CURRENT BALANCE : ' WD-BALANCE
           DISPLAY '  AMOUNT (0=CANCEL): ' WITH NO ADVANCING
           ACCEPT WW-AMOUNT
           IF WW-AMOUNT = 0
               DISPLAY '  OPERATION CANCELLED.'
               EXIT PARAGRAPH
           END-IF
           PERFORM 3100-VALIDATE-DEPOSIT
           IF WW-RESULT = 'OK'
               PERFORM 3200-APPLY-DEPOSIT
           ELSE
               DISPLAY '  *** REJECTED: ' WW-ERROR-MSG
           END-IF
           PERFORM 9200-LOG-TRANSACTION
           .

      *----------------------------------------------------------------*
       3100-VALIDATE-DEPOSIT.
           MOVE 'OK' TO WW-RESULT
           MOVE SPACES TO WW-ERROR-MSG
           IF DB-FROZEN(WW-FOUND-IDX)
               MOVE 'RJ' TO WW-RESULT
               MOVE 'ACCOUNT FROZEN - VISIT BRANCH TO UNFREEZE'
                   TO WW-ERROR-MSG
               EXIT PARAGRAPH
           END-IF
           IF DB-CLOSED(WW-FOUND-IDX)
               MOVE 'RJ' TO WW-RESULT
               MOVE 'ACCOUNT IS PERMANENTLY CLOSED'
                   TO WW-ERROR-MSG
               EXIT PARAGRAPH
           END-IF
           IF WW-AMOUNT < BR-MIN-TX-AMOUNT
               MOVE 'RJ' TO WW-RESULT
               MOVE 'AMOUNT BELOW MINIMUM DEPOSIT OF $1.00'
                   TO WW-ERROR-MSG
               EXIT PARAGRAPH
           END-IF
           IF DB-VIP(WW-FOUND-IDX)
               IF WW-AMOUNT > BR-VIP-MAX-DEP-SINGLE
                   MOVE 'RJ' TO WW-RESULT
                   MOVE 'EXCEEDS VIP SINGLE DEPOSIT CAP $250,000.00'
                       TO WW-ERROR-MSG
                   EXIT PARAGRAPH
               END-IF
           ELSE
               IF WW-AMOUNT > BR-MAX-DEP-SINGLE
                   MOVE 'RJ' TO WW-RESULT
                   MOVE 'EXCEEDS REGULAR SINGLE DEPOSIT CAP $50,000'
                       TO WW-ERROR-MSG
                   EXIT PARAGRAPH
               END-IF
           END-IF
           COMPUTE WW-AVAIL-DEP =
               DB-DAILY-DEP(WW-FOUND-IDX) + WW-AMOUNT
           IF DB-VIP(WW-FOUND-IDX)
               IF WW-AVAIL-DEP > BR-VIP-MAX-DEP-DAILY
                   MOVE 'RJ' TO WW-RESULT
                   MOVE 'VIP DAILY DEPOSIT LIMIT REACHED $500,000'
                       TO WW-ERROR-MSG
                   EXIT PARAGRAPH
               END-IF
           ELSE
               IF WW-AVAIL-DEP > BR-MAX-DEP-DAILY
                   MOVE 'RJ' TO WW-RESULT
                   MOVE 'DAILY DEPOSIT LIMIT REACHED $100,000.00'
                       TO WW-ERROR-MSG
                   EXIT PARAGRAPH
               END-IF
           END-IF
           .

      *----------------------------------------------------------------*
       3200-APPLY-DEPOSIT.
           COMPUTE DB-BALANCE(WW-FOUND-IDX) =
               DB-BALANCE(WW-FOUND-IDX) + WW-AMOUNT
           ADD WW-AMOUNT TO DB-DAILY-DEP(WW-FOUND-IDX)
           ADD 1 TO DB-TX-COUNT(WW-FOUND-IDX)
           MOVE WW-DATE-SIM TO DB-LAST-TX-DATE(WW-FOUND-IDX)
           MOVE 'D' TO DB-LAST-TX-TYPE(WW-FOUND-IDX)
           MOVE WW-AMOUNT TO DB-LAST-TX-AMT(WW-FOUND-IDX)
           IF DB-BALANCE(WW-FOUND-IDX) > BR-VIP-THRESHOLD
               MOVE 'V' TO DB-ACCT-TYPE(WW-FOUND-IDX)
           END-IF
           MOVE WW-AMOUNT TO WD-AMOUNT
           MOVE DB-BALANCE(WW-FOUND-IDX) TO WD-BALANCE
           DISPLAY '  >> DEPOSIT APPROVED <<'
           DISPLAY '  AMOUNT DEPOSITED : ' WD-AMOUNT
           DISPLAY '  NEW BALANCE      : ' WD-BALANCE
           .

      *================================================================*
      *  WITHDRAWAL PROCESSING                                          *
      *================================================================*

       4000-PROCESS-WITHDRAWAL.
           MOVE 'W' TO WW-CURRENT-OP
           DISPLAY WD-DASH-LINE
           DISPLAY '  WITHDRAWAL'
           DISPLAY WD-DASH-LINE
           DISPLAY '  CLIENT ID (0=CANCEL): ' WITH NO ADVANCING
           ACCEPT WW-SEARCH-ID
           IF WW-SEARCH-ID = 0
               DISPLAY '  OPERATION CANCELLED.'
               EXIT PARAGRAPH
           END-IF
           PERFORM 9000-FIND-CLIENT
           IF WW-FOUND-FLAG = 'N'
               DISPLAY '  *** CLIENT NOT FOUND: ' WW-SEARCH-ID
               EXIT PARAGRAPH
           END-IF
           PERFORM 9100-SHOW-CLIENT-HEADER
           MOVE DB-BALANCE(WW-FOUND-IDX) TO WD-BALANCE
           DISPLAY '  CURRENT BALANCE : ' WD-BALANCE
           DISPLAY '  AMOUNT (0=CANCEL): ' WITH NO ADVANCING
           ACCEPT WW-AMOUNT
           IF WW-AMOUNT = 0
               DISPLAY '  OPERATION CANCELLED.'
               EXIT PARAGRAPH
           END-IF
           PERFORM 4100-VALIDATE-WITHDRAWAL
           IF WW-RESULT = 'OK'
               PERFORM 4200-APPLY-WITHDRAWAL
           ELSE
               DISPLAY '  *** REJECTED: ' WW-ERROR-MSG
           END-IF
           PERFORM 9200-LOG-TRANSACTION
           .

      *----------------------------------------------------------------*
       4100-VALIDATE-WITHDRAWAL.
           MOVE 'OK' TO WW-RESULT
           MOVE SPACES TO WW-ERROR-MSG
           IF DB-FROZEN(WW-FOUND-IDX)
               MOVE 'RJ' TO WW-RESULT
               MOVE 'ACCOUNT FROZEN - VISIT BRANCH TO UNFREEZE'
                   TO WW-ERROR-MSG
               EXIT PARAGRAPH
           END-IF
           IF DB-CLOSED(WW-FOUND-IDX)
               MOVE 'RJ' TO WW-RESULT
               MOVE 'ACCOUNT IS PERMANENTLY CLOSED'
                   TO WW-ERROR-MSG
               EXIT PARAGRAPH
           END-IF
           IF WW-AMOUNT < BR-MIN-TX-AMOUNT
               MOVE 'RJ' TO WW-RESULT
               MOVE 'AMOUNT BELOW MINIMUM WITHDRAWAL OF $1.00'
                   TO WW-ERROR-MSG
               EXIT PARAGRAPH
           END-IF
           IF DB-VIP(WW-FOUND-IDX)
               IF WW-AMOUNT > BR-VIP-MAX-WD-SINGLE
                   MOVE 'RJ' TO WW-RESULT
                   MOVE 'EXCEEDS VIP SINGLE WITHDRAWAL CAP $50,000'
                       TO WW-ERROR-MSG
                   EXIT PARAGRAPH
               END-IF
           ELSE
               IF WW-AMOUNT > BR-MAX-WD-SINGLE
                   MOVE 'RJ' TO WW-RESULT
                   MOVE 'EXCEEDS REGULAR SINGLE WITHDRAWAL CAP $10K'
                       TO WW-ERROR-MSG
                   EXIT PARAGRAPH
               END-IF
           END-IF
           COMPUTE WW-AVAIL-WD =
               DB-DAILY-WD(WW-FOUND-IDX) + WW-AMOUNT
           IF DB-VIP(WW-FOUND-IDX)
               IF WW-AVAIL-WD > BR-VIP-MAX-WD-DAILY
                   MOVE 'RJ' TO WW-RESULT
                   MOVE 'VIP DAILY WITHDRAWAL LIMIT REACHED $100,000'
                       TO WW-ERROR-MSG
                   EXIT PARAGRAPH
               END-IF
           ELSE
               IF WW-AVAIL-WD > BR-MAX-WD-DAILY
                   MOVE 'RJ' TO WW-RESULT
                   MOVE 'DAILY WITHDRAWAL LIMIT REACHED $20,000.00'
                       TO WW-ERROR-MSG
                   EXIT PARAGRAPH
               END-IF
           END-IF
           COMPUTE WW-NEW-BALANCE =
               DB-BALANCE(WW-FOUND-IDX) - WW-AMOUNT
           IF WW-NEW-BALANCE < BR-MIN-BALANCE
               MOVE 'RJ' TO WW-RESULT
               MOVE 'WOULD BREACH MINIMUM REQUIRED BALANCE $100.00'
                   TO WW-ERROR-MSG
               EXIT PARAGRAPH
           END-IF
           IF WW-NEW-BALANCE < 0
               MOVE 'RJ' TO WW-RESULT
               MOVE 'INSUFFICIENT FUNDS - OVERDRAFT NOT PERMITTED'
                   TO WW-ERROR-MSG
               EXIT PARAGRAPH
           END-IF
           .

      *----------------------------------------------------------------*
       4200-APPLY-WITHDRAWAL.
           COMPUTE DB-BALANCE(WW-FOUND-IDX) =
               DB-BALANCE(WW-FOUND-IDX) - WW-AMOUNT
           ADD WW-AMOUNT TO DB-DAILY-WD(WW-FOUND-IDX)
           ADD 1 TO DB-TX-COUNT(WW-FOUND-IDX)
           MOVE WW-DATE-SIM TO DB-LAST-TX-DATE(WW-FOUND-IDX)
           MOVE 'W' TO DB-LAST-TX-TYPE(WW-FOUND-IDX)
           MOVE WW-AMOUNT TO DB-LAST-TX-AMT(WW-FOUND-IDX)
           IF DB-VIP(WW-FOUND-IDX)
               IF DB-BALANCE(WW-FOUND-IDX) < BR-VIP-THRESHOLD
                   MOVE 'R' TO DB-ACCT-TYPE(WW-FOUND-IDX)
                   DISPLAY '  NOTE: ACCOUNT DOWNGRADED VIP -> REGULAR'
               END-IF
           END-IF
           MOVE WW-AMOUNT TO WD-AMOUNT
           MOVE DB-BALANCE(WW-FOUND-IDX) TO WD-BALANCE
           DISPLAY '  >> WITHDRAWAL APPROVED <<'
           DISPLAY '  AMOUNT WITHDRAWN : ' WD-AMOUNT
           DISPLAY '  NEW BALANCE      : ' WD-BALANCE
           .

      *================================================================*
      *  BALANCE INQUIRY                                                *
      *================================================================*

       5000-BALANCE-INQUIRY.
           DISPLAY WD-DASH-LINE
           DISPLAY '  BALANCE INQUIRY'
           DISPLAY WD-DASH-LINE
           DISPLAY '  CLIENT ID (0=CANCEL): ' WITH NO ADVANCING
           ACCEPT WW-SEARCH-ID
           IF WW-SEARCH-ID = 0
               DISPLAY '  CANCELLED.'
               EXIT PARAGRAPH
           END-IF
           PERFORM 9000-FIND-CLIENT
           IF WW-FOUND-FLAG = 'N'
               DISPLAY '  *** CLIENT NOT FOUND: ' WW-SEARCH-ID
               EXIT PARAGRAPH
           END-IF
           PERFORM 9100-SHOW-CLIENT-HEADER
           MOVE DB-BALANCE(WW-FOUND-IDX) TO WD-BALANCE
           DISPLAY '  CURRENT BALANCE  : ' WD-BALANCE
           MOVE DB-DAILY-WD(WW-FOUND-IDX) TO WD-DAILY-WD
           DISPLAY '  WITHDRAWN TODAY  : ' WD-DAILY-WD
           MOVE DB-DAILY-DEP(WW-FOUND-IDX) TO WD-DAILY-DEP
           DISPLAY '  DEPOSITED TODAY  : ' WD-DAILY-DEP
           DISPLAY '  TOTAL TX ON ACCT : '
               DB-TX-COUNT(WW-FOUND-IDX)
           .

      *================================================================*
      *  ACCOUNT DETAIL                                                 *
      *================================================================*

       6000-ACCOUNT-DETAIL.
           DISPLAY WD-DASH-LINE
           DISPLAY '  ACCOUNT DETAIL'
           DISPLAY WD-DASH-LINE
           DISPLAY '  CLIENT ID (0=CANCEL): ' WITH NO ADVANCING
           ACCEPT WW-SEARCH-ID
           IF WW-SEARCH-ID = 0
               DISPLAY '  CANCELLED.'
               EXIT PARAGRAPH
           END-IF
           PERFORM 9000-FIND-CLIENT
           IF WW-FOUND-FLAG = 'N'
               DISPLAY '  *** CLIENT NOT FOUND: ' WW-SEARCH-ID
               EXIT PARAGRAPH
           END-IF
           PERFORM 9300-DISPLAY-FULL-RECORD
           .

      *================================================================*
      *  CLIENT LIST                                                    *
      *================================================================*

       7000-LIST-CLIENTS.
           DISPLAY WD-DASH-LINE
           DISPLAY '  CLIENT LIST  (PAGE: 20 RECORDS)'
           DISPLAY WD-DASH-LINE
           DISPLAY '  START FROM RECORD # (1-1000): '
               WITH NO ADVANCING
           ACCEPT WW-PAGE-START
           IF WW-PAGE-START < 1 OR WW-PAGE-START > 1000
               MOVE 1 TO WW-PAGE-START
           END-IF
           COMPUTE WW-PAGE-END = WW-PAGE-START + WW-PAGE-LIMIT - 1
           IF WW-PAGE-END > DB-CLIENT-COUNT
               MOVE DB-CLIENT-COUNT TO WW-PAGE-END
           END-IF
           DISPLAY ' '
           DISPLAY '  IDX  CLIENT-ID  LAST NAME        FIRST'
               '      BALANCE           ST TY'
           DISPLAY WD-DASH-LINE
           PERFORM VARYING WW-LOOP-CTR
               FROM WW-PAGE-START BY 1
               UNTIL WW-LOOP-CTR > WW-PAGE-END
               MOVE DB-BALANCE(WW-LOOP-CTR) TO WD-BALANCE
               DISPLAY '  '
                   WW-LOOP-CTR '  '
                   DB-CLIENT-ID(WW-LOOP-CTR) '  '
                   DB-LAST-NAME(WW-LOOP-CTR)
                   DB-FIRST-NAME(WW-LOOP-CTR) '  '
                   WD-BALANCE '  '
                   DB-STATUS(WW-LOOP-CTR) '  '
                   DB-ACCT-TYPE(WW-LOOP-CTR)
           END-PERFORM
           DISPLAY WD-DASH-LINE
           DISPLAY '  RECORDS ' WW-PAGE-START ' TO '
               WW-PAGE-END ' OF ' DB-CLIENT-COUNT
           .

      *================================================================*
      *  DAILY SUMMARY REPORT                                           *
      *================================================================*

       8000-DAILY-SUMMARY.
           DISPLAY WD-DASH-LINE
           DISPLAY '  DAILY SUMMARY - ' WW-DATE-SIM
           DISPLAY WD-DASH-LINE
           PERFORM 8100-CALC-TOTALS
           DISPLAY WD-DASH-LINE
           PERFORM 8200-SHOW-STATUS-COUNTS
           .

      *----------------------------------------------------------------*
       8100-CALC-TOTALS.
           MOVE ZEROS TO WW-TOTAL-DEP-DAY
           MOVE ZEROS TO WW-TOTAL-WD-DAY
           PERFORM VARYING WW-LOOP-CTR FROM 1 BY 1
               UNTIL WW-LOOP-CTR > DB-CLIENT-COUNT
               ADD DB-DAILY-DEP(WW-LOOP-CTR) TO WW-TOTAL-DEP-DAY
               ADD DB-DAILY-WD(WW-LOOP-CTR) TO WW-TOTAL-WD-DAY
           END-PERFORM
           MOVE WW-TOTAL-DEP-DAY TO WD-DAILY-DEP
           MOVE WW-TOTAL-WD-DAY TO WD-DAILY-WD
           DISPLAY '  TOTAL DEPOSITS TODAY    : ' WD-DAILY-DEP
           DISPLAY '  TOTAL WITHDRAWALS TODAY : ' WD-DAILY-WD
           DISPLAY '  TOTAL TRANSACTIONS LOGGED: ' TX-TOTAL-COUNT
           .

      *----------------------------------------------------------------*
       8200-SHOW-STATUS-COUNTS.
           MOVE ZEROS TO WW-LOOP-CTR
           MOVE 0 TO WW-AVAIL-DEP
           MOVE 0 TO WW-AVAIL-WD
           MOVE 0 TO WW-NEW-BALANCE
           PERFORM VARYING WW-LOOP-CTR FROM 1 BY 1
               UNTIL WW-LOOP-CTR > DB-CLIENT-COUNT
               EVALUATE DB-STATUS(WW-LOOP-CTR)
                   WHEN 'A'
                       ADD 1 TO WW-AVAIL-DEP
                   WHEN 'F'
                       ADD 1 TO WW-AVAIL-WD
                   WHEN 'C'
                       ADD 1 TO WW-NEW-BALANCE
               END-EVALUATE
           END-PERFORM
           DISPLAY '  ACTIVE ACCOUNTS         : ' WW-AVAIL-DEP
           DISPLAY '  FROZEN ACCOUNTS         : ' WW-AVAIL-WD
           DISPLAY '  CLOSED ACCOUNTS         : ' WW-NEW-BALANCE
           .

      *================================================================*
      *  SHARED SUBROUTINES                                             *
      *================================================================*

       9000-FIND-CLIENT.
           MOVE 'N' TO WW-FOUND-FLAG
           MOVE 0 TO WW-FOUND-IDX
           PERFORM VARYING WW-LOOP-CTR FROM 1 BY 1
               UNTIL WW-LOOP-CTR > DB-CLIENT-COUNT
                   OR WW-FOUND-FLAG = 'Y'
               IF DB-CLIENT-ID(WW-LOOP-CTR) = WW-SEARCH-ID
                   MOVE 'Y' TO WW-FOUND-FLAG
                   MOVE WW-LOOP-CTR TO WW-FOUND-IDX
               END-IF
           END-PERFORM
           .

      *----------------------------------------------------------------*
       9100-SHOW-CLIENT-HEADER.
           EVALUATE DB-STATUS(WW-FOUND-IDX)
               WHEN 'A'  MOVE 'ACTIVE  ' TO WW-STATUS-LABEL
               WHEN 'F'  MOVE 'FROZEN  ' TO WW-STATUS-LABEL
               WHEN 'C'  MOVE 'CLOSED  ' TO WW-STATUS-LABEL
               WHEN OTHER MOVE '?       ' TO WW-STATUS-LABEL
           END-EVALUATE
           EVALUATE DB-ACCT-TYPE(WW-FOUND-IDX)
               WHEN 'V'  MOVE 'VIP     ' TO WW-TYPE-LABEL
               WHEN 'R'  MOVE 'REGULAR ' TO WW-TYPE-LABEL
               WHEN OTHER MOVE '?       ' TO WW-TYPE-LABEL
           END-EVALUATE
           DISPLAY '  '
               DB-FIRST-NAME(WW-FOUND-IDX) ' '
               DB-LAST-NAME(WW-FOUND-IDX)
               '   ID#' DB-CLIENT-ID(WW-FOUND-IDX)
               '   ' WW-STATUS-LABEL
               '   ' WW-TYPE-LABEL
           .

      *----------------------------------------------------------------*
       9200-LOG-TRANSACTION.
           ADD 1 TO TX-TOTAL-COUNT
           COMPUTE WW-TX-SLOT =
               FUNCTION MOD(TX-TOTAL-COUNT - 1, BR-MAX-TX-LOG) + 1
           MOVE TX-NEXT-ID        TO TX-ID(WW-TX-SLOT)
           ADD 1 TO TX-NEXT-ID
           MOVE WW-DATE-SIM       TO TX-DATE(WW-TX-SLOT)
           MOVE WW-TIME-SIM       TO TX-TIME(WW-TX-SLOT)
           MOVE DB-CLIENT-ID(WW-FOUND-IDX)
                                  TO TX-CLIENT-ID(WW-TX-SLOT)
           MOVE WW-CURRENT-OP     TO TX-TYPE(WW-TX-SLOT)
           MOVE WW-AMOUNT         TO TX-AMOUNT(WW-TX-SLOT)
           MOVE DB-BALANCE(WW-FOUND-IDX)
                                  TO TX-BAL-AFTER(WW-TX-SLOT)
           MOVE WW-RESULT         TO TX-RESULT(WW-TX-SLOT)
           IF WW-RESULT NOT = 'OK'
               MOVE WW-ERROR-MSG  TO TX-REJECT-REASON(WW-TX-SLOT)
           ELSE
               MOVE SPACES        TO TX-REJECT-REASON(WW-TX-SLOT)
           END-IF
           .

      *----------------------------------------------------------------*
       9300-DISPLAY-FULL-RECORD.
           DISPLAY WD-DASH-LINE
           DISPLAY '  == FULL ACCOUNT RECORD =='
           DISPLAY WD-DASH-LINE
           DISPLAY '  CLIENT ID      : '
               DB-CLIENT-ID(WW-FOUND-IDX)
           DISPLAY '  LAST NAME      : '
               DB-LAST-NAME(WW-FOUND-IDX)
           DISPLAY '  FIRST NAME     : '
               DB-FIRST-NAME(WW-FOUND-IDX)
           MOVE DB-BALANCE(WW-FOUND-IDX) TO WD-BALANCE
           DISPLAY '  BALANCE        : ' WD-BALANCE
           DISPLAY '  STATUS         : '
               DB-STATUS(WW-FOUND-IDX)
               '   (A=ACTIVE  F=FROZEN  C=CLOSED)'
           DISPLAY '  ACCOUNT TYPE   : '
               DB-ACCT-TYPE(WW-FOUND-IDX)
               '   (R=REGULAR  V=VIP)'
           DISPLAY '  DATE OPENED    : '
               DB-OPEN-DATE(WW-FOUND-IDX)
           DISPLAY '  TOTAL TX COUNT : '
               DB-TX-COUNT(WW-FOUND-IDX)
           MOVE DB-DAILY-WD(WW-FOUND-IDX) TO WD-DAILY-WD
           DISPLAY '  WITHDRAWN TODAY: ' WD-DAILY-WD
           MOVE DB-DAILY-DEP(WW-FOUND-IDX) TO WD-DAILY-DEP
           DISPLAY '  DEPOSITED TODAY: ' WD-DAILY-DEP
           DISPLAY '  LAST TX DATE   : '
               DB-LAST-TX-DATE(WW-FOUND-IDX)
           DISPLAY '  LAST TX TYPE   : '
               DB-LAST-TX-TYPE(WW-FOUND-IDX)
               '  (D=DEPOSIT  W=WITHDRAWAL)'
           MOVE DB-LAST-TX-AMT(WW-FOUND-IDX) TO WD-AMOUNT
           DISPLAY '  LAST TX AMOUNT : ' WD-AMOUNT
           DISPLAY WD-DASH-LINE
           DISPLAY '  -- APPLICABLE LIMITS --'
           IF DB-VIP(WW-FOUND-IDX)
               MOVE BR-VIP-MAX-DEP-SINGLE TO WD-AMOUNT
               DISPLAY '  MAX SINGLE DEP : ' WD-AMOUNT '  (VIP)'
               MOVE BR-VIP-MAX-WD-SINGLE TO WD-AMOUNT
               DISPLAY '  MAX SINGLE WD  : ' WD-AMOUNT '  (VIP)'
               MOVE BR-VIP-MAX-DEP-DAILY TO WD-AMOUNT
               DISPLAY '  DAILY DEP LIMIT: ' WD-AMOUNT '  (VIP)'
               MOVE BR-VIP-MAX-WD-DAILY TO WD-AMOUNT
               DISPLAY '  DAILY WD LIMIT : ' WD-AMOUNT '  (VIP)'
           ELSE
               MOVE BR-MAX-DEP-SINGLE TO WD-AMOUNT
               DISPLAY '  MAX SINGLE DEP : ' WD-AMOUNT '  (REG)'
               MOVE BR-MAX-WD-SINGLE TO WD-AMOUNT
               DISPLAY '  MAX SINGLE WD  : ' WD-AMOUNT '  (REG)'
               MOVE BR-MAX-DEP-DAILY TO WD-AMOUNT
               DISPLAY '  DAILY DEP LIMIT: ' WD-AMOUNT '  (REG)'
               MOVE BR-MAX-WD-DAILY TO WD-AMOUNT
               DISPLAY '  DAILY WD LIMIT : ' WD-AMOUNT '  (REG)'
           END-IF
           MOVE BR-MIN-BALANCE TO WD-AMOUNT
           DISPLAY '  MIN BALANCE REQ: ' WD-AMOUNT
           DISPLAY WD-DASH-LINE
           .

      *================================================================*
      *  END-OF-DAY RESET                                               *
      *================================================================*

       9500-RESET-DAILY-LIMITS.
           DISPLAY WD-DASH-LINE
           DISPLAY '  RESET DAILY LIMITS - NEW BUSINESS DAY'
           DISPLAY WD-DASH-LINE
           DISPLAY '  CONFIRM RESET? (Y/N): ' WITH NO ADVANCING
           ACCEPT WW-MENU-CHOICE
           IF WW-MENU-CHOICE NOT = 'Y' AND
              WW-MENU-CHOICE NOT = 'y'
               DISPLAY '  RESET CANCELLED.'
               EXIT PARAGRAPH
           END-IF
           PERFORM VARYING WW-LOOP-CTR FROM 1 BY 1
               UNTIL WW-LOOP-CTR > DB-CLIENT-COUNT
               MOVE ZEROS TO DB-DAILY-WD(WW-LOOP-CTR)
               MOVE ZEROS TO DB-DAILY-DEP(WW-LOOP-CTR)
           END-PERFORM
           DISPLAY '  DAILY LIMITS RESET FOR ALL '
               DB-CLIENT-COUNT ' ACCOUNTS.'
           DISPLAY '  NEW BUSINESS DAY COMMENCED.'
           .

      *================================================================*
      *  TRANSACTION LOG DISPLAY                                        *
      *================================================================*

       9600-SHOW-TX-LOG.
           DISPLAY WD-DASH-LINE
           DISPLAY '  TRANSACTION LOG - LAST 20 ENTRIES'
           DISPLAY WD-DASH-LINE
           IF TX-TOTAL-COUNT = 0
               DISPLAY '  NO TRANSACTIONS RECORDED YET.'
               EXIT PARAGRAPH
           END-IF
           DISPLAY '  TXID      DATE        CLIENT  OP  AMOUNT'
               '           RESULT'
           DISPLAY WD-DASH-LINE
           COMPUTE WW-PAGE-START = TX-TOTAL-COUNT - 19
           IF WW-PAGE-START < 1
               MOVE 1 TO WW-PAGE-START
           END-IF
           PERFORM VARYING WW-LOOP-CTR
               FROM WW-PAGE-START BY 1
               UNTIL WW-LOOP-CTR > TX-TOTAL-COUNT
               COMPUTE WW-TX-SLOT =
                   FUNCTION MOD(WW-LOOP-CTR - 1, BR-MAX-TX-LOG) + 1
               MOVE TX-AMOUNT(WW-TX-SLOT) TO WD-AMOUNT
               DISPLAY '  '
                   TX-ID(WW-TX-SLOT) '  '
                   TX-DATE(WW-TX-SLOT) '  '
                   TX-CLIENT-ID(WW-TX-SLOT) '   '
                   TX-TYPE(WW-TX-SLOT) '  '
                   WD-AMOUNT '  '
                   TX-RESULT(WW-TX-SLOT)
           END-PERFORM
           DISPLAY WD-DASH-LINE
           .

      *================================================================*
      *  END PROGRAM                                                    *
      *================================================================*

       9999-END-PROGRAM.
           DISPLAY WD-SEP-LINE
           DISPLAY '  SESSION CLOSED'
           DISPLAY '  TRANSACTIONS THIS SESSION : ' TX-TOTAL-COUNT
           DISPLAY '  BANK OF COBOL - HAVE A GOOD DAY'
           DISPLAY WD-SEP-LINE
           .

      *================================================================*
      *  END OF PROGRAM: BANKING-SYSTEM                                *
      *================================================================*
