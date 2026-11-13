# Rithan Technologies Website

Static company website migrated from `srv1632013` (old IP `31.97.202.224`) to `srv2078618` (new IP `187.126.126.42`) on 2026-10-26.

## Repository contents

- `site/`: Complete public web root, including the homepage, images, legal pages and linked static microsites. Served directly by Nginx from `/srv/rithantechnologies-website/site`.
- `ops/nginx/rithantechnologies.com.conf`: HTTP/HTTPS Nginx virtual host including the existing main-domain WhatsApp webhook.
- `README.md`: Deployment and recovery notes.

The application has no Node.js build, database, or container requirement.

## Configure a new VPS

1. Install Nginx and Certbot. Clone this repository to `/srv/rithantechnologies-website`. Make the repository path and `site/` readable by Nginx but keep `.git` outside the web root.
2. Create `/var/www/rithan-acme/.well-known/acme-challenge` (readable by Nginx).
3. Obtain a separate Let's Encrypt certificate for `rithantechnologies.com` and `www.rithantechnologies.com` with Certbot webroot:
   `certbot certonly --webroot -w /var/www/rithan-acme -d rithantechnologies.com -d www.rithantechnologies.com`.
   DNS must point to the server during validation, or the old site must temporarily relay ACME challenges to it.
4. Install `ops/nginx/rithantechnologies.com.conf` as `/etc/nginx/sites-available/rithantechnologies.com.conf`, enable its symlink in `sites-enabled`, then run `nginx -t` before `systemctl reload nginx`.
5. Verify both HTTPS hostnames, `/privacy/`, `/terms/`, public images and WhatsApp webhook routing.
6. Point both DNS A records (apex and `www`) to the new VPS IP. Check for obsolete AAAA records.
7. After DNS propagation, run `certbot renew --dry-run` to confirm future automatic renewal on the new VPS.

## Existing webhook integration

The company domain routes `GET/POST /webhooks/whatsapp` through Nginx to `http://127.0.0.1:4300`. This is the existing Rithan AI webhook, not part of the static website. Keep that service and routing intact during any migration. The AI and WooCommerce sites on this VPS have independent Nginx configurations.

## Rollback

Keep the old VPS's main website and HTTPS Nginx configuration available until DNS migration and production tests pass. The old public web root was `/var/www/rithan`; the source website was copied without modification. Restoring the old A records can serve as a DNS rollback, subject to propagation.

## Repository history

Initial migration commit is made on the `main` branch locally. Configure an approved Git remote and push `main` after the repository owner provides the destination Git URL and authorizes authentication. Do not commit TLS keys, credentials or application environment files.

## WhatsApp AI product page (2026-10-29)

- `site/whatsapp-ai/index.html` is Rithan AI's standalone, original branded
  WhatsApp AI service page. No third-party product code is included.
- `site/index.html` links to `/whatsapp-ai/` from its desktop/mobile navigation,
  footer and existing AI section. Existing project demos and legal pages remain
  untouched.
- The interactive conversations are scripted illustrations, not a live WhatsApp
  chat or a claim that every optional integration is available now.
- The public contact links use the same Rithan Technologies WhatsApp number
  and email as the company homepage.
- The original homepage backup from this deployment is kept outside the Git
  repository at `/var/backups/rithantechnologies-site/index.html.before-whatsapp-ai.20261029.bak`.
- On future VPS deployments, this static page is included automatically by
  cloning the website repository and serving its `site/` directory.


## Rithan AI public product UI and signup (2026-11-05)

- The public WhatsApp-only product page is `/whatsapp-ai/`, with its base
  `index.html`, `v3.css`, and latest Orbion-inspired `v4-orbion.css`.
  Designs are original Rithan-branded markup; no Orbion code or images are used.
- Public navigation includes **Sign in** -> `https://ai.rithantechnologies.com/`
  and **Sign up** -> `/whatsapp-ai/signup/`.
- The public sign-up page is **request access**, not open self-registration.
  Client account creation still requires an administrator-issued private invitation.
  The static form validates the business contact details locally, then opens a
  prefilled WhatsApp message to the Rithan Technologies business number; the
  visitor must send it manually. Email is available as an alternative.
  There is no public database write, payment collection, user provisioning, or
  messaging API endpoint introduced by this static page.
- Approved subscription prices on both the homepage and product page are
  ₹999 / 1 month, ₹2,398 / 3 months, ₹4,196 / 6 months, and
  ₹5,994 / 12 months. Payment and activation remain manual; marketing pages
  must not advertise AI credit/reply limits.
