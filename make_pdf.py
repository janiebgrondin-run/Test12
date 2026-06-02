"""Convert BUSINESS_RULES.md to BUSINESS_RULES.pdf using reportlab."""

import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ── colour palette ──────────────────────────────────────────────────────────
DARK_BLUE   = colors.HexColor("#1a3a5c")
MID_BLUE    = colors.HexColor("#2e6da4")
LIGHT_BLUE  = colors.HexColor("#dce9f5")
ACCENT      = colors.HexColor("#e8f0f8")
RULE_AMBER  = colors.HexColor("#fff3cd")
RULE_BORDER = colors.HexColor("#ffc107")
GREY_LINE   = colors.HexColor("#cccccc")
WHITE       = colors.white
BLACK       = colors.black

# ── styles ───────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

styles = {
    "h1": S("h1", fontSize=22, textColor=WHITE,      spaceAfter=4,
            fontName="Helvetica-Bold", leading=28),
    "h1sub": S("h1sub", fontSize=11, textColor=colors.HexColor("#c8dff0"),
               fontName="Helvetica", leading=16),
    "h2": S("h2", fontSize=14, textColor=DARK_BLUE,  spaceBefore=18,
            spaceAfter=4, fontName="Helvetica-Bold",
            borderPad=4, leading=18),
    "h3": S("h3", fontSize=11, textColor=MID_BLUE,   spaceBefore=10,
            spaceAfter=3, fontName="Helvetica-Bold", leading=14),
    "body": S("body", fontSize=9.5, textColor=BLACK, spaceAfter=5,
              fontName="Helvetica", leading=14, leftIndent=0),
    "bullet": S("bullet", fontSize=9.5, textColor=BLACK, spaceAfter=3,
                fontName="Helvetica", leading=13, leftIndent=18,
                bulletIndent=6),
    "rule": S("rule", fontSize=9.5, textColor=colors.HexColor("#5a3e00"),
              fontName="Helvetica-Bold", leading=13, leftIndent=8),
    "rule_body": S("rule_body", fontSize=9.5, textColor=BLACK,
                   fontName="Helvetica", leading=13, leftIndent=8,
                   spaceAfter=2),
    "quote": S("quote", fontSize=9, textColor=colors.HexColor("#555555"),
               fontName="Helvetica-Oblique", leading=13, leftIndent=24,
               rightIndent=12, spaceAfter=4),
    "note": S("note", fontSize=8.5, textColor=colors.HexColor("#444444"),
              fontName="Helvetica-Oblique", leading=12, leftIndent=12),
    "toc": S("toc", fontSize=9.5, textColor=MID_BLUE,
             fontName="Helvetica", leading=16, leftIndent=12),
    "footer": S("footer", fontSize=7.5, textColor=colors.HexColor("#888888"),
                fontName="Helvetica", alignment=TA_CENTER),
}

