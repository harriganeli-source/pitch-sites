# Clean Flow Water Solutions: funnel architecture brief (v2)

Purpose: the build plan for the lead funnel behind a marketing site for a small water-filtration installer in Rochester, NY. Two owners, no staff, no CRM, all sales start from Instagram/Facebook/YouTube ads they run themselves. The builder is one developer who hand-codes static sites on Vercel. Scope rule: build the website and what feeds it, keep the lead-delivery system working under a defined care agreement, and never run the client's sales process. v2 incorporates an outside review; the changelog is at the end.

## 1. Stack

- Static HTML/CSS/JS on Vercel, no framework, no CMS. Lenis smooth scroll. A few Vercel serverless functions (Node) for anything that needs a secret.
- Client-owned accounts for everything that holds their data: Google account (Sheets, Business Profile, GA4 if used), email platform, sending domain, domain registrar. Secrets in Vercel environment variables. The Vercel project sits in the developer's team and is transferable. The Google Cloud project and service account are part of the handoff plan.
- No CRM and no database. The Google Sheet is the working lead record; email is notification and fallback. Durable storage with retry states is the upgrade path if unattended recovery is ever promised.
- Why a custom endpoint rather than a form service: server-side validation, the recommendation rules, attribution, and conditional email enrollment all live in one small integration the developer can understand, test, and hand over. Fewer vendors is not the argument; a legible integration is.

## 2. The quiz

One client-side multi-step form, identical on the landing page and on every per-system page. No pre-seeding from the page: the page someone is browsing must not tilt the recommendation. The landing page is recorded on the lead for attribution only.

The contact step is announced up front: finishing the quiz requests a callback. Product explanations remain readable on the page without submitting anything; what is gated is the personalized next step.

Steps:
1. Town or ZIP (service-area check and local context).
2. Water source: city / well / not sure (the main routing decision).
3. Household size: 1-2 / 3-4 / 5+ (sizing context).
4. Main concerns, multi-select: hard water or scale, taste or smell, staining, well water safety, not sure (treatment category). One deterministic primary concern is derived.
5. Contact: name, phone, email. No street address. A one-line notice: "You will also get a short series of emails about your water. Unsubscribe any time." (Series applies to the upgraded tier.)
6. Result: the system that likely fits, or "needs a closer look": the default for well-water safety concerns, for "not sure," and for combinations the rules do not cover. Then: "Nick or Reese will confirm before anything is installed and call you within [agreed window, business hours]."

Rules: a small server-side table (source, primary concern, household, town context) to one of four systems or "needs assessment." Approved by the client, versioned, version recorded on every lead. Town is context and eligibility, never a diagnosis. Evaluated only on the server; the browser echoes the result.

Behavior: progress kept in memory and sessionStorage, cleared on success. Each step fires "step viewed" and "step completed" events. Spam: honeypot, Cloudflare Turnstile on the contact step (tokens are single-use and expire; a retry re-verifies), rate limiting enforced across instances (not function memory).

## 3. Submission, logging, and the failure contract

Client POSTs JSON with an idempotency key to /api/lead. The function, in order:

1. Validate, verify Turnstile, compute the recommendation, assign a submission ID.
2. Persist the lead: append a row to the client-owned Google Sheet via a service account limited to that sheet. Values written as literals (no formula injection). Intake columns protected; client-editable columns (status, notes) designated. Columns: submission ID, timestamp, name, phone, email, town, source, household, concerns, primary concern, recommended result, rules version, landing page, utm_source, utm_medium, utm_campaign, utm_content, notice version, status, notes.
3. Send the owner notification (their named inbox) with every field and the submission ID. If the sheet write failed, the subject says so and the email says the lead must be added by hand.
4. Send the customer acknowledgement (section 4) with the submission ID.
5. Respond to the browser with the result.
6. Downstream, tracked to completion before the function exits: email-series enrollment (upgraded tier). Its failure never invalidates a saved lead.

