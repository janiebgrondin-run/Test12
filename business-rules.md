# Missive — Hard-Coded Business Rules
**Document type:** Business Analyst Reference  
**Source:** `missiveapp-french.html` (repository source of truth)  
**Date:** 2026-06-02

---

## How to Read This Document

Each rule is stated in plain business language, followed by:
- **Where it lives in the product** — the value-chain stage or workflow step it governs
- **Current hard-coded value** — the exact threshold, limit, or condition embedded in the system today
- **Change impact** — what must be updated if the rule changes

---

## 1. SUBSCRIPTION & PRICING RULES

### Rule P-01 — Free Plan: Maximum User Count
**Statement:** A team on the Free plan may have no more than **3 users**. Adding a 4th user requires upgrading to a paid plan.  
**Value-chain stage:** Onboarding → Account provisioning  
**Hard-coded value:** `3 users`  
**Trigger:** User tries to invite a new team member  
**Change impact:** Pricing page copy, backend seat-limit enforcement, upgrade prompts

---

### Rule P-02 — Free Plan: Shared Inbox Limit
**Statement:** A team on the Free plan may create exactly **1 shared inbox**. Any additional shared inbox requires a paid plan.  
**Value-chain stage:** Onboarding → Workspace setup  
**Hard-coded value:** `1 shared inbox`  
**Change impact:** Inbox-creation guard, pricing page

---

### Rule P-03 — Free Plan: Message History Retention
**Statement:** On the Free plan, users can only access conversations and messages from the **last 30 days**. Anything older is not retrievable without upgrading.  
**Value-chain stage:** Customer service operations → Search & retrieval  
**Hard-coded value:** `30 days`  
**Change impact:** Data retention policy, archive queries, storage cost model

---

### Rule P-04 — Productivity Plan: Per-Seat Pricing
**Statement:** The Productivity plan is billed at **€14 per user per month**. Every active user in the workspace counts as one billable seat.  
**Value-chain stage:** Revenue collection → Invoice generation  
**Hard-coded value:** `€14 / user / month`  
**Change impact:** Billing engine, pricing page, sales materials, contracts

---

### Rule P-05 — Productivity Plan: Free Trial Duration
**Statement:** New subscribers to the Productivity plan receive a **14-day free trial** before any charge is applied.  
**Value-chain stage:** Sales → Trial conversion  
**Hard-coded value:** `14 days`  
**Change impact:** Trial timer, payment-capture trigger, onboarding email sequence

---

### Rule P-06 — Productivity Plan: Unlimited Entitlements
**Statement:** The Productivity plan grants unlimited users, unlimited shared inboxes, and unlimited message history — removing all the caps imposed by the Free plan.  
**Value-chain stage:** Account provisioning → Feature access  
**Hard-coded value:** `Unlimited` (no cap enforced)  
**Change impact:** Seat-limit and inbox-limit guards must be toggled off for this tier

---

### Rule P-07 — Enterprise Plan: Custom Pricing
**Statement:** The Enterprise plan has no published price. Pricing is determined through a sales negotiation and documented in a custom contract.  
**Value-chain stage:** Sales → Contracting  
**Hard-coded value:** `Devis (Quote)` — no numeric value  
**Change impact:** Any introduction of a published Enterprise price requires a pricing-page update and sales-process revision

---

### Rule P-08 — No Credit Card Required for Free Plan
**Statement:** A user can start a Free account without providing payment information. No payment credential is collected at signup for the Free tier.  
**Value-chain stage:** Onboarding → Registration  
**Hard-coded value:** Payment field = not required on Free plan  
**Change impact:** Signup form, payment processor integration, fraud-risk model

---

### Rule P-09 — Setup Time Commitment (SLA-adjacent)
**Statement:** The product promises account configuration can be completed within **2 minutes**. This sets an internal benchmark for onboarding complexity.  
**Value-chain stage:** Onboarding → Time-to-value  
**Hard-coded value:** `2 minutes`  
**Change impact:** If new mandatory setup steps are added, this claim must be reviewed

---

## 2. CONVERSATION WORKFLOW RULES

