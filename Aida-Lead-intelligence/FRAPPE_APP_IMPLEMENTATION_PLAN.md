## Aida Lead Intelligence – Frappe App Implementation Plan

### Goal
Build the entire Aida Lead Intelligence solution natively as a Frappe app within the Mocxha (ERPNext rebrand) platform, replacing the standalone Flask app. Keep third‑party APIs (Apify, Apollo via RapidAPI, Google GenAI) but call them directly from the Frappe app.

### Scope (now)
- In-scope: lead generation, enrichment scaffold, AI criteria extraction, AI lead scoring, email templates/sending/tracking, campaigns, sequences, basic automation, analytics, ERPNext lead creation.
- Out-of-scope (for now): compliance features, SMS/text outreach.

### App metadata
- **App name**: `aida_lead_intelligence`
- **Python module**: `aida`
- **Target site**: Mocxha/ERPNext site(s)

### High-level architecture
- **DocTypes**: Replace SQLite tables with Frappe DocTypes.
- **Services**: Python modules for integrations (Apify/Apollo), AI criteria extraction, lead scoring, email sending/tracking, sequences/automation.
- **APIs**: Whitelisted methods to expose functionality (for Desk UI or external clients if needed).
- **Background jobs**: `frappe.enqueue` for long tasks; Scheduler events for recurring tasks (sequence engine, automation checks).
- **UI**: Desk List/Form views, Pages for dashboards, Reports for analytics.
- **Security**: Use Frappe auth/roles/permissions; guest access only for tracking endpoints.

### DocTypes (schema outline)
- **Aida Lead Generation**
  - Fields: user (Link User), query (Data), source (Select: gmaps/apollo/ai_agent/api_generate), generated_count (Int), synced_count (Int), status (Select: pending/success/failed), started_at/finished_at (Datetime), logs (Long Text)
- **Aida Lead**
  - Fields: owner_user (Link User), lead_generation (Link Aida Lead Generation), name/company_name (Data), email (Data), phone (Data), website (Data), address/city/state/country/postal_code (Data), rating (Float), review_count (Int), category (Data), data (JSON), erpnext_lead (Link Lead), is_synced (Check)
- **Aida Lead Score**
  - Fields: aida_lead (Link Aida Lead), score (Int), status (Select: HOT/WARM/COLD), factors (JSON), recommendations (Small Text), confidence (Select), reasoning (Long Text), scored_at (Datetime)
- **Aida Email Template**
  - Fields: name (Data), subject (Data), content (HTML), variables (Data), category (Data), is_active (Check)
- **Aida Campaign**
  - Fields: name (Data), description (Small Text), status (Select: draft/active/paused/completed)
- **Aida Sequence** + child **Aida Sequence Step**
  - Sequence Fields: campaign (Link Aida Campaign), name (Data), description (Small Text), is_active (Check)
  - Step Fields (Child Table): sequence (Link), step_no (Int), delay_hours (Int), template (Link Aida Email Template), condition (Data/Code), notes (Small Text)
- **Aida Sequence Instance**
  - Fields: user (Link User), sequence (Link Aida Sequence), aida_lead (Link Aida Lead), current_step (Int), status (Select: active/paused/completed/failed), next_due (Datetime), started_at/completed_at (Datetime)
- **Aida Email Tracking**
  - Fields: user (Link User), campaign (Link Aida Campaign), sequence (Link Aida Sequence), sequence_instance (Link), aida_lead (Link Aida Lead), email_address (Data), subject (Data), template (Link Aida Email Template), status (Select: pending/sent/delivered/opened/clicked/replied/bounced/unsubscribed), sent_at/opened_at/clicked_at/... (Datetime), tracking_id (Data, Unique), open_count/click_count (Int)
- **Aida Email Event**
  - Fields: email_tracking (Link Aida Email Tracking), event_type (Select: sent/opened/clicked/replied/bounced/unsubscribed/spam), event_data (JSON), ip_address (Data), user_agent (Data), location (Data)