- Existing Meta webhook routing and the Rithan AI application on the
  `ai.rithantechnologies.com` subdomain are separate, unchanged services.
- Verify changes with `python3 scripts/check-rithan-ai-landing.py`, and
  request HTTP 200 from `/whatsapp-ai/`, `/whatsapp-ai/v4-orbion.css`,
  and `/whatsapp-ai/signup/`. The website needs no build pipeline.


## Rithan AI functional self-service signup (2026-11-05)

- The public Sign up links now go directly to the secure SaaS application at
  `https://ai.rithantechnologies.com/signup` (responsive light theme).
- The older `/whatsapp-ai/signup/` path is retained as an immediate redirect
  and accessible fallback link. Its earlier static form is no longer the
  registration authority. `light-signup.css` is preserved as an unused visual
  draft and is not loaded by the redirect page.
- Clients submit their own details and password, confirm their email via
  a single-use link, and receive an isolated, paused workspace. A platform
  administrator must verify/review the account, and manual subscription
  activation is separate. WhatsApp connection is client-owned and remains
  subject to Meta authorization and messaging controls.
- The full signup/login implementation, Postmark integration and database
  migration live in the separate Rithan AI Git repository. This public website
  must NOT host or replicate authentication endpoints or credentials.
- Public marketing pricing stays at ₹999, ₹2,398, ₹4,196, ₹5,994 for the four
  approved subscription durations; no public reply/AI-credit limit claims.

## Privacy-conscious first-party site analytics (2026-11-12)

The static company website can track aggregate page views and contact link
clicks without a third-party tracker or a separate application server.

- `site/assets/visit-analytics.js` sends a same-origin POST for each supported
  page load and clicks on `tel:`, `mailto:`, and WhatsApp links. The homepage's
  JavaScript WhatsApp form also records a click. It respects Do Not Track and
  Global Privacy Control preferences.
- The event URL contains **only allowlisted page and contact categories**. No
  cookies, visitor/session IDs, IP addresses, URL queries, hash fragments,
  message contents, contact numbers, or user agents are written to the
  **event log**.
- `ops/nginx/rithantechnologies.com.conf` writes JSONL **access logs** to
  `/var/log/nginx/rithantechnologies-access.log`, including hostname, IP,
  HTTP status, path (no query string), user agent and coarse referrer source.
  Access logs are for short-term operations/security, not identifying contacts.
  Events go to `/var/log/nginx/rithantechnologies-events.log` with time,
  hostname, event category and status only. Only 204 events are counted.
- The VPS's pre-existing `/etc/logrotate.d/nginx` rotates `*.log` daily
  with 14 retained rotations. Logs must remain restricted to Nginx/admin
  users. IP addresses appear in the access log but **not** the event log.
- The fixed POST endpoint rejects invalid methods (405), categories (404),
  and foreign origins (403). These reduce accidental noise, but determined
  automated clients can forge requests. **Counts are not unique people**.
- The Nginx config serves the public static website with HTTPS redirect,
  WhatsApp webhook at `/webhooks/whatsapp`, and ACME challenge handling.
  Analytics categories and access logging remain restricted as documented.

### Deploy on srv2078618

Do this as **root**, after the GitHub `main` branch has the change. Never
overwrite an uncommitted live checkout or touch other site configurations.

```bash
cd /srv/rithantechnologies-website
git pull --ff-only origin main
bash ops/deploy-analytics-root.sh
```

The deploy script checks the repository, fast-forwards from `origin/main`,
backs up the active Nginx site configuration, creates the two private log
files only if absent, validates `nginx -t`, and reloads Nginx. It restores
the previous config if validation/reload fails.

### View aggregate reports

```bash
cd /srv/rithantechnologies-website
python3 scripts/analytics-report.py --days 7
```

Reading the rotated access logs may require root or membership in `adm`.
The reporter displays page and contact counts, request status summaries,
and coarse referrer sources, but does not print IPs or browser identifiers.
Historical click/pageview events cannot be reconstructed before deployment.

For a **future client VPS**, clone this repository as a starting point but
configure its own hostnames, certificate, log file names, web root, and
allowed event pages. Do not copy WhatsApp tokens, unrelated Nginx hosts,
private keys, or the existing webhook upstream into a client setup.

## Public website and price-free company demo (2026-11-13)

The main public website is enabled. The standalone page at
`/whatsapp-ai/free-trial/` is specifically for company referrals: it describes
free-trial onboarding and links to the SaaS sign-up without subscription prices.
The standard `/whatsapp-ai/` marketing page and public subscription prices
are unchanged. Account review and manual activation are still required.