TABLE_HDR  = TableStyle([
    ("BACKGROUND",  (0, 0), (-1, 0), DARK_BLUE),
    ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",    (0, 0), (-1, 0), 9),
    ("TOPPADDING",  (0, 0), (-1, 0), 6),
    ("BOTTOMPADDING",(0,0), (-1, 0), 6),
    ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE",    (0, 1), (-1, -1), 8.5),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ACCENT]),
    ("TOPPADDING",  (0, 1), (-1, -1), 5),
    ("BOTTOMPADDING",(0,1), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING",(0, 0), (-1, -1), 8),
    ("GRID",        (0, 0), (-1, -1), 0.5, GREY_LINE),
    ("VALIGN",      (0, 0), (-1, -1), "TOP"),
])

# ── helpers ──────────────────────────────────────────────────────────────────
def page_header_footer(canvas, doc):
    canvas.saveState()
    w, h = letter
    # header bar
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, h - 0.45*inch, w, 0.45*inch, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(WHITE)
    canvas.drawString(0.5*inch, h - 0.28*inch, "BANK OF COBOL — CORE BANKING SYSTEM: BUSINESS RULES")
    canvas.drawRightString(w - 0.5*inch, h - 0.28*inch, "MIGRATION REFERENCE DOCUMENT")
    # footer
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(w/2, 0.3*inch, f"Page {doc.page}  |  CONFIDENTIAL — FOR INTERNAL USE ONLY")
    canvas.setStrokeColor(GREY_LINE)
    canvas.line(0.5*inch, 0.45*inch, w - 0.5*inch, 0.45*inch)
    canvas.restoreState()

def hr(color=GREY_LINE, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceAfter=4, spaceBefore=4)

def rule_box(label, text, quote=None, note=None):
    """Amber-tinted box for individual business rules."""
    items = [Paragraph(label, styles["rule"])]
    if text:
        items.append(Paragraph(text, styles["rule_body"]))
    if quote:
        items.append(Paragraph(f'<i>"{quote}"</i>', styles["quote"]))
    if note:
        items.append(Paragraph(f"<i>Note: {note}</i>", styles["note"]))
    t = Table([[items]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), RULE_AMBER),
        ("BOX",          (0, 0), (-1, -1), 1, RULE_BORDER),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([t, Spacer(1, 5)])

def section_title(num, title):
    p = Paragraph(f"{num}. {title}", styles["h2"])
    return KeepTogether([hr(GREY_LINE, 0.5), p])

def sub_title(title):
    return Paragraph(title, styles["h3"])

def body(text):
    return Paragraph(text, styles["body"])

def bullet(text):
    return Paragraph(f"• {text}", styles["bullet"])

def make_table(headers, rows, col_widths):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TABLE_HDR)
    return t

# ── document assembly ────────────────────────────────────────────────────────
story = []
PAGE_W = letter[0] - inch  # usable width

# ── Cover block ──────────────────────────────────────────────────────────────
cover = Table(
    [[Paragraph("BANK OF COBOL", styles["h1"]),],
     [Paragraph("Core Banking System — Business Rules", styles["h1sub"])],
     [Paragraph("Migration Reference Document", styles["h1sub"])],
    ],
    colWidths=[PAGE_W]
)
cover.setStyle(TableStyle([
    ("BACKGROUND",   (0, 0), (-1, -1), DARK_BLUE),
    ("TOPPADDING",   (0, 0), (-1, -1), 14),
    ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ("LEFTPADDING",  (0, 0), (-1, -1), 16),
    ("RIGHTPADDING", (0, 0), (-1, -1), 16),
]))
story += [cover, Spacer(1, 6)]

