#!/usr/bin/env bash
# Root-only, idempotent deployment for the Rithan Technologies website analytics.
# Does not touch any other virtual host, service, webhook, or app.
set -Eeuo pipefail

if [[ $(id -u) -ne 0 ]]; then
    echo "Run as root: sudo bash ops/deploy-analytics-root.sh" >&2
    exit 1
fi

repo=/srv/rithantechnologies-website
target=/etc/nginx/sites-available/rithantechnologies.com.conf
source_file=$repo/ops/nginx/rithantechnologies.com.conf
cd "$repo"

if [[ $(git branch --show-current) != main ]]; then
    echo "Stopping: website checkout must be on main." >&2
    exit 1
fi
if [[ -n $(git status --porcelain) ]]; then
    echo "Stopping: local website checkout has uncommitted changes." >&2
    exit 1
fi

# The repository has to remain the source of truth; never deploy VPS-only edits.
git fetch origin main
git merge --ff-only origin/main

# Safety: maintain the owner's public-site restore and existing special routes.
grep -Fq 'location / {' "$source_file"
grep -Fq 'try_files $uri $uri/ =404;' "$source_file"
grep -Fq 'location = /webhooks/whatsapp' "$source_file"
grep -Fq 'location ^~ /.well-known/acme-challenge/' "$source_file"
grep -Fq 'rithantechnologies-events.log' "$source_file"

# Existing /etc/logrotate.d/nginx already rotates every /var/log/nginx/*.log
# daily, retaining 14 copies. Create new logs with restricted permissions.
for file in /var/log/nginx/rithantechnologies-access.log /var/log/nginx/rithantechnologies-events.log; do
    if [[ ! -e "$file" ]]; then
        install -o www-data -g adm -m 0640 /dev/null "$file"
    fi
done

backup="$target.before-analytics-$(date -u +%Y%m%d-%H%M%S)"
cp -a "$target" "$backup"
install -o root -g root -m 0644 "$source_file" "$target"

restore() {
    echo "Nginx check/reload failed; restoring previous website config." >&2
    cp -a "$backup" "$target"
    /usr/sbin/nginx -t || true
    systemctl reload nginx || true
    exit 1
}

if ! /usr/sbin/nginx -t; then
    restore
fi
if ! systemctl reload nginx; then
    restore
fi

echo "Analytics Nginx config active. Public website enabled."
echo "Old config kept: $backup"
echo "Report command: python3 $repo/scripts/analytics-report.py --days 7"
