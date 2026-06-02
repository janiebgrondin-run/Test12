# Bank of COBOL — Core Banking System: Business Rules

**Source:** BANKING-SYSTEM (BANKING.cbl)
**Purpose:** Business rules extracted for system migration — written for business analyst review
**Operations supported:** Deposit and Withdrawal only

---

## Table of Contents

1. [Account Data Model](#1-account-data-model)
2. [Account Opening & Initialization](#2-account-opening--initialization)
3. [Account Status Management](#3-account-status-management)
4. [Account Tier Classification (Regular vs VIP)](#4-account-tier-classification-regular-vs-vip)
5. [Deposit Processing](#5-deposit-processing)
6. [Withdrawal Processing](#6-withdrawal-processing)
7. [Transaction Limits Reference Table](#7-transaction-limits-reference-table)
8. [Account Tier Promotion & Demotion](#8-account-tier-promotion--demotion)
9. [Transaction Logging & Audit Trail](#9-transaction-logging--audit-trail)
10. [End-of-Day Processing](#10-end-of-day-processing)
11. [Inquiries & Reporting](#11-inquiries--reporting)
12. [System Capacity & Constraints](#12-system-capacity--constraints)

---

## 1. Account Data Model

Each client account holds the following information:

| Field | Description |
|---|---|
| Client ID | Unique 6-digit number assigned at account opening (starts at 100001) |
| Last Name | Up to 15 characters |
| First Name | Up to 10 characters |
| Balance | Current account balance (can be negative only in error — see withdrawal rules) |
| Status | ACTIVE, FROZEN, or CLOSED |
| Account Type | REGULAR or VIP |
| Daily Withdrawal Total | Cumulative withdrawals processed today (resets at end of day) |
| Daily Deposit Total | Cumulative deposits processed today (resets at end of day) |
| Date Opened | The date the account was opened |
| Total Transaction Count | Lifetime count of all transactions (approved and rejected) on the account |
| Last Transaction Date | Date of the most recent transaction attempt |
| Last Transaction Type | Whether the last transaction was a Deposit or Withdrawal |
| Last Transaction Amount | Dollar amount of the most recent transaction |

---

## 2. Account Opening & Initialization

**BR-001 — Client ID Assignment**
Every new account is assigned a unique 6-digit Client ID. IDs are assigned sequentially, beginning at **100001**.

**BR-002 — Opening Balance**
All new accounts are funded with an initial balance of **$500.00** at the time of opening.

**BR-003 — Account Type at Opening**
At the time of opening, the system evaluates the account balance to determine account type:
- If opening balance exceeds **$50,000.00**, the account is classified as **VIP**.
- Otherwise, the account is classified as **REGULAR**.

*(Note: With a standard opening balance of $500.00, all new accounts open as Regular unless a higher opening balance is applied.)*

**BR-004 — Daily Accumulators at Opening**
Daily withdrawal and deposit totals are initialized to **$0.00** at account opening.

---

## 3. Account Status Management

An account can be in one of three statuses. Status governs whether transactions are permitted.

### 3.1 Account Statuses

| Status | Code | Description |
|---|---|---|
| Active | A | Account is in good standing. All permitted transactions can be processed. |
| Frozen | F | Account has been suspended. No deposits or withdrawals are allowed. Customer must visit a branch to unfreeze. |
| Closed | C | Account is permanently closed. No transactions of any kind are permitted. |

**BR-005 — Frozen Account Restriction**
No transaction (deposit or withdrawal) may be processed on a Frozen account. The system rejects all attempts with the message:
> *"ACCOUNT FROZEN - VISIT BRANCH TO UNFREEZE"*

**BR-006 — Closed Account Restriction**
No transaction (deposit or withdrawal) may be processed on a Closed account. The system rejects all attempts with the message:
> *"ACCOUNT IS PERMANENTLY CLOSED"*

**BR-007 — Status Check is First Priority**
Account status is always validated **before** any amount or limit checks. If an account is Frozen or Closed, no further validation is performed — the transaction is immediately rejected.

---

## 4. Account Tier Classification (Regular vs VIP)

The system operates two account tiers with different transaction limits.

**BR-008 — VIP Qualification Threshold**
An account qualifies for VIP status when the account balance exceeds **$50,000.00**.

**BR-009 — Regular Account**
Any account with a balance of **$50,000.00 or less** is classified as Regular and is subject to Regular transaction limits.

**BR-010 — VIP Account**
Any account with a balance **above $50,000.00** is classified as VIP and is subject to VIP transaction limits (which are significantly higher).

---

## 5. Deposit Processing

Deposits are processed in the following validation sequence. Each rule is checked in order; the first failure immediately rejects the transaction.

### 5.1 Deposit Validation Sequence

**Step 1 — Account Status Check**
- If account is **FROZEN** → Reject. *(See BR-005)*
- If account is **CLOSED** → Reject. *(See BR-006)*

**Step 2 — Minimum Amount Check**

**BR-011 — Minimum Deposit Amount**
The minimum deposit amount is **$1.00**. Any deposit below this amount is rejected with:
> *"AMOUNT BELOW MINIMUM DEPOSIT OF $1.00"*

**Step 3 — Single Transaction Cap**

**BR-012 — Regular Account: Single Deposit Limit**
A Regular account may not receive more than **$50,000.00** in a single deposit transaction. Amounts exceeding this cap are rejected with:
> *"EXCEEDS REGULAR SINGLE DEPOSIT CAP $50,000"*

**BR-013 — VIP Account: Single Deposit Limit**
A VIP account may not receive more than **$250,000.00** in a single deposit transaction. Amounts exceeding this cap are rejected with:
> *"EXCEEDS VIP SINGLE DEPOSIT CAP $250,000.00"*

**Step 4 — Daily Cumulative Cap**

**BR-014 — Regular Account: Daily Deposit Limit**
The total of all deposits made to a Regular account in a single business day may not exceed **$100,000.00**. If this deposit would cause the daily total to exceed that amount, the transaction is rejected with:
> *"DAILY DEPOSIT LIMIT REACHED $100,000.00"*

**BR-015 — VIP Account: Daily Deposit Limit**
The total of all deposits made to a VIP account in a single business day may not exceed **$500,000.00**. If this deposit would cause the daily total to exceed that amount, the transaction is rejected with:
> *"VIP DAILY DEPOSIT LIMIT REACHED $500,000"*

### 5.2 Approved Deposit Processing

When a deposit passes all validations:
1. The deposit amount is added to the account balance.
2. The deposit amount is added to the account's daily deposit accumulator.
3. The transaction counter for the account is incremented by 1.
4. The last transaction date, type (Deposit), and amount are recorded on the account.
5. The system evaluates whether the new balance qualifies the account for VIP upgrade. *(See BR-016)*

---

## 6. Withdrawal Processing

Withdrawals are processed in the following validation sequence. Each rule is checked in order; the first failure immediately rejects the transaction.

### 6.1 Withdrawal Validation Sequence

**Step 1 — Account Status Check**
- If account is **FROZEN** → Reject. *(See BR-005)*
- If account is **CLOSED** → Reject. *(See BR-006)*

**Step 2 — Minimum Amount Check**

**BR-020 — Minimum Withdrawal Amount**
The minimum withdrawal amount is **$1.00**. Any withdrawal below this amount is rejected with:
> *"AMOUNT BELOW MINIMUM WITHDRAWAL OF $1.00"*

**Step 3 — Single Transaction Cap**

**BR-021 — Regular Account: Single Withdrawal Limit**
A Regular account may not withdraw more than **$10,000.00** in a single transaction. Amounts exceeding this cap are rejected with:
> *"EXCEEDS REGULAR SINGLE WITHDRAWAL CAP $10K"*

**BR-022 — VIP Account: Single Withdrawal Limit**
A VIP account may not withdraw more than **$50,000.00** in a single transaction. Amounts exceeding this cap are rejected with:
> *"EXCEEDS VIP SINGLE WITHDRAWAL CAP $50,000"*

**Step 4 — Daily Cumulative Cap**

**BR-023 — Regular Account: Daily Withdrawal Limit**
The total of all withdrawals made from a Regular account in a single business day may not exceed **$20,000.00**. If this withdrawal would cause the daily total to exceed that amount, the transaction is rejected with:
> *"DAILY WITHDRAWAL LIMIT REACHED $20,000.00"*

**BR-024 — VIP Account: Daily Withdrawal Limit**
The total of all withdrawals made from a VIP account in a single business day may not exceed **$100,000.00**. If this withdrawal would cause the daily total to exceed that amount, the transaction is rejected with:
> *"VIP DAILY WITHDRAWAL LIMIT REACHED $100,000"*

**Step 5 — Balance Adequacy Checks**

**BR-025 — Minimum Required Balance**
After a withdrawal, the account balance must not fall below **$100.00**. If the requested amount would bring the balance below this threshold, the transaction is rejected with:
> *"WOULD BREACH MINIMUM REQUIRED BALANCE $100.00"*

**BR-026 — No Overdraft**
The system does not permit overdrafts. If the requested amount would result in a negative balance, the transaction is rejected with:
> *"INSUFFICIENT FUNDS - OVERDRAFT NOT PERMITTED"*

*(Note: BR-025 is checked first. In practice, BR-026 would only be reached if the minimum balance were set to $0.00.)*

### 6.2 Approved Withdrawal Processing

When a withdrawal passes all validations:
1. The withdrawal amount is deducted from the account balance.
2. The withdrawal amount is added to the account's daily withdrawal accumulator.
3. The transaction counter for the account is incremented by 1.
4. The last transaction date, type (Withdrawal), and amount are recorded on the account.
5. The system evaluates whether the new balance requires the account to be downgraded from VIP to Regular. *(See BR-017)*

---

## 7. Transaction Limits Reference Table

| Limit | Regular Account | VIP Account |
|---|---|---|
| Minimum transaction amount | $1.00 | $1.00 |
| Maximum single deposit | $50,000.00 | $250,000.00 |
| Maximum single withdrawal | $10,000.00 | $50,000.00 |
| Maximum daily deposits (cumulative) | $100,000.00 | $500,000.00 |
| Maximum daily withdrawals (cumulative) | $20,000.00 | $100,000.00 |
| Minimum required balance | $100.00 | $100.00 |
| Overdraft permitted | No | No |

---

## 8. Account Tier Promotion & Demotion

Account type (Regular/VIP) is re-evaluated automatically after every approved transaction.

**BR-016 — Automatic VIP Upgrade After Deposit**
After a deposit is applied, if the account's new balance exceeds **$50,000.00** and the account is currently Regular, the account is automatically upgraded to **VIP**. The new VIP limits apply to all subsequent transactions within the same business day.

**BR-017 — Automatic VIP Downgrade After Withdrawal**
After a withdrawal is applied, if the account's new balance is **$50,000.00 or less** and the account is currently VIP, the account is automatically downgraded to **Regular**. The system notifies the operator:
> *"NOTE: ACCOUNT DOWNGRADED VIP -> REGULAR"*
The Regular limits apply to all subsequent transactions within the same business day.

**BR-018 — Tier Applies at Time of Transaction**
The account type at the moment of transaction submission determines which limits apply. A mid-day upgrade or downgrade takes effect immediately for all subsequent transactions.

---

## 9. Transaction Logging & Audit Trail

**BR-030 — All Transactions Are Logged**
Every transaction attempt — whether approved or rejected — is recorded in the transaction log. A rejected transaction is not applied to the account balance but is still written to the log.

**BR-031 — Transaction Log Contents**
Each log entry captures:
- Transaction ID (sequential, system-generated)
- Transaction Date
- Transaction Time
- Client ID
- Transaction Type (Deposit or Withdrawal)
- Amount
- Account Balance after the transaction (for approved transactions)
- Result: Approved (OK) or Rejected (RJ)
- Rejection Reason (if rejected)

**BR-032 — Circular Log Buffer**
The transaction log holds a maximum of **5,000 entries**. When the log is full, new entries overwrite the oldest entries (circular/ring buffer). The system retains the total transaction count across the lifetime of the session, even after entries are overwritten.

**BR-033 — Transaction IDs are Sequential**
Each log entry is assigned a unique, sequentially incrementing Transaction ID starting at 1. IDs are never reused within a session.

---

## 10. End-of-Day Processing

**BR-040 — Daily Limit Reset**
At the end of each business day, an authorized operator must manually trigger the end-of-day reset. This process:
1. Clears the daily withdrawal accumulator to **$0.00** for every account.
2. Clears the daily deposit accumulator to **$0.00** for every account.
3. Marks the beginning of a new business day.

**BR-041 — Confirmation Required**
The end-of-day reset requires explicit operator confirmation (Y/N prompt) before executing. If the operator does not confirm, the reset is cancelled and no data is changed.

**BR-042 — Reset Applies to All Accounts**
The daily reset applies simultaneously to **all accounts** in the database, regardless of account status or type. Frozen and Closed accounts also have their daily accumulators cleared.

**BR-043 — Daily Limits are Per Business Day**
Transaction limits (daily deposit cap and daily withdrawal cap) are calculated from the start of the current business day. After an end-of-day reset, every account starts the new day with $0.00 accumulated toward its daily limits.

---

## 11. Inquiries & Reporting

### 11.1 Balance Inquiry

**BR-050 — Balance Inquiry**
Any account (including Frozen and Closed) may be queried for its current balance. The inquiry displays:
- Current balance
- Total amount withdrawn today
- Total amount deposited today
- Lifetime transaction count

### 11.2 Account Detail

**BR-051 — Full Account Detail**
A full account record view displays all account fields plus the applicable transaction limits based on current account type (Regular or VIP), and the minimum required balance.

### 11.3 Client List

**BR-052 — Paginated Client List**
The client list is displayed **20 records at a time**. The operator selects a starting record number (1 to 1000). The display shows Client ID, name, balance, status, and account type for each account.

### 11.4 Daily Summary Report

**BR-053 — Daily Summary**
The daily summary report provides an aggregate view for the current business day:
- Total deposits across all accounts today
- Total withdrawals across all accounts today
- Total number of transactions logged in the session
- Count of accounts by status: Active, Frozen, Closed

### 11.5 Transaction Log View

**BR-054 — Transaction Log Display**
The operator can view the **most recent 20 transactions** from the transaction log. Entries show Transaction ID, date, Client ID, transaction type, amount, and result.

---

## 12. System Capacity & Constraints

| Parameter | Value |
|---|---|
| Maximum accounts in database | 1,000 |
| Maximum transaction log entries | 5,000 (circular — oldest overwritten) |
| First assigned Client ID | 100001 |
| Supported transaction types | Deposit, Withdrawal only |
| Overdraft facility | Not supported |
| Inter-account transfers | Not supported |
| Interest calculation | Not supported |
| Account creation via system | Not supported (pre-loaded) |
| Account closure via system | Not supported (status is pre-set) |

---

## 13. Migration Notes for Business Analysts

The following items are embedded as hardcoded values in the COBOL source and will need to be externalized as configurable parameters in the new system:

| Rule Reference | Parameter | Current Value | COBOL Variable |
|---|---|---|---|
| BR-025 | Minimum required balance | $100.00 | BR-MIN-BALANCE |
| BR-021 | Regular max single withdrawal | $10,000.00 | BR-MAX-WD-SINGLE |
| BR-012 | Regular max single deposit | $50,000.00 | BR-MAX-DEP-SINGLE |
| BR-023 | Regular max daily withdrawal | $20,000.00 | BR-MAX-WD-DAILY |
| BR-014 | Regular max daily deposit | $100,000.00 | BR-MAX-DEP-DAILY |
| BR-011/BR-020 | Minimum transaction amount | $1.00 | BR-MIN-TX-AMOUNT |
| BR-002 | Initial account balance | $500.00 | BR-INITIAL-BALANCE |
| BR-008 | VIP qualification threshold | $50,000.00 | BR-VIP-THRESHOLD |
| BR-022 | VIP max single withdrawal | $50,000.00 | BR-VIP-MAX-WD-SINGLE |
| BR-013 | VIP max single deposit | $250,000.00 | BR-VIP-MAX-DEP-SINGLE |
| BR-024 | VIP max daily withdrawal | $100,000.00 | BR-VIP-MAX-WD-DAILY |
| BR-015 | VIP max daily deposit | $500,000.00 | BR-VIP-MAX-DEP-DAILY |

**Key design decisions to resolve during migration:**

1. **VIP threshold logic is balance-based only.** There is no minimum tenure, credit score, or manual approval pathway — VIP status is granted and revoked automatically based solely on balance crossing the $50,000 threshold.

2. **End-of-day reset is manual.** The current system requires a human operator to trigger the daily limit reset. The new system will need to decide whether this is automated (scheduled batch job) or remains operator-initiated.

3. **Rejected transactions are fully logged.** The audit trail includes both approved and rejected attempts. This behavior must be preserved in the new system.

4. **No overdraft product exists.** The current system has no concept of an authorized overdraft. If the new system introduces overdraft, new business rules will be required.

5. **Frozen vs. Closed distinction.** Frozen is a temporary, reversible state that requires a branch visit to lift. Closed is permanent. The new system must preserve this distinction and implement the branch-visit workflow for unfreezing accounts.
