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
import math
from reportlab.graphics.shapes import Drawing, Rect, String as GString, Line

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

def make_erd(page_w):
    """Build an entity-relationship diagram as a reportlab Drawing."""
    DW, DH = page_w, 265
    drw = Drawing(DW, DH)

    BW, BH, HDR_H = 148, 145, 22
    LINE_H = 14

    C_DARK  = colors.HexColor("#1a3a5c")
    C_MID   = colors.HexColor("#2e6da4")
    C_LIGHT = colors.HexColor("#dce9f5")
    C_AMBER = colors.HexColor("#fff8e1")
    C_GREEN = colors.HexColor("#e8f5e9")
    C_DKGRN = colors.HexColor("#2e7d32")
    C_GREY  = colors.HexColor("#888888")
    C_LGREY = colors.HexColor("#f5f5f5")

    def draw_box(x, y, title, lines, pk_idx=(), fk_idx=()):
        drw.add(Rect(x, y + BH - HDR_H, BW, HDR_H,
                     fillColor=C_DARK, strokeColor=C_DARK, strokeWidth=0))
        drw.add(GString(x + BW/2, y + BH - HDR_H + 6, title,
                        fontSize=7.5, fontName="Helvetica-Bold",
                        fillColor=colors.white, textAnchor="middle"))
        drw.add(Rect(x, y, BW, BH - HDR_H,
                     fillColor=C_LIGHT, strokeColor=C_DARK, strokeWidth=0.8))
        for i, txt in enumerate(lines):
            ry = y + BH - HDR_H - 17 - i * LINE_H
            hl = C_AMBER if i in pk_idx else C_GREEN if i in fk_idx else None
            if hl:
                drw.add(Rect(x + 1, ry - 3, BW - 2, 13,
                             fillColor=hl, strokeColor=None, strokeWidth=0))
            drw.add(GString(x + 7, ry, txt, fontSize=7,
                            fontName="Helvetica", fillColor=colors.black,
                            textAnchor="start"))

    def draw_arrow(x1, y1, x2, y2, label=""):
        drw.add(Line(x1, y1, x2, y2, strokeColor=C_MID, strokeWidth=1.2))
        ang = math.atan2(y2 - y1, x2 - x1)
        for da in (0.45, -0.45):
            drw.add(Line(x2, y2,
                         x2 - 9*math.cos(ang + da),
                         y2 - 9*math.sin(ang + da),
                         strokeColor=C_MID, strokeWidth=1.2))
        if label:
            drw.add(GString((x1+x2)/2, (y1+y2)/2 + 7, label,
                            fontSize=6.5, fontName="Helvetica-Oblique",
                            fillColor=C_GREY, textAnchor="middle"))

    # ── Three runtime boxes ────────────────────────────────────────────────
    y0 = 105
    r_x, c_x, t_x = 5, 200, 392

    draw_box(r_x, y0, "WS-RULES  (Config — singleton)",
             ["BR-MIN-BALANCE   = $100.00",
              "BR-VIP-THRESHOLD = $50,000",
              "BR-MIN-TX-AMOUNT = $1.00",
              "BR-MAX-WD-SINGLE = $10,000",
              "BR-MAX-DEP-SINGLE= $50,000",
              "BR-MAX-WD-DAILY  = $20,000",
              "BR-MAX-DEP-DAILY = $100,000",
              "... (15 parameters total)"])

    draw_box(c_x, y0, "WS-CLIENT-DB  (≤1,000 rows)",
             ["PK  DB-CLIENT-ID  (6-digit)",
              "    DB-LAST-NAME / FIRST-NAME",
              "    DB-BALANCE",
              "    DB-STATUS  (A / F / C)",
              "    DB-ACCT-TYPE  (R / V)",
              "    DB-DAILY-WD / DAILY-DEP",
              "    DB-TX-COUNT / OPEN-DATE",
              "    ... (13 fields total)"],
             pk_idx=(0,))

    draw_box(t_x, y0, "WS-TX-LOG  (≤5,000 rows)",
             ["PK  TX-ID  (sequential)",
              "FK  TX-CLIENT-ID",
              "    TX-DATE / TX-TIME",
              "    TX-TYPE  (D / W)",
              "    TX-AMOUNT",
              "    TX-BAL-AFTER",
              "    TX-RESULT  (OK / RJ)",
              "    TX-REJECT-REASON"],
             pk_idx=(0,), fk_idx=(1,))

    # ── Relationship arrows ────────────────────────────────────────────────
    mid_y = y0 + BH / 2
    draw_arrow(r_x + BW, mid_y, c_x, mid_y, "governs transaction limits")
    draw_arrow(c_x + BW, mid_y, t_x, mid_y)
    drw.add(GString(c_x + BW + 5, mid_y + 5, "1",
                    fontSize=9, fontName="Helvetica-Bold",
                    fillColor=C_DARK, textAnchor="start"))
    drw.add(GString(t_x - 13, mid_y + 5, "M",
                    fontSize=9, fontName="Helvetica-Bold",
                    fillColor=C_DARK, textAnchor="start"))
    drw.add(GString((c_x + BW + t_x) / 2, mid_y - 10,
                    "TX-CLIENT-ID  →  DB-CLIENT-ID",
                    fontSize=6.5, fontName="Helvetica-Oblique",
                    fillColor=C_GREY, textAnchor="middle"))

    # ── Init-only section (bottom strip) ──────────────────────────────────
    IW, IH = 130, 62
    i_y = 8
    drw.add(Rect(5, i_y - 4, DW - 10, IH + 14,
                 fillColor=C_LGREY,
                 strokeColor=colors.HexColor("#cccccc"), strokeWidth=0.5))
    drw.add(GString(DW / 2, i_y + IH + 4,
                    "INITIALIZATION ONLY — seeded once at startup, not modified at runtime",
                    fontSize=7, fontName="Helvetica-Bold",
                    fillColor=colors.HexColor("#555555"), textAnchor="middle"))

    for ix, name, l1, l2, tgt_x in [
        (10,  "WS-LNAME-TABLE", "LT-VALUE × 20", "Surnames for DB seeding",      c_x + 35),
        (165, "WS-FNAME-TABLE", "FT-VALUE × 20", "First names for DB seeding",   c_x + 85),
    ]:
        drw.add(Rect(ix, i_y, IW, IH,
                     fillColor=C_GREEN, strokeColor=C_DKGRN, strokeWidth=0.8))
        drw.add(Rect(ix, i_y + IH - 18, IW, 18,
                     fillColor=C_DKGRN, strokeColor=C_DKGRN, strokeWidth=0))
        drw.add(GString(ix + IW/2, i_y + IH - 10, name,
                        fontSize=7, fontName="Helvetica-Bold",
                        fillColor=colors.white, textAnchor="middle"))
        drw.add(GString(ix + 8, i_y + 28, l1, fontSize=7,
                        fontName="Helvetica", fillColor=colors.black))
        drw.add(GString(ix + 8, i_y + 14, l2, fontSize=7,
                        fontName="Helvetica", fillColor=colors.black))
        draw_arrow(ix + IW, i_y + IH/2, tgt_x, y0, "seeds at init")

    # ── Legend ─────────────────────────────────────────────────────────────
    lx, ly = 315, i_y + 2
    drw.add(Rect(lx, ly, 218, 68,
                 fillColor=C_LGREY,
                 strokeColor=colors.HexColor("#cccccc"), strokeWidth=0.5))
    drw.add(GString(lx + 109, ly + 57, "LEGEND",
                    fontSize=7.5, fontName="Helvetica-Bold",
                    fillColor=colors.black, textAnchor="middle"))
    for j, (fc, sc, lbl) in enumerate([
        (C_AMBER, C_DARK,  "Row highlighted amber   =  Primary Key (PK)"),
        (C_GREEN, C_DKGRN, "Row highlighted green   =  Foreign Key (FK)"),
        (C_LIGHT, C_DARK,  "Blue header box          =  Runtime table"),
        (C_GREEN, C_DKGRN, "Green header box        =  Init-only table"),
    ]):
        jy = ly + 44 - j * 14
        drw.add(Rect(lx + 8, jy, 12, 10,
                     fillColor=fc, strokeColor=sc, strokeWidth=0.5))
        drw.add(GString(lx + 26, jy + 1, lbl, fontSize=6.5,
                        fontName="Helvetica", fillColor=colors.black,
                        textAnchor="start"))
    return drw

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
    "14. Data Structures, Fields & Entity Relationships",
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

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 14 — Data Structures, Fields & Entity Relationships
# ═══════════════════════════════════════════════════════════════════════════════
story.append(section_title("14", "Data Structures, Fields & Entity Relationships"))
story.append(body(
    "The system holds three runtime in-memory databases and two initialization-only reference tables. "
    "The diagram below shows the structure and relationships; detailed field definitions follow."))
