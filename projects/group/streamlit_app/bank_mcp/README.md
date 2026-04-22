# Bank Transfer Review MCP

Local prototype MCP server for **BANK TRANSFER REVIEW**. It uses the
official MCP Python SDK plus a local SQLite database to support:

- beneficiary name/account checking during a bank transfer review
- prior scam/risk lookup for a beneficiary account
- reporting beneficiary accounts as suspicious or fraudulent

This implementation is intentionally lean, local, and demo-friendly.
There is no external database, cloud service, or network dependency
other than the MCP transport itself.

## Location

- Server package: `streamlit_app/bank_mcp`
- SQLite database: `data/bank_transfer_review.db`

## Tools

### `check_beneficiary_for_bank_transfer`

Checks whether the entered beneficiary name matches the registered name
for the account number, and whether the beneficiary has prior active
scam/risk reports relevant to a **bank transfer review**.

Inputs:

- `recipient_name: string`
- `account_number: string`

Output:

```json
{
  "name_account_check": "match",
  "reported_risk_status": "reported"
}
```

### `report_beneficiary_risk_for_bank_transfer`

Records a suspicious beneficiary account for **bank transfer scam/risk
review**.

Inputs:

- `account_number: string`
- `reason_code: "suspected_scam" | "confirmed_fraud" | "customer_dispute" | "manual_review"`
- `recipient_name: string | null`
- `case_id: string | null`

Output:

```json
{
  "status": "accepted",
  "report_id": "4"
}
```

## Setup

From `streamlit_app/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

The project dependency list in `pyproject.toml` includes the MCP Python
SDK. On first run, the server automatically creates the SQLite database,
schema, indexes, and seed data.

## Run

### Stdio transport

```bash
python -m bank_mcp.server
```

### Streamable HTTP transport

```bash
python -m bank_mcp.server --transport streamable-http
```

## Seed data

The local SQLite seed includes:

- `123-456-789-001` → `APEX SOLUTIONS LIMITED`
  - aliases: `APEX SOLUTIONS LTD`, `APEX SOLUTIONS`
  - active reports: none
- `987-654-321-002` → `CHAN TAI MAN COMPANY LIMITED`
  - aliases: `CHAN TAI MAN CO LTD`, `C T M CO LTD`
  - active reports: one medium-severity report
- `555-666-777-003` → `HARBOUR VIEW TRADING LTD`
  - aliases: `HARBOUR VIEW TRADING`, `HARBOURVIEW TRADING LTD`
  - active reports: one high-severity report and one medium-severity report

## Example requests / responses

### 1. Beneficiary check with clean account

Request:

```json
{
  "recipient_name": "Apex Solutions Ltd",
  "account_number": "123-456-789-001"
}
```

Response:

```json
{
  "name_account_check": "match",
  "reported_risk_status": "none"
}
```

### 2. Beneficiary check with risky account

Request:

```json
{
  "recipient_name": "Chan Tai Man Co Ltd",
  "account_number": "987654321002"
}
```

Response:

```json
{
  "name_account_check": "close_match",
  "reported_risk_status": "reported"
}
```

### 3. Report risky beneficiary

Request:

```json
{
  "account_number": "555666777003",
  "recipient_name": "Harbour View Trading Ltd",
  "reason_code": "manual_review",
  "case_id": "CASE-9001"
}
```

Response:

```json
{
  "status": "accepted",
  "report_id": "4"
}
```

## How an agentic bank transfer review system would call this MCP

The upstream bank transfer workflow already knows:

- `recipient_name`
- `account_number`
- `transfer_amount`
- `first_time_transfer`

Recommended sequence:

1. Call `check_beneficiary_for_bank_transfer` with `recipient_name` and
   `account_number`.
2. Combine the MCP result with the existing transfer context
   (`transfer_amount`, `first_time_transfer`, recent channel activity,
   model reasoning, or fraud rules).
3. If the downstream fraud workflow or analyst later confirms risk,
   call `report_beneficiary_risk_for_bank_transfer`.

Suggested bank transfer review logic:

- `name_account_check = mismatch` should increase transfer friction.
- `reported_risk_status = reported` should trigger a warning or manual review.
- `reported_risk_status = high_risk` should trigger stronger friction,
  escalation, or a hold depending on bank policy.

## Notes

- Raw account numbers are never stored in SQLite.
- Account numbers are hashed for lookup and masked for logging/display.
- Outputs are JSON-compatible dictionaries designed for MCP tool calls.
- This is a local prototype for **bank transfer beneficiary checking and
  scam-risk reporting**, not a production fraud platform.