### Rule W-01 — Conversation Status: Three-State Model
**Statement:** Every conversation must be in exactly one of three states at any time: **Open**, **Pending**, or **Resolved**. There is no other valid status.  
**Value-chain stage:** Customer service operations → Ticket lifecycle management  
**Hard-coded values:** `Open` | `Pending` | `Resolved`  
**Change impact:** Status filter UI, reporting dashboards, automation triggers that fire on status change, SLA calculations

---

### Rule W-02 — Priority Classification
**Statement:** Conversations can be flagged as **Urgent** (high priority). This classification exists as a distinct label and must be visually differentiated from non-urgent conversations.  
**Value-chain stage:** Customer service operations → Triage & routing  
**Hard-coded value:** `Urgent` label (single high-priority tier)  
**Change impact:** If a multi-level priority scale (Low / Medium / High / Critical) is needed, all triage logic and UI must be revised

---

### Rule W-03 — Assignment: One Owner Per Conversation
**Statement:** Each conversation is assigned to a single team member. The assignment model is one-to-one (one conversation → one assignee).  
**Value-chain stage:** Customer service operations → Work assignment  
**Hard-coded value:** Single-assignee model  
**Change impact:** If co-ownership or multi-assignee is introduced, assignment display, notification logic, and reporting all change

---

### Rule W-04 — Internal Comments Are Private by Default
**Statement:** Comments added inside a conversation thread are internal (visible to team members only) and are never included in outbound replies to the customer.  
**Value-chain stage:** Customer service operations → Internal collaboration  
**Hard-coded value:** Internal = invisible to external recipient  
**Change impact:** If any internal comment must ever be shared externally, a new message type and permission model are required

---

### Rule W-05 — Draft Approval Before Send
**Statement:** A collaborative draft can be held for peer review before sending. The system supports a "draft ready for review" state. Sending is not automatic — a human must confirm dispatch.  
**Value-chain stage:** Customer service operations → Quality assurance before response  
**Hard-coded value:** Human-approval step required before send  
**Change impact:** If automated sending of drafts is introduced, risk controls and audit trail requirements change materially

---

## 3. AUTOMATION RULES

### Rule A-01 — Automation Trigger: Subject-Line Keyword Matching
**Statement:** An automation rule fires when the subject line of an inbound email **contains** a specified keyword (e.g., "remboursement" / "refund"). The match is keyword-based, not semantic.  
**Value-chain stage:** Inbound email processing → Automated triage  
**Hard-coded logic:** `IF subject CONTAINS [keyword] THEN [action]`  
**Change impact:** If fuzzy matching, regex, or AI classification replaces keyword match, the rule engine must be updated

---

### Rule A-02 — Automation Action: Auto-Assign on Trigger
**Statement:** When an automation rule fires, the conversation is automatically assigned to a specified team member. The assignment target is a named person (not a queue or round-robin).  
**Value-chain stage:** Inbound email processing → Work assignment  
**Hard-coded logic:** Assign to a named individual  
**Change impact:** Introduction of team-queue or round-robin routing requires a new assignment-action type

---

### Rule A-03 — Automation Action: Auto-Label on Trigger
**Statement:** When an automation rule fires, the system automatically applies a specified label to the conversation (e.g., "Remboursement").  
**Value-chain stage:** Inbound email processing → Classification & tagging  
**Hard-coded logic:** Apply label = [label name]  
**Change impact:** Label taxonomy changes cascade to automation rule maintenance

---

### Rule A-04 — Automation Action: Auto-Set Priority on Trigger
**Statement:** When an automation rule fires, the conversation priority is automatically set to **High (Haute)**.  
**Value-chain stage:** Inbound email processing → Prioritization  
**Hard-coded value:** Priority = `High` (only value used in automation output today)  
**Change impact:** Multi-level priority scale would require updating automation action options

---

### Rule A-05 — Automation Action: Auto-Close
**Statement:** Automation rules can close (resolve) a conversation without any manual action by a team member.  
**Value-chain stage:** Customer service operations → Ticket closure  
**Hard-coded logic:** Auto-close on defined trigger  
**Change impact:** Must be reviewed against any SLA or compliance requirement that mandates human sign-off before closure