Rules: each destination has its own timeout and error handling; the customer acknowledgement alone never counts as captured; a failed sheet write raises an alert to the developer; the idempotency key prevents duplicate rows and emails on retry; one immediate retry on the sheet call. Missing-row recovery is manual from the notification email and is documented for the client. Provider acceptance of an email is not proof of inbox delivery.

Pre-launch partial-failure tests: sheet unavailable, email provider unavailable, email platform unavailable, double submit and browser retry, lead saved but response lost, expired Turnstile token. Test submissions are flagged and kept out of live sequences and reports.

## 4. Contacting the customer

- Immediate acknowledgement email from a monitored address on their domain (SPF, DKIM, DMARC set at DNS): the request arrived, what they told us, the likely result, who will call and within what window. No price. Sender identity and physical address in the footer.
- No SMS. No booking calendar unless they actually maintain appointment slots.
- The quote and the call are manual, by the owners, from the inbox or the sheet. The callback window is agreed in business hours before launch.

## 5. Email series (upgraded tier)

- Provider: one platform for both acknowledgement and marketing email where it supports both reliably (Brevo evaluated first; verify plan limits before promising it stays free). Two providers only if a concrete reason appears. Same sending domain either way, so separation is not a reputation guarantee.
- Enrollment: the endpoint subscribes the contact by API with tags for town, primary concern, and result. Sequence of six emails at day 1, 3, 6, 10, 15, 22 (the acknowledgement goes at once; the series never lands the same minute). Email one uses merge fields for town and concern; the rest are general.
- Consent model (owner decision): giving an email for the quiz result enrolls the person; the notice at the contact step says so; every email carries identity, address, and a working unsubscribe honored promptly. Timestamp, notice version, and source stored with the lead. Repeat submissions do not restart the series; API updates never undo an unsubscribe.
- Responsibilities: the developer writes six emails, sets up the platform on the client's account, and hands it over. The business owns its messages and opt-outs; the platform supplies tools. Replies, deliverability, list hygiene, and new sequences are the client's or separately scoped; text changes after launch are quoted.

## 6. Reviews

- Google Business Profile is the review destination. The client sends a review link with a short text after each install, by hand.
- On the site: testimonials customers have given permission to use, kept verbatim in the site files and updated during care, plus a link to the Google reviews page. Google-sourced review text is not stored or reproduced. A live rating and count is added only if implemented within Google's current Places terms, with a graceful fallback, never as a dependency the page needs.

## 7. Measurement and the 90-day review

- Vercel Web Analytics custom events (Pro plan): quiz_step_viewed and quiz_step_completed per step, lead_accepted (fired only on a confirmed save, never on the button click), cta_click with location, section_visible (visibility, not reading). UTMs captured on landing and written to the lead row. Repeat step views deduplicated per session.
- Ad conversion tracking (Meta pixel or Conversions API, Google/YouTube conversion) settled with the client before launch; the ad platforms report what they report, and UTMs on the lead row tie leads to campaigns. Neither ties leads to installations; that is the client's status column.
- 90-day review: observational by default. Step-by-step drop-off, leads by landing page and source, sections seen, results by town and system. Confirm before launch that the event history needed at day 90 will still be available.
- A/B of the opening: only for a substantial change, with a predefined primary outcome and stopping rule, and only if traffic supports a fair comparison. No middleware assignment is built until there is a test to run.

## 8. Per-system landing pages

Four pages (hard water, taste and odor, staining, well water) so ads deep-link to a matching page. The quiz on each is the same quiz.

## 9. Security and privacy

HTTPS only, Turnstile, cross-instance rate limiting, no PII in analytics events, a short privacy note under the form, secrets only in Vercel env, service account scoped to one sheet, sessionStorage cleared on success.

## 10. Who owns what