meta = Table(
    [["Source Program:", "BANKING-SYSTEM (BANKING.cbl)"],
     ["Platform:",       "IBM Mainframe (COBOL)"],
     ["Prepared for:",   "System Migration — Business Analyst Review"],
     ["Operations:",     "Deposit and Withdrawal only"],
    ],
    colWidths=[1.6*inch, PAGE_W - 1.6*inch]
)
meta.setStyle(TableStyle([
    ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
    ("FONTSIZE",    (0, 0), (-1, -1), 9),
    ("TOPPADDING",  (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING",(0,0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("BACKGROUND",  (0, 0), (-1, -1), LIGHT_BLUE),
    ("GRID",        (0, 0), (-1, -1), 0.5, GREY_LINE),
]))
story += [meta, Spacer(1, 14)]

# ── Table of Contents ─────────────────────────────────────────────────────────
story.append(sub_title("Table of Contents"))
toc_items = [
    "1.  Account Data Model",
    "2.  Account Opening & Initialization",
    "3.  Account Status Management",
    "4.  Account Tier Classification (Regular vs VIP)",
    "5.  Deposit Processing",
    "6.  Withdrawal Processing",
    "7.  Transaction Limits Reference Table",
    "8.  Account Tier Promotion & Demotion",
    "9.  Transaction Logging & Audit Trail",
    "10. End-of-Day Processing",
    "11. Inquiries & Reporting",
    "12. System Capacity & Constraints",
    "13. Migration Notes for Business Analysts",
]
for item in toc_items:
    story.append(Paragraph(item, styles["toc"]))
story.append(Spacer(1, 12))

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Account Data Model
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("1", "Account Data Model"))
story.append(body("Each client account holds the following information:"))
story.append(Spacer(1, 4))
story.append(make_table(
    ["Field", "Description"],
    [
        ["Client ID",              "Unique 6-digit number assigned at account opening (starts at 100001)"],
        ["Last Name",              "Up to 15 characters"],
        ["First Name",             "Up to 10 characters"],
        ["Balance",                "Current account balance"],
        ["Status",                 "ACTIVE, FROZEN, or CLOSED"],
        ["Account Type",           "REGULAR or VIP"],
        ["Daily Withdrawal Total", "Cumulative withdrawals processed today (resets at end of day)"],
        ["Daily Deposit Total",    "Cumulative deposits processed today (resets at end of day)"],
        ["Date Opened",            "The date the account was opened"],
        ["Total Transaction Count","Lifetime count of all transactions (approved and rejected)"],
        ["Last Transaction Date",  "Date of the most recent transaction attempt"],
        ["Last Transaction Type",  "Whether the last transaction was a Deposit or Withdrawal"],
        ["Last Transaction Amount","Dollar amount of the most recent transaction"],
    ],
    [1.8*inch, PAGE_W - 1.8*inch]
))
story.append(Spacer(1, 10))

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Account Opening
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("2", "Account Opening & Initialization"))
story += [
    rule_box("BR-001 — Client ID Assignment",
             "Every new account is assigned a unique 6-digit Client ID. IDs are assigned "
             "sequentially, beginning at 100001."),
    rule_box("BR-002 — Opening Balance",
             "All new accounts are funded with an initial balance of $500.00 at the time of opening."),
    rule_box("BR-003 — Account Type at Opening",
             "At the time of opening, the system evaluates the account balance to determine account type: "
             "if the opening balance exceeds $50,000.00, the account is classified as VIP; otherwise Regular.",
             note="With a standard opening balance of $500.00, all new accounts open as Regular."),
    rule_box("BR-004 — Daily Accumulators at Opening",
             "Daily withdrawal and deposit totals are initialized to $0.00 at account opening."),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Account Status
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("3", "Account Status Management"))
story.append(body("An account can be in one of three statuses. Status governs whether transactions are permitted."))
story.append(Spacer(1, 4))
story.append(make_table(
    ["Status", "Code", "Description"],
    [
        ["Active", "A",
         "Account is in good standing. All permitted transactions can be processed."],
        ["Frozen", "F",
         "Account has been suspended. No deposits or withdrawals are allowed. "
         "Customer must visit a branch to unfreeze."],
        ["Closed", "C",
         "Account is permanently closed. No transactions of any kind are permitted."],
    ],
    [1.1*inch, 0.6*inch, PAGE_W - 1.7*inch]
))
story.append(Spacer(1, 6))
story += [
    rule_box("BR-005 — Frozen Account Restriction",
             "No transaction (deposit or withdrawal) may be processed on a Frozen account.",
             quote="ACCOUNT FROZEN - VISIT BRANCH TO UNFREEZE"),
    rule_box("BR-006 — Closed Account Restriction",
             "No transaction may be processed on a Closed account.",
             quote="ACCOUNT IS PERMANENTLY CLOSED"),
    rule_box("BR-007 — Status Check is First Priority",
             "Account status is always validated before any amount or limit checks. "
             "If an account is Frozen or Closed, the transaction is immediately rejected with no further validation."),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Account Tiers
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("4", "Account Tier Classification (Regular vs VIP)"))
story += [
    rule_box("BR-008 — VIP Qualification Threshold",
             "An account qualifies for VIP status when the account balance exceeds $50,000.00."),
    rule_box("BR-009 — Regular Account",
             "Any account with a balance of $50,000.00 or less is classified as Regular "
             "and is subject to Regular transaction limits."),
    rule_box("BR-010 — VIP Account",
             "Any account with a balance above $50,000.00 is classified as VIP "
             "and is subject to VIP transaction limits (significantly higher)."),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Deposit Processing
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("5", "Deposit Processing"))
story.append(body("Deposits are validated in the following sequence. The first failure immediately rejects the transaction."))
story.append(Spacer(1, 4))