story.append(Spacer(1, 8))

story.append(make_erd(PAGE_W))
story.append(Spacer(1, 14))

# ── 14.1  WS-RULES ────────────────────────────────────────────────────────────
story.append(sub_title("14.1  WS-RULES — Business Rules Configuration"))
story.append(body(
    "A single, read-only record loaded at startup. Contains every hardcoded threshold and limit "
    "applied during transaction processing. There is no key — the record is a singleton."))
story.append(Spacer(1, 4))
story.append(make_table(
    ["COBOL Field", "Value", "Data Type", "Description"],
    [
        ["BR-MIN-BALANCE",        "$100.00",      "Numeric 8.2",  "Minimum balance an account must retain after any withdrawal"],
        ["BR-MAX-WD-SINGLE",      "$10,000.00",   "Numeric 8.2",  "Maximum amount a Regular account may withdraw in one transaction"],
        ["BR-MAX-DEP-SINGLE",     "$50,000.00",   "Numeric 8.2",  "Maximum amount a Regular account may deposit in one transaction"],
        ["BR-MAX-WD-DAILY",       "$20,000.00",   "Numeric 8.2",  "Maximum total withdrawals a Regular account may make in one business day"],
        ["BR-MAX-DEP-DAILY",      "$100,000.00",  "Numeric 8.2",  "Maximum total deposits a Regular account may receive in one business day"],
        ["BR-MIN-TX-AMOUNT",      "$1.00",        "Numeric 8.2",  "Minimum dollar amount accepted for any transaction (deposit or withdrawal)"],
        ["BR-INITIAL-BALANCE",    "$500.00",      "Numeric 8.2",  "Opening balance assigned to every new account"],
        ["BR-VIP-THRESHOLD",      "$50,000.00",   "Numeric 8.2",  "Balance threshold above which an account is classified as VIP"],
        ["BR-VIP-MAX-WD-SINGLE",  "$50,000.00",   "Numeric 8.2",  "Maximum amount a VIP account may withdraw in one transaction"],
        ["BR-VIP-MAX-DEP-SINGLE", "$250,000.00",  "Numeric 8.2",  "Maximum amount a VIP account may deposit in one transaction"],
        ["BR-VIP-MAX-WD-DAILY",   "$100,000.00",  "Numeric 8.2",  "Maximum total withdrawals a VIP account may make in one business day"],
        ["BR-VIP-MAX-DEP-DAILY",  "$500,000.00",  "Numeric 8.2",  "Maximum total deposits a VIP account may receive in one business day"],
        ["BR-MAX-CLIENTS",        "1,000",        "Numeric 4",    "Maximum number of client accounts the database can hold"],
        ["BR-MAX-TX-LOG",         "5,000",        "Numeric 5",    "Capacity of the transaction log circular buffer"],
        ["BR-FIRST-CLIENT-ID",    "100001",       "Numeric 6",    "Starting value for auto-assigned Client IDs"],
    ],
    [1.7*inch, 0.85*inch, 0.85*inch, PAGE_W - 3.4*inch]
))
story.append(Spacer(1, 12))