---

### Rule A-06 — No-Code Rule Builder
**Statement:** Automation rules are configured entirely through the UI (no custom code required). This constrains available logic to the conditions and actions exposed by the rule builder.  
**Value-chain stage:** Operations → Configuration & administration  
**Hard-coded constraint:** Rules limited to the IF/THEN conditions available in the UI  
**Change impact:** Complex logic (nested conditions, loops, external API calls) requires a code-based or webhook integration layer

---

## 4. TEAM STRUCTURE & ACCESS RULES

### Rule T-01 — Standard Team Categories
**Statement:** The system ships with three default team groupings: **Support**, **Sales**, and **Technical**. These are the out-of-the-box organizational units.  
**Value-chain stage:** Onboarding → Workspace setup  
**Hard-coded values:** `Support` | `Sales` | `Technical`  
**Change impact:** Teams are configurable by admins, but the default scaffold assumes this three-team model

---

### Rule T-02 — Label Taxonomy: Urgency and Customer Labels
**Statement:** The system pre-defines two default labels: **Urgent** (red) and **Client/Customer** (green). These are the baseline classification tags.  
**Value-chain stage:** Customer service operations → Triage & classification  
**Hard-coded values:** `Urgent` (red) | `Client` (green)  
**Change impact:** Additional labels can be added, but any downstream reporting built on these two defaults will be affected if they are renamed or removed

---

### Rule T-03 — Enterprise Plan: SSO / SAML Required
**Statement:** Single Sign-On (SSO) via SAML is an **Enterprise-only feature**. Free and Productivity plans do not have access to SSO.  
**Value-chain stage:** Security & access management → Authentication  
**Hard-coded value:** SSO = Enterprise tier only  
**Change impact:** Moving SSO to a lower tier requires billing-engine and feature-flag changes

---

### Rule T-04 — Enterprise Plan: SLA Contract
**Statement:** A formal Service Level Agreement (SLA) is only provided to Enterprise customers.  
**Value-chain stage:** Sales → Contract management  
**Hard-coded value:** SLA = Enterprise tier only  
**Change impact:** Offering SLA guarantees to Productivity customers requires operational readiness and legal review

---

## 5. DATA & COMPLIANCE RULES

### Rule D-01 — GDPR Compliance Declaration
**Statement:** The product declares conformity with GDPR (EU General Data Protection Regulation). This implies specific obligations: right to erasure, data portability, consent management, and breach notification timelines.  
**Value-chain stage:** Data management → Legal & compliance  
**Hard-coded value:** GDPR compliance = mandatory baseline  
**Change impact:** Any new data collection, processing, or sharing must be assessed against GDPR obligations before release

---

### Rule D-02 — Encryption at Rest and in Transit
**Statement:** All data is encrypted both while stored (at rest) and while transmitted over the network (in transit). This is a non-negotiable security baseline.  
**Value-chain stage:** Infrastructure → Data security  
**Hard-coded value:** Encryption = always on (no opt-out)  
**Change impact:** Any storage or transmission layer must implement encryption by default

---

### Rule D-03 — Granular Access Control
**Statement:** Administrators can control access permissions at a granular level (per user, per inbox, per team). This means access is not binary (all or nothing) but scoped.  
**Value-chain stage:** Security & access management → Authorization  
**Hard-coded value:** Granular (not role-only) permission model  
**Change impact:** Simplifying to coarse roles (Admin / Member only) would reduce flexibility for large teams

---

## 6. NOTIFICATION RULES

### Rule N-01 — Relevance-Based Notification Filtering
**Statement:** Users only receive notifications for conversations that are relevant to them (assigned to them, or where they are @mentioned). They do not receive notifications for all team activity.  
**Value-chain stage:** Customer service operations → Team communication  
**Hard-coded logic:** Notify user only if: assigned to them OR @mentioned  
**Change impact:** If broadcast notifications are introduced (e.g., "notify whole team on Urgent"), this logic must be explicitly expanded

---

## 7. INTEGRATION & CHANNEL RULES