story.append(sub_title("5.1  Deposit Validation Sequence"))
story += [
    body("<b>Step 1 — Account Status Check</b>"),
    bullet("If account is FROZEN → Reject (see BR-005)"),
    bullet("If account is CLOSED → Reject (see BR-006)"),
    Spacer(1, 4),
    body("<b>Step 2 — Minimum Amount Check</b>"),
    rule_box("BR-011 — Minimum Deposit Amount",
             "The minimum deposit amount is $1.00.",
             quote="AMOUNT BELOW MINIMUM DEPOSIT OF $1.00"),
    body("<b>Step 3 — Single Transaction Cap</b>"),
    rule_box("BR-012 — Regular Account: Single Deposit Limit",
             "A Regular account may not receive more than $50,000.00 in a single deposit.",
             quote="EXCEEDS REGULAR SINGLE DEPOSIT CAP $50,000"),
    rule_box("BR-013 — VIP Account: Single Deposit Limit",
             "A VIP account may not receive more than $250,000.00 in a single deposit.",
             quote="EXCEEDS VIP SINGLE DEPOSIT CAP $250,000.00"),
    body("<b>Step 4 — Daily Cumulative Cap</b>"),
    rule_box("BR-014 — Regular Account: Daily Deposit Limit",
             "The total of all deposits to a Regular account in a single business day may not exceed $100,000.00.",
             quote="DAILY DEPOSIT LIMIT REACHED $100,000.00"),
    rule_box("BR-015 — VIP Account: Daily Deposit Limit",
             "The total of all deposits to a VIP account in a single business day may not exceed $500,000.00.",
             quote="VIP DAILY DEPOSIT LIMIT REACHED $500,000"),
]

story.append(sub_title("5.2  Approved Deposit Processing"))
story.append(body("When a deposit passes all validations, the system:"))
for step in [
    "Adds the deposit amount to the account balance.",
    "Adds the deposit amount to the account's daily deposit accumulator.",
    "Increments the transaction counter for the account by 1.",
    "Records the last transaction date, type (Deposit), and amount on the account.",
    "Evaluates whether the new balance qualifies the account for VIP upgrade (see BR-016).",
]:
    story.append(bullet(step))
story.append(Spacer(1, 6))

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Withdrawal Processing
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("6", "Withdrawal Processing"))
story.append(body("Withdrawals are validated in the following sequence. The first failure immediately rejects the transaction."))
story.append(Spacer(1, 4))

story.append(sub_title("6.1  Withdrawal Validation Sequence"))
story += [
    body("<b>Step 1 — Account Status Check</b>"),
    bullet("If account is FROZEN → Reject (see BR-005)"),
    bullet("If account is CLOSED → Reject (see BR-006)"),
    Spacer(1, 4),
    body("<b>Step 2 — Minimum Amount Check</b>"),
    rule_box("BR-020 — Minimum Withdrawal Amount",
             "The minimum withdrawal amount is $1.00.",
             quote="AMOUNT BELOW MINIMUM WITHDRAWAL OF $1.00"),
    body("<b>Step 3 — Single Transaction Cap</b>"),
    rule_box("BR-021 — Regular Account: Single Withdrawal Limit",
             "A Regular account may not withdraw more than $10,000.00 in a single transaction.",
             quote="EXCEEDS REGULAR SINGLE WITHDRAWAL CAP $10K"),
    rule_box("BR-022 — VIP Account: Single Withdrawal Limit",
             "A VIP account may not withdraw more than $50,000.00 in a single transaction.",
             quote="EXCEEDS VIP SINGLE WITHDRAWAL CAP $50,000"),
    body("<b>Step 4 — Daily Cumulative Cap</b>"),
    rule_box("BR-023 — Regular Account: Daily Withdrawal Limit",
             "The total of all withdrawals from a Regular account in a single business day may not exceed $20,000.00.",
             quote="DAILY WITHDRAWAL LIMIT REACHED $20,000.00"),
    rule_box("BR-024 — VIP Account: Daily Withdrawal Limit",
             "The total of all withdrawals from a VIP account in a single business day may not exceed $100,000.00.",
             quote="VIP DAILY WITHDRAWAL LIMIT REACHED $100,000"),
    body("<b>Step 5 — Balance Adequacy Checks</b>"),
    rule_box("BR-025 — Minimum Required Balance",
             "After a withdrawal, the account balance must not fall below $100.00.",
             quote="WOULD BREACH MINIMUM REQUIRED BALANCE $100.00"),
    rule_box("BR-026 — No Overdraft",
             "The system does not permit overdrafts. A negative post-withdrawal balance is not allowed.",
             quote="INSUFFICIENT FUNDS - OVERDRAFT NOT PERMITTED",
             note="BR-025 is checked first. BR-026 is only reached if the minimum balance were $0.00."),
]

