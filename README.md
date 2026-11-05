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