### Rule I-01 — Supported Email Protocols
**Statement:** The system accepts email connections via **Gmail**, **Outlook**, and generic **IMAP**. Any email provider outside this set is not natively supported.  
**Value-chain stage:** Onboarding → Channel connection  
**Hard-coded values:** `Gmail` | `Outlook` | `IMAP`  
**Change impact:** Adding a new provider (e.g., Yahoo, custom SMTP-only) requires connector development

---

### Rule I-02 — Supported Messaging Channels
**Statement:** In addition to email, the system supports inbound and outbound communication via **WhatsApp**, **Twitter/X**, and **Twilio SMS**.  
**Value-chain stage:** Customer service operations → Multi-channel intake  
**Hard-coded values:** `WhatsApp` | `Twitter/X` | `Twilio SMS`  
**Change impact:** Adding or removing channels requires connector maintenance and channel-routing rule updates

---

### Rule I-03 — Webhook and REST API Availability
**Statement:** The system exposes a REST API and supports outbound webhooks, enabling integration with any third-party system not covered by native connectors.  
**Value-chain stage:** IT & operations → System integration  
**Hard-coded value:** API and webhooks = available (no plan restriction stated for this HTML source)  
**Change impact:** If API access becomes tier-restricted, documentation and integration partners must be notified

---

## Summary Table

| Rule ID | Category | Plain-Language Summary | Hard-Coded Value | Value-Chain Stage |
|---------|----------|------------------------|------------------|-------------------|
| P-01 | Pricing | Free plan user cap | 3 users | Onboarding |
| P-02 | Pricing | Free plan inbox cap | 1 shared inbox | Onboarding |
| P-03 | Pricing | Free plan history limit | 30 days | Operations / Search |
| P-04 | Pricing | Productivity plan price | €14/user/month | Revenue collection |
| P-05 | Pricing | Free trial length | 14 days | Sales / Conversion |
| P-06 | Pricing | Productivity plan caps | Unlimited | Account provisioning |
| P-07 | Pricing | Enterprise pricing model | Custom quote only | Sales / Contracting |
| P-08 | Pricing | No CC required on Free | Payment = not required | Onboarding |
| P-09 | Pricing | Onboarding time promise | 2 minutes | Onboarding / UX |
| W-01 | Workflow | Conversation statuses | Open / Pending / Resolved | Ticket lifecycle |
| W-02 | Workflow | Priority flag | Urgent (single tier) | Triage |
| W-03 | Workflow | Assignment model | One owner per conversation | Work assignment |
| W-04 | Workflow | Internal comment privacy | Always private | Collaboration |
| W-05 | Workflow | Draft approval gate | Human must approve | QA before send |
| A-01 | Automation | Trigger condition | Subject CONTAINS keyword | Email triage |
| A-02 | Automation | Auto-assign action | Named individual | Work assignment |
| A-03 | Automation | Auto-label action | Named label | Classification |
| A-04 | Automation | Auto-priority action | High only | Prioritization |
| A-05 | Automation | Auto-close action | No human required | Ticket closure |
| A-06 | Automation | Rule builder constraint | No-code UI only | Configuration |
| T-01 | Teams | Default team structure | Support / Sales / Technical | Setup |
| T-02 | Teams | Default labels | Urgent (red) / Client (green) | Classification |
| T-03 | Access | SSO availability | Enterprise only | Authentication |
| T-04 | Access | SLA availability | Enterprise only | Contracting |
| D-01 | Compliance | GDPR conformity | Mandatory baseline | Legal / Data |
| D-02 | Compliance | Encryption | Always on, no opt-out | Security |
| D-03 | Compliance | Access control granularity | Per-user / per-inbox | Authorization |
| N-01 | Notifications | Notification scope | Assigned or @mentioned only | Team comms |
| I-01 | Integrations | Supported email protocols | Gmail / Outlook / IMAP | Channel setup |
| I-02 | Integrations | Supported messaging channels | WhatsApp / Twitter-X / SMS | Multi-channel |
| I-03 | Integrations | API access | REST API + Webhooks | IT integration |

---

*This document was generated from hard-coded values and logic found in `missiveapp-french.html`. Any rule change requires updating both the code/configuration AND this register.*