# ── 14.2  WS-CLIENT-DB ────────────────────────────────────────────────────────
story.append(sub_title("14.2  WS-CLIENT-DB — Client Account Database"))
story.append(body(
    "The primary account store. Holds up to 1,000 records, one per client. "
    "DB-CLIENT-ID is the primary key and the join field to WS-TX-LOG."))
story.append(Spacer(1, 4))
story.append(make_table(
    ["COBOL Field", "Key", "Data Type", "Valid Values / Format", "Description"],
    [
        ["DB-CLIENT-ID",    "PK", "Numeric 6",       "100001 – 101000",        "Unique client identifier assigned sequentially at account opening"],
        ["DB-LAST-NAME",    "",   "Alpha 15",         "Free text",              "Client surname (up to 15 characters)"],
        ["DB-FIRST-NAME",   "",   "Alpha 10",         "Free text",              "Client given name (up to 10 characters)"],
        ["DB-BALANCE",      "",   "Signed Num 10.2",  "Any value ≥ BR-MIN-BALANCE", "Current account balance in dollars"],
        ["DB-STATUS",       "",   "Alpha 1",          "A = Active\nF = Frozen\nC = Closed", "Current account status — controls whether transactions are permitted"],
        ["DB-ACCT-TYPE",    "",   "Alpha 1",          "R = Regular\nV = VIP",   "Account tier — determines which transaction limits apply"],
        ["DB-DAILY-WD",     "",   "Numeric 10.2",     "0.00 – 999,999.99",      "Running total of withdrawals processed today; resets to 0 at end of day"],
        ["DB-DAILY-DEP",    "",   "Numeric 10.2",     "0.00 – 999,999.99",      "Running total of deposits received today; resets to 0 at end of day"],
        ["DB-OPEN-DATE",    "",   "Alpha 10",         "YYYY-MM-DD",             "Date the account was opened"],
        ["DB-TX-COUNT",     "",   "Numeric 6",        "0 – 999999",             "Lifetime count of all transaction attempts (approved and rejected)"],
        ["DB-LAST-TX-DATE", "",   "Alpha 10",         "YYYY-MM-DD",             "Date of the most recent transaction attempt on this account"],
        ["DB-LAST-TX-TYPE", "",   "Alpha 1",          "D = Deposit\nW = Withdrawal", "Type of the most recent transaction"],
        ["DB-LAST-TX-AMT",  "",   "Numeric 10.2",     "0.00 – 999,999.99",      "Dollar amount of the most recent transaction"],
    ],
    [1.55*inch, 0.3*inch, 0.95*inch, 1.35*inch, PAGE_W - 4.15*inch]
))
story.append(Spacer(1, 12))