story.append(sub_title("6.2  Approved Withdrawal Processing"))
story.append(body("When a withdrawal passes all validations, the system:"))
for step in [
    "Deducts the withdrawal amount from the account balance.",
    "Adds the withdrawal amount to the account's daily withdrawal accumulator.",
    "Increments the transaction counter for the account by 1.",
    "Records the last transaction date, type (Withdrawal), and amount on the account.",
    "Evaluates whether the new balance requires VIP → Regular downgrade (see BR-017).",
]:
    story.append(bullet(step))
story.append(Spacer(1, 6))

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Limits Reference Table
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("7", "Transaction Limits Reference Table"))
story.append(make_table(
    ["Limit", "Regular Account", "VIP Account"],
    [
        ["Minimum transaction amount",       "$1.00",        "$1.00"],
        ["Maximum single deposit",           "$50,000.00",   "$250,000.00"],
        ["Maximum single withdrawal",        "$10,000.00",   "$50,000.00"],
        ["Maximum daily deposits (total)",   "$100,000.00",  "$500,000.00"],
        ["Maximum daily withdrawals (total)","$20,000.00",   "$100,000.00"],
        ["Minimum required balance",         "$100.00",      "$100.00"],
        ["Overdraft permitted",              "No",           "No"],
    ],
    [2.5*inch, 1.8*inch, 1.8*inch]
))
story.append(Spacer(1, 10))

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Tier Promotion / Demotion
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("8", "Account Tier Promotion & Demotion"))
story += [
    rule_box("BR-016 — Automatic VIP Upgrade After Deposit",
             "After a deposit is applied, if the new balance exceeds $50,000.00 and the account is "
             "currently Regular, the account is automatically upgraded to VIP. New VIP limits apply immediately."),
    rule_box("BR-017 — Automatic VIP Downgrade After Withdrawal",
             "After a withdrawal is applied, if the new balance is $50,000.00 or less and the account is "
             "currently VIP, the account is automatically downgraded to Regular. "
             "The operator is notified: \"NOTE: ACCOUNT DOWNGRADED VIP -> REGULAR\"."),
    rule_box("BR-018 — Tier Applies at Time of Transaction",
             "The account type at the moment of transaction submission determines which limits apply. "
             "A mid-day upgrade or downgrade takes effect immediately for all subsequent transactions."),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — Transaction Logging
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("9", "Transaction Logging & Audit Trail"))
story += [
    rule_box("BR-030 — All Transactions Are Logged",
             "Every transaction attempt — whether approved or rejected — is recorded in the transaction log. "
             "A rejected transaction is not applied to the balance but is still written to the log."),
]
story.append(body("<b>BR-031 — Transaction Log Contents.</b> Each log entry captures:"))
for f in [
    "Transaction ID (sequential, system-generated)",
    "Transaction Date and Time",
    "Client ID",
    "Transaction Type (Deposit or Withdrawal)",
    "Amount",
    "Account Balance after the transaction (approved transactions)",
    "Result: Approved (OK) or Rejected (RJ)",
    "Rejection Reason (if rejected)",
]:
    story.append(bullet(f))