- **Aida Email Server Config** (optional; else use core Email Account)
  - Fields: user (Link User), name (Data), smtp_server (Data), smtp_port (Int), sender_email (Data), sender_password (Password), sender_name (Data), use_ssl (Check), use_tls (Check), is_active (Check)
- **Aida Automation Rule**
  - Fields: user (Link User), name (Data), trigger_type (Select: open/click/reply/bounce/step_completed), trigger_conditions (JSON), action_type (Select: send_next_step/tag_lead/create_task), action_data (JSON), is_active (Check)
- **Aida API Key**
  - Fields: user (Link User), service_name (Select: apify/apollo/genai), api_key (Password), is_active (Check)
- **Customizations on ERPNext Lead** (optional)
  - Fields: google_maps_url, place_id, rating, review_count, latitude, longitude, category (or keep inside `Aida Lead.data`)

### Services/modules (server-side)
- `aida.lead_generation.service`
  - Methods: `run_gmaps(criteria)`, `run_apollo(criteria)`, `process_gmaps_item(raw)`, `process_apollo_item(raw)`
  - Persist to `Aida Lead Generation`, create `Aida Lead` rows; enqueue long jobs.
- `aida.ai.criteria`
  - Methods: `extract_criteria(user_query)` using Google GenAI; fallback regex extraction.
- `aida.scoring.service`
  - Methods: `score_lead(aida_lead)`, `batch_score(leads)`; Gemini prompt + fallback.
- `aida.email.send`
  - Methods: `send_with_template(user, aida_lead, template, campaign=None, sequence=None)` → creates `Aida Email Tracking`, decorates content with pixel, sends via `frappe.sendmail` or custom SMTP from `Aida Email Server Config`.
- `aida.email.track`
  - Guest endpoints: `track_open(tracking_id)`, `track_click(tracking_id, url)`, `unsubscribe(tracking_id)` → update `Aida Email Tracking` + log `Aida Email Event`, return 1x1 GIF or redirect.
- `aida.sequences.engine`
  - Scheduler job: find due `Aida Sequence Instance`, send step email, advance state, compute `next_due`.
- `aida.automation.engine`
  - On email events, evaluate `Aida Automation Rule` and enqueue actions.

### Whitelisted API (examples)
- `aida.api.generate_leads(criteria_json)`
- `aida.api.generate_apollo_leads(url, page)`
- `aida.api.score_lead(aida_lead_name)` / `aida.api.batch_score(aida_lead_names)`
- `aida.api.email.templates.*` CRUD
- `aida.api.email.send(lead, template, subject, content, campaign, sequence)`
- `aida.api.email.analytics(campaign|sequence|range)`
- `aida.api.sequences.*` CRUD + start instance
- Guest:
  - `aida.api.track_open(tracking_id)` → returns 1x1 GIF
  - `aida.api.track_click(tracking_id, url)` → redirects
  - `aida.api.unsubscribe(tracking_id)` → JSON success

### Background jobs & scheduler
- Use `frappe.enqueue(long=True)` for: lead generation (Apify/Apollo), batch scoring, heavy analytics.
- Scheduler Events:
  - Every 5–10 minutes: sequence engine tick.
  - Hourly: automation cleanup, stuck job checks.

### UI (Desk)
- List/Form for all DocTypes.
- Pages:
  - **Aida Dashboard**: KPIs (generated leads, scored status distribution, open/click rates, ERP connection state), charts (Frappe Charts), quick actions.
  - **Lead Generation**: criteria form (query/source/filters), run job, show results grid with “Add to ERPNext Lead”.
  - **Email**: Template builder (HTML editor), Campaigns, Sequences (child steps grid).
  - **Tracking**: Tracking detail with events timeline; filters by campaign/sequence.
- Reports:
  - **Scoring Summary** (date range), **Campaign Analytics**, **Sequence Performance**.