# ── 14.3  WS-TX-LOG ────────────────────────────────────────────────────────────
story.append(sub_title("14.3  WS-TX-LOG — Transaction Log"))
story.append(body(
    "An audit log of every transaction attempt (approved and rejected). Implemented as a circular "
    "buffer of 5,000 entries — once full, the oldest entry is overwritten. "
    "TX-CLIENT-ID is a foreign key to WS-CLIENT-DB.DB-CLIENT-ID (many transactions per client)."))
story.append(Spacer(1, 4))
story.append(make_table(
    ["COBOL Field", "Key", "Data Type", "Valid Values / Format", "Description"],
    [
        ["TX-ID",            "PK", "Numeric 8",       "1, 2, 3 … (never reset)", "Sequential transaction identifier assigned at log time; never reused in a session"],
        ["TX-DATE",          "",   "Alpha 10",         "YYYY-MM-DD",              "Date the transaction was processed"],
        ["TX-TIME",          "",   "Alpha 8",          "HH:MM:SS",                "Time the transaction was processed"],
        ["TX-CLIENT-ID",     "FK", "Numeric 6",        "100001 – 101000",         "Client account involved; joins to DB-CLIENT-ID in WS-CLIENT-DB"],
        ["TX-TYPE",          "",   "Alpha 1",          "D = Deposit\nW = Withdrawal", "Type of transaction attempted"],
        ["TX-AMOUNT",        "",   "Numeric 10.2",     "0.00 – 999,999.99",       "Dollar amount of the transaction attempt"],
        ["TX-BAL-AFTER",     "",   "Signed Num 10.2",  "Any value",               "Account balance immediately after the transaction (populated for approved transactions)"],
        ["TX-RESULT",        "",   "Alpha 2",          "OK = Approved\nRJ = Rejected", "Whether the transaction was approved or rejected by the validation rules"],
        ["TX-REJECT-REASON", "",   "Alpha 30",         "Free text or spaces",     "Plain-text explanation of why the transaction was rejected; blank if approved"],
    ],
    [1.55*inch, 0.3*inch, 0.95*inch, 1.35*inch, PAGE_W - 4.15*inch]
))
story.append(Spacer(1, 12))

# ── 14.4  Init reference tables ───────────────────────────────────────────────
story.append(sub_title("14.4  WS-LNAME-TABLE & WS-FNAME-TABLE — Initialization Seed Data"))
story.append(body(
    "Two small lookup tables used only during system startup to populate the client database with "
    "sample names. They are not referenced during normal transaction processing and have no "
    "primary key or relationships at runtime."))
story.append(Spacer(1, 4))
story.append(make_table(
    ["Table", "COBOL Field", "Data Type", "Entries", "Purpose"],
    [
        ["WS-LNAME-TABLE", "LT-VALUE", "Alpha 15", "20",
         "Pool of surnames cycled across 1,000 client records at initialization"],
        ["WS-FNAME-TABLE", "FT-VALUE", "Alpha 10", "20",
         "Pool of first names cycled across 1,000 client records at initialization"],
    ],
    [1.5*inch, 1.0*inch, 0.8*inch, 0.6*inch, PAGE_W - 3.9*inch]
))
story.append(Spacer(1, 12))

# ── 14.5  Relationship summary ─────────────────────────────────────────────────
story.append(sub_title("14.5  Entity Relationship Summary"))
story.append(make_table(
    ["From Table", "Relationship", "To Table", "Join Condition", "Cardinality"],
    [
        ["WS-RULES",        "governs",           "WS-CLIENT-DB", "No join field — rules apply globally to all accounts",   "1 rule set → N accounts"],
        ["WS-RULES",        "governs",           "WS-TX-LOG",    "No join field — rules govern every transaction attempt",  "1 rule set → N log entries"],
        ["WS-CLIENT-DB",    "referenced by",     "WS-TX-LOG",    "WS-TX-LOG.TX-CLIENT-ID = WS-CLIENT-DB.DB-CLIENT-ID",     "1 account → M log entries"],
        ["WS-LNAME-TABLE",  "seeds (init only)", "WS-CLIENT-DB", "MOD(record#, 20) selects surname index",                 "20 names → 1,000 accounts"],
        ["WS-FNAME-TABLE",  "seeds (init only)", "WS-CLIENT-DB", "MOD(record#+6, 20) selects first name index",            "20 names → 1,000 accounts"],
    ],
    [1.2*inch, 1.0*inch, 1.1*inch, 2.4*inch, PAGE_W - 5.7*inch]
))
story.append(Spacer(1, 10))

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