story.append(Spacer(1, 4))
story += [
    rule_box("BR-032 — Circular Log Buffer",
             "The transaction log holds a maximum of 5,000 entries. When full, new entries overwrite "
             "the oldest entries (circular buffer). The total count is retained across the session."),
    rule_box("BR-033 — Transaction IDs are Sequential",
             "Each log entry is assigned a unique, sequentially incrementing Transaction ID starting at 1. "
             "IDs are never reused within a session."),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — End-of-Day
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("10", "End-of-Day Processing"))
story += [
    rule_box("BR-040 — Daily Limit Reset",
             "At the end of each business day, an authorized operator must manually trigger the end-of-day reset. "
             "This clears daily withdrawal and deposit accumulators to $0.00 for every account and marks the "
             "beginning of a new business day."),
    rule_box("BR-041 — Confirmation Required",
             "The end-of-day reset requires explicit operator confirmation (Y/N prompt) before executing. "
             "If the operator does not confirm, the reset is cancelled and no data is changed."),
    rule_box("BR-042 — Reset Applies to All Accounts",
             "The daily reset applies simultaneously to all accounts regardless of status or type. "
             "Frozen and Closed accounts also have their daily accumulators cleared."),
    rule_box("BR-043 — Daily Limits are Per Business Day",
             "Transaction limits are calculated from the start of the current business day. "
             "After an end-of-day reset, every account starts the new day with $0.00 accumulated toward daily limits."),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — Reporting
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("11", "Inquiries & Reporting"))

story.append(sub_title("11.1  Balance Inquiry (BR-050)"))
story.append(body("Any account (including Frozen and Closed) may be queried for its current balance. Displays:"))
for f in ["Current balance", "Total amount withdrawn today",
          "Total amount deposited today", "Lifetime transaction count"]:
    story.append(bullet(f))
story.append(Spacer(1, 4))

story.append(sub_title("11.2  Account Detail (BR-051)"))
story.append(body(
    "A full account record view displays all account fields, plus the applicable transaction limits "
    "based on current account type (Regular or VIP), and the minimum required balance."))
story.append(Spacer(1, 4))

story.append(sub_title("11.3  Client List (BR-052)"))
story.append(body(
    "The client list is displayed 20 records at a time. The operator selects a starting record number "
    "(1 to 1000). Shows Client ID, name, balance, status, and account type for each account."))
story.append(Spacer(1, 4))

story.append(sub_title("11.4  Daily Summary Report (BR-053)"))
story.append(body("The daily summary provides an aggregate view for the current business day:"))
for f in ["Total deposits across all accounts today",
          "Total withdrawals across all accounts today",
          "Total number of transactions logged in the session",
          "Count of accounts by status: Active, Frozen, Closed"]:
    story.append(bullet(f))
story.append(Spacer(1, 4))

story.append(sub_title("11.5  Transaction Log View (BR-054)"))
story.append(body(
    "The operator can view the most recent 20 transactions. "
    "Entries show: Transaction ID, date, Client ID, transaction type, amount, and result (OK/RJ)."))
story.append(Spacer(1, 8))

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 12 — Capacity
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("12", "System Capacity & Constraints"))
story.append(make_table(
    ["Parameter", "Value"],
    [
        ["Maximum accounts in database",         "1,000"],
        ["Maximum transaction log entries",       "5,000 (circular — oldest overwritten)"],
        ["First assigned Client ID",              "100001"],
        ["Supported transaction types",           "Deposit and Withdrawal only"],
        ["Overdraft facility",                    "Not supported"],
        ["Inter-account transfers",               "Not supported"],
        ["Interest calculation",                  "Not supported"],
        ["Account creation via system",           "Not supported (pre-loaded database)"],
        ["Account closure via system",            "Not supported (status is pre-set)"],
    ],
    [2.8*inch, PAGE_W - 2.8*inch]
))
story.append(Spacer(1, 10))

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 13 — Migration Notes
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("13", "Migration Notes for Business Analysts"))
story.append(body(
    "The following values are hardcoded in the COBOL source and must be externalized as configurable "
    "parameters in the new system:"))