### Email tracking details
- Open pixel: `<img src="/api/method/aida.api.track_open?tracking_id=xxx" width="1" height="1" style="display:none;"/>`
- Click tracking: links can be wrapped by future enhancement; initially support explicit tracked links.
- Unsubscribe: mark in `Aida Email Tracking` and suppress future sends for that recipient.

### ERPNext/Mocxha integration
- From `Aida Lead`, action: **Create ERPNext Lead** → map fields and insert `Lead`; optionally attach a Note with detailed info.
- Avoid strict `industry` mapping unless custom field exists; store category into custom or Note if needed.

### Security
- Use Frappe roles/permissions; restrict DocTypes by owner where appropriate.
- Only tracking endpoints are `allow_guest`.
- Encrypt API keys using Password field; optionally integrate with Frappe’s secret storage.

### Dependencies
- Python packages (to add in app `requirements.txt`):
  - `apify-client`, `requests`, `google-generativeai`, optional `langchain`
- Environment/site config:
  - API keys: Apify, Apollo (RapidAPI), Google GenAI

### Migration (optional)
- Bench command to import from existing `platform.db` → DocTypes (`Aida Lead Generation`, `Aida Lead`, `Aida Email Template`, etc.).
- Map `lead_scores`, `email_tracking`, `campaigns/sequences` JSON to new DocTypes.

### Phased delivery & checklists
- **Phase 1: App scaffold + core DocTypes + lead gen + ERP create**
  - Create app, install on site, add requirements.
  - Implement DocTypes: Lead Generation, Lead, API Key.
  - Implement `aida.lead_generation.service` for Apify/Apollo and whitelisted `generate_*` APIs.
  - Add action to create ERPNext `Lead` from `Aida Lead`.
  - Basic Dashboard with counts.
  - Deliverables: create leads end‑to‑end; ERP lead creation works; permissions in place.
- **Phase 2: AI criteria + AI lead scoring**
  - Add `aida.ai.criteria` and `aida.scoring.service` (Gemini + fallback).
  - DocType: Aida Lead Score; endpoints for scoring single/batch; scoring summary report.
  - Dashboard: score distribution.
- **Phase 3: Email templates/sending/tracking**
  - DocTypes: Email Template, Email Tracking, Email Event, Email Server Config (if needed).
  - Implement `aida.email.send` and guest tracking endpoints (open/click/unsubscribe) with 1x1 GIF and redirect.
  - Analytics APIs and desk pages for campaign/sequence stats.
- **Phase 4: Campaigns, Sequences, Automation**
  - DocTypes: Campaign, Sequence, Sequence Step, Sequence Instance, Automation Rule.
  - Sequence engine scheduler; automation engine on events.
  - Reports: campaign/sequence performance; pages to manage and monitor instances.
- **Phase 5: UX polish + reports + optional migration**
  - Advanced dashboard widgets, charts, quick actions.
  - Import legacy data from `platform.db` if needed.

### Acceptance criteria (per phase)
- P1: User can run lead generation, see results, and create ERPNext `Lead` with correct mapping.
- P2: User can score leads and view summaries; fallback works without GenAI key.
- P3: User can send tracked emails; opens/clicks appear in tracking views; unsubscribe works.
- P4: User can start sequences; emails send on schedule; events advance steps; automation executes.

### Risks & mitigations
- Third‑party API limits/timeouts → enqueue jobs, retries, backoff.
- Email deliverability → leverage site’s `Email Account`, test DNS, consider rate limiting.
- Custom field mismatches in ERPNext `Lead` → avoid strict fields; use Notes or custom fields.

### Next steps (kickoff)
1. Create Frappe app `aida_lead_intelligence`, install on Mocxha site, commit app skeleton.
2. Add `requirements.txt` (apify-client, google-generativeai, requests).
3. Implement Phase 1 DocTypes and `aida.lead_generation.service` + whitelisted APIs.
4. Build Lead Generation page and Dashboard MVP.
5. Validate ERPNext lead creation on Mocxha dev site. 