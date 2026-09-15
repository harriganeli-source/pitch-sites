# Clean Flow Water Solutions: funnel architecture brief

Purpose: a second opinion on how the lead funnel behind a proposed marketing site should be built. The site is for a small water-filtration installer in Rochester, NY. Two owners, no staff, no CRM, all sales start from Instagram/Facebook/YouTube ads. They run their own ads and want to rely on as few outside parties as possible. Budget is small-business scale. The builder is one developer who hand-codes static sites and hosts on Vercel, and who wants to build the website and what feeds it, not the client's operating process.

Please challenge the choices marked "decision" and tell me where you would do it differently and why.

## 1. Stack

- Static HTML/CSS/JS site on Vercel (no framework, no CMS). Lenis smooth scroll. A few Vercel serverless functions (Node) for anything that needs a secret.
- Client-owned accounts for everything that holds their data: Google account (Sheets, Business Profile, GA4), email sending domain, email marketing platform, domain registrar. Secrets live in Vercel environment variables. The Vercel project sits in the developer's team and is transferable.
- No database. The lead record of truth is a Google Sheet the client owns, plus email.

Decision: no CRM, no database. Sheet + inbox is the system. Is that defensible at 20 to 100 leads a month, or should there be a durable store (Vercel KV/Postgres) with the sheet as a mirror?

## 2. The quiz

Client-side multi-step form on the landing page and on each per-system page, identical everywhere.

Steps:
1. Town (select from a list of Monroe County and surrounding towns, plus zip). Rationale: the client says water quality is known per town and does not vary house to house, so town drives the recommendation.
2. Water source: city / well / not sure.
3. Household size (1-2, 3-4, 5+).
4. Main concerns (multi-select): hard water or scale, taste or smell, staining, well water safety, not sure.
5. Contact: name, phone, email, street address (optional), consent line for email follow-up.
6. Result screen: "Based on your town and what you told us, the system that likely fits is X. Nick or Reese will confirm before anything is installed and call you within [N hours]."

Result logic: a small JSON table (town -> known water profile) plus (source, concerns) -> one of four systems. Evaluated on the server in the submit function and echoed to the client; the client never computes the recommendation itself, so the table lives in one place.

Behavior: state kept in memory and sessionStorage so a refresh does not lose progress. Each step fires an analytics event. Result is only shown after contact details are submitted (deliberate: the answer is the reward for the lead).

Spam: honeypot field, Cloudflare Turnstile on the contact step, rate limit by IP in the function.

Decision: recommendation shown only after contact submit. Decision: town-driven logic with server-side evaluation.

## 3. Submission and logging

Client POSTs JSON to /api/lead (Vercel function). The function:

1. Validates and checks Turnstile.
2. Computes the recommendation from the shared table.
3. Appends a row to the Google Sheet "Clean Flow Leads" via the Sheets API using a service account the client has shared the sheet with. Columns: timestamp, name, phone, email, address, town, source, household, concerns, recommended system, landing page, variant, utm_source, utm_medium, utm_campaign, utm_content, status (client-owned column, blank).
4. Sends a notification email to the owners' address (single inbox they named) with all fields.
5. Sends a confirmation email to the customer (see section 4).
6. If the client has the email-series option: subscribes the customer to the email platform with tags for town, concern, and recommended system (see section 5).
7. Returns the recommendation to the client.

Failure handling: steps 4 and 5 must succeed independently of 3 and 6. If the Sheets write fails, the lead still emails and the function logs the error; a daily reconciliation is not built (decision). No queue. Retries: one immediate retry on the Sheets call.

Transactional email provider: Resend (or Postmark) on the client's domain, with SPF/DKIM/DMARC set at DNS. Free tier covers the volume.

Alternative considered: Web3Forms or Formspree for the form (email + autoresponder built in) plus a Zapier/Make zap to write the sheet and subscribe to the email platform. Less code, but two more third parties, a monthly zap cost at volume, and the recommendation logic would have to live on the client. Rejected for now (decision).

## 4. Contacting the customer