story.append(Spacer(1, 6))
story.append(make_table(
    ["Rule Ref", "Parameter", "Current Value", "COBOL Variable"],
    [
        ["BR-025", "Minimum required balance",          "$100.00",      "BR-MIN-BALANCE"],
        ["BR-021", "Regular max single withdrawal",     "$10,000.00",   "BR-MAX-WD-SINGLE"],
        ["BR-012", "Regular max single deposit",        "$50,000.00",   "BR-MAX-DEP-SINGLE"],
        ["BR-023", "Regular max daily withdrawal",      "$20,000.00",   "BR-MAX-WD-DAILY"],
        ["BR-014", "Regular max daily deposit",         "$100,000.00",  "BR-MAX-DEP-DAILY"],
        ["BR-011/020", "Minimum transaction amount",    "$1.00",        "BR-MIN-TX-AMOUNT"],
        ["BR-002", "Initial account balance",           "$500.00",      "BR-INITIAL-BALANCE"],
        ["BR-008", "VIP qualification threshold",       "$50,000.00",   "BR-VIP-THRESHOLD"],
        ["BR-022", "VIP max single withdrawal",         "$50,000.00",   "BR-VIP-MAX-WD-SINGLE"],
        ["BR-013", "VIP max single deposit",            "$250,000.00",  "BR-VIP-MAX-DEP-SINGLE"],
        ["BR-024", "VIP max daily withdrawal",          "$100,000.00",  "BR-VIP-MAX-WD-DAILY"],
        ["BR-015", "VIP max daily deposit",             "$500,000.00",  "BR-VIP-MAX-DEP-DAILY"],
    ],
    [0.75*inch, 2.1*inch, 1.2*inch, PAGE_W - 4.05*inch]
))
story.append(Spacer(1, 10))

story.append(sub_title("Key Design Decisions to Resolve During Migration"))
decisions = [
    ("<b>VIP threshold logic is balance-based only.</b>  There is no minimum tenure, credit score, or "
     "manual approval pathway — VIP status is granted and revoked automatically based solely on the "
     "balance crossing $50,000."),
    ("<b>End-of-day reset is manual.</b>  The current system requires a human operator to trigger the "
     "daily limit reset. The new system must decide whether this is automated (scheduled batch job) "
     "or remains operator-initiated."),
    ("<b>Rejected transactions are fully logged.</b>  The audit trail includes both approved and rejected "
     "attempts. This behaviour must be preserved in the new system."),
    ("<b>No overdraft product exists.</b>  The current system has no concept of an authorized overdraft. "
     "If the new system introduces overdraft, new business rules will be required."),
    ("<b>Frozen vs. Closed distinction.</b>  Frozen is a temporary, reversible state that requires a branch "
     "visit to lift. Closed is permanent. The new system must preserve this distinction and implement "
     "the branch-visit workflow for unfreezing accounts."),
]
for i, d in enumerate(decisions, 1):
    story.append(Paragraph(f"{i}.  {d}", styles["body"]))
    story.append(Spacer(1, 4))

# ── Build PDF ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    "/home/user/Test12/BUSINESS_RULES.pdf",
    pagesize=letter,
    topMargin=0.7*inch,
    bottomMargin=0.65*inch,
    leftMargin=0.5*inch,
    rightMargin=0.5*inch,
    title="Bank of COBOL — Business Rules",
    author="Core Banking Migration Team",
)
doc.build(story, onFirstPage=page_header_footer, onLaterPages=page_header_footer)
print("PDF created: BUSINESS_RULES.pdf")