- Client: calling leads, quoting, marking status, requesting reviews, approving water claims and the rules table, replying to customers, paying for subscriptions and the domain.
- Developer under care: form delivery, credentials, the sheet and email connections, a monthly end-to-end test of the form, technical recovery when a provider changes something, replies within one business day.
- Separately scoped: new pages, new features, new email campaigns, major third-party migrations.

Pricing on the proposal: hosting and funnel watch $80/month or $900/year; care $250/month or $2,100/year including hosting and funnel watch plus up to four small updates a month.

## 11. Revisions after outside review (Sept 15, 2026)

Adopted:
- Sheet is the working lead record; email is notification and fallback, not a second record of truth. Every submission gets a unique ID that appears in the sheet row and both emails. Protected intake columns; client-editable columns designated. Per-destination timeouts and error handling. If the sheet write fails, the owner notification says so in the subject and the lead must be added by hand; the developer gets a failure alert. Customer confirmation alone never counts as capture. Idempotency key on submit so retries do not duplicate rows or emails. Turnstile tokens are single-use, so a retry re-verifies.
- Persist the lead first, respond, then run downstream actions (marketing enrollment) independently; nothing is left running untracked after the response.
- Pre-launch partial-failure tests: sheet down, email provider down, marketing platform down, double submit, saved-but-response-lost, expired token.
- Town is context and service-area eligibility, not a diagnosis. Water source is the main routing decision, concerns give the treatment category, household size is sizing context, testing and install details make the final selection. "Needs assessment" is a valid result, and the default for well-water safety concerns and "not sure." Rules table approved by the client, versioned, version recorded on each lead.
- Per-system pages do not preselect or skip anything; the quiz is identical everywhere (owner decision, stricter than the reviewer suggested).
- The contact step says up front that finishing the quiz requests a callback. Product explanations stay readable without submitting. Street address removed from the form. Callback window defined in business hours with the client.
- Email series: no opt-in checkbox (owner decision). Giving an email for the quiz result enrolls the person; the contact step carries a one-line notice ("You will also get a short series of emails about your water. Unsubscribe any time."). Every email carries sender identity, a physical address, and a working unsubscribe honored promptly. Store timestamp, notice text version, and source with the lead. Repeat submissions do not restart the series; API updates never undo an unsubscribe; one deterministic primary concern; enrollment failure never invalidates a saved lead. Acknowledgement goes now, the series starts later, never two emails at once. One provider for both transactional and marketing (Brevo evaluated first) unless a reason appears for two. Monitored reply address.
- Reviews: customer-permitted testimonials in site files plus a link to Google reviews. Places API rating/count only if implemented within Google's terms, with graceful fallback, never a critical dependency. Google-sourced review text is not stored in JSON.
- Analytics: step viewed, step completed, and lead accepted instrumented distinctly; a button click is not a saved lead. Custom events are on the Pro plan (the developer's team is Pro). Ad conversion tracking settled before launch. First 90-day review observational by default; A/B only for a substantial change with a predefined outcome and stopping rule; no middleware assignment until there is a test to run.
- Rate limiting enforced across instances, not in function memory. Sheet values written as literals. Session storage cleared on success. Test submissions kept out of live sequences and reports. Google Cloud project and service account in the handoff plan.

Ownership split adopted as written: client calls, quotes, marks status, requests reviews, approves water claims and rules, replies to customers, pays subscriptions; developer keeps form delivery, credentials, integrations, and technical recovery working under a defined care agreement; new pages, features, campaigns, and migrations are scoped separately.

Pricing adopted on the proposal: hosting and funnel watch $80/month or $900/year (site, domain settings, quiz, sheet and email connections, monthly test, one-business-day replies); care $250/month or $2,100/year including hosting and funnel watch plus up to four small updates a month. The reviewer suggested $1,800 and $2,400 with a one-hour cap; the lower hosting number was chosen for this buyer, and the update cap is expressed in requests rather than hours by house rule.
