# Rithan Technologies automatic website traffic reports

This configuration is ONLY for the main Rithan Technologies marketing site.
It does not modify any other Nginx virtual host, WhatsApp webhook, API,
SPS Track service, or the user's other workloads.

## What happens each day

- The VPS is set to UTC. Cron runs at **01:27 UTC / 06:57 IST** and
  **16:27 UTC / 21:57 IST**, shortly before the user's ChatGPT scheduled
  notifications at 07:00 and 22:00 IST.
- The root-owned exporter reads dedicated Rithan Nginx access/event logs
  (including rotated files) and writes **aggregate-only** JSON snapshots:
  `/var/lib/rithan-analytics/morning-latest.json` and
  `/var/lib/rithan-analytics/evening-latest.json`.
- Morning covers roughly the previous 21:57 to 06:57 IST (9 hours);
  evening covers 06:57 to 21:57 IST (15 hours). The last 3 minutes of
  each interval before the requested notification time are included in
  the **following** report, rather than falsely reporting them.
- The snapshots have directory mode 0750 `root:rithan-ai` and file
  mode 0640 `root:rithan-ai`. The unprivileged ChatGPT VPS connector
  can read the aggregates but **cannot read private original access logs**.
- Root's cron commands log their success/errors through syslog tag
  `rithan-site-analytics`; they do not restart Nginx or touch another
  service. The exporter uses only Python standard library.
- Snapshot data includes page-view and contact-click counts, access
  totals, HTTP status breakdowns, approximate distinct IP counts,
  recognizable bots/scans, referrer categories, repeat-IP counts,
  and counts for the previously investigated IPs. It does not export
  raw IP lists, user-agent strings, cookies, private URLs, or personal
  identification. An IP is not a person.
- Browser-like counters are heuristics, not guaranteed unique visitors.

## Root installation (one-time, after staging)

On the authorized server, after checking stage contents, run:

```bash
bash /home/rithan-ai/rithan-reports-stage/apply-site-reporting.sh
```

The guarded installer checks current Git `main`, remote access and a clean
working tree before copying exactly three new files to the website repo:
`scripts/export-site-analytics.py`,
`ops/cron/rithantechnologies-analytics`, and this documentation.
It commits and pushes to `main`, then installs only the new cron file and
aggregate export directory, leaving all other services/configuration intact.

If `main` has advanced, or an existing cron entry conflicts, the installer
stops to avoid overwriting someone else's work. In such a case, inspect the
stage against the new repository before retrying. Don't delete unrelated
files or services.

## Verify reports

After root installation:

```bash
cat /var/lib/rithan-analytics/morning-latest.json
systemctl is-active cron
journalctl -t rithan-site-analytics -n 20 --no-pager
```

Nightly snapshot is created at 21:57 IST, morning snapshot at 06:57 IST.
No manual logs or copies are needed afterward. ChatGPT daily automations
attempt to read only the corresponding JSON files. If the connected VPS is
unavailable, the automation must report a data-access problem, not invent
a report.

For client VPS deployments, adapt cron timing to the server timezone and
use that client's own domain, logs, service account, and privacy rules.