- Immediate confirmation email, transactional, from a named address on their domain. Contents: your request arrived, here is what you told us, the system that likely fits, Nick or Reese will call within [N hours]. No price. Plain text or minimal HTML.
- No SMS (decision: Twilio adds cost, A2P 10DLC registration, and compliance surface for a two-person company).
- The actual quote and follow-up call are manual, by the owners, from the inbox or the sheet. The site does not schedule calls. Decision: no calendar booking step; would you add one?

## 5. Email series (the upgraded tier only)

- Platform: an email marketing service on the client's account with a free tier and tag-triggered sequences (Kit, MailerLite, or Brevo). The developer writes six emails once and loads them.
- Trigger: the /api/lead function subscribes the contact via the platform API with tags (town, concern, system). A sequence starts on subscribe: day 0, 2, 5, 9, 14, 21. Email 1 uses merge fields for town and concern; later emails are generic. Alternative: four sequences, one per concern, at 4x the writing (not planned).
- Consent: the contact step includes a line stating they will receive a short series of emails about their water and can unsubscribe any time. Unsubscribe, list hygiene, and CAN-SPAM mechanics are the platform's.
- Transactional confirmation (section 4) stays on a separate provider from marketing email, for deliverability.
- Ownership: list, account, and subscription are the client's. The developer sets it up and writes the emails, and does not operate the platform afterwards (replies, deliverability, new sequences are out of scope; text changes are quoted).

Decision: separate transactional and marketing providers. Decision: subscribe-on-submit from the server rather than a platform form embed.

## 6. Reviews

- Google Business Profile is the review source. The client sends a review link with a short text after each install (manual, their process).
- On the site: a reviews section showing the live rating and count via the Places API (New) place details call from a cached serverless function (as on a previous site by the same developer), plus a handful of curated verbatim quotes kept in a small JSON file the developer updates during care. No automated review request, no trigger on install completion (deliberately removed: that is the client's operating process, not the website).

Decision: curated quotes via JSON in care, not a live feed of all reviews. Would you pull full review text from the API instead?

## 7. Measurement and the 90-day review

- Vercel Web Analytics with custom events: quiz_start, quiz_step_1..4, quiz_contact_submitted, result_viewed, cta_click (with location), section_view (IntersectionObserver on major sections). UTMs captured on landing into sessionStorage and written to the lead row.
- Optional GA4 under the client's account if they want ad-platform attribution beyond what the ad managers already report.
- 90-day review: step-by-step drop-off, landing page by ad, sections read, leads by town and system.
- A/B of the opening: two variants of the hero, assignment by a cookie set in Vercel Edge Middleware (or client-side random persisted in localStorage), variant tagged on every event and on the lead row. Compared on quiz_start rate and contact-submit rate. Only claimed as a result where traffic supports it.

Decision: Vercel Analytics events rather than GA4 as the primary. Decision: middleware cookie split rather than a testing tool.

## 8. Per-system landing pages

Four pages (hard water, taste and odor, staining, well water) so ads deep-link to a matching page. The quiz component is identical on every page: same questions, same rules, no pre-seeding from the page (owner decision: the page someone is browsing must not tilt the recommendation). The landing page is recorded on the lead for attribution only.

## 9. Security and privacy

HTTPS only, Turnstile on submit, rate limiting, no PII in analytics events, a short privacy note under the form, secrets only in Vercel env, the service account limited to the one sheet.

## 10. Questions I want answered

1. Sheet + inbox as the record of truth versus a small database with the sheet as a view. Where does this break?
2. Custom /api/lead function versus a form service plus Zapier. Which would you pick for a two-person client who wants to rely on nobody, and why?
3. Confirmation email from a transactional provider versus from the marketing platform. Is the separation worth the second account for a client this small?
4. Subscribe-on-submit from the server: any consent or deliverability problem with that pattern?
5. A/B assignment at maybe 300 to 1,000 visits a month: is a middleware split worth it, or should the 90-day review be observational only?
6. Anything in here that becomes the developer's operational burden after launch that should be pushed back to the client or dropped?

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
