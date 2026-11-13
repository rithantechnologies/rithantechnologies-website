#!/usr/bin/env python3
"""Export a restricted, aggregate-only website report for scheduled summaries.

Run as root from cron because raw Nginx access logs are not readable by
the unprivileged report reader. Do not export raw IPs, user agents or URLs
containing query strings.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, time, timedelta, timezone
import gzip
import json
import os
from pathlib import Path
import pwd
import re
import tempfile
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
DEFAULT_ACCESS = Path("/var/log/nginx/rithantechnologies-access.log")
DEFAULT_EVENTS = Path("/var/log/nginx/rithantechnologies-events.log")
DEFAULT_DEST = Path("/var/lib/rithan-analytics")
PAGES = {
    "/": "home",
    "/whatsapp-ai/": "whatsapp-ai",
    "/privacy/": "privacy",
    "/terms/": "terms",
    "/rithan-ai/privacy/": "ai-privacy",
    "/rithan-ai/data-deletion/": "ai-deletion",
}
WATCHED = ("125.16.39.154", "14.97.1.186")
BOT = re.compile(
    r"bot|crawl|spider|scanner|headless|curl/|python|aiohttp|wget/"
    r"|superhumandesktop|ccleaner|facebookexternalhit|meta-external"
    r"|elevenlabs|bytespider|dataprovider|semrush|ahrefs|preview",
    re.I,
)
SCAN = re.compile(
    r"wp-|wordpress|xmlrpc|\\.php$|\\.env|\\.git|/cgi-bin|/admin"
    r"|/login|\\.bak$|/boaform|/vendor/|/actuator",
    re.I,
)


def read_json_lines(base: Path):
    files = [base] + sorted(base.parent.glob(base.name + ".*"))
    if not base.is_file():
        raise RuntimeError(f"Current log is missing: {base}")
    for path in files:
        if not path.is_file():
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                    stamp = datetime.fromisoformat(row["time"])
                    if stamp.tzinfo is not None:
                        yield stamp.astimezone(IST), row
                except (ValueError, TypeError, KeyError):
                    continue


def time_range(slot: str, now: datetime):
    today = now.astimezone(IST).date()
    morning = datetime.combine(today, time(6, 57), IST)
    evening = datetime.combine(today, time(21, 57), IST)
    if slot == "morning":
        return evening - timedelta(days=1), morning
    return morning, evening


def build_report(slot: str, access_file: Path, events_file: Path, now: datetime):
    start, end = time_range(slot, now)
    if now.astimezone(IST) < end:
        raise RuntimeError(f"{slot} report window has not closed: {end.isoformat()}")

    recent_ips = set()
    previously_seen = set()
    browser_ips = set()
    seen_ips = set()
    watched = Counter()
    status = Counter()
    paths = Counter()
    referrers = Counter()
    bot_count = scan_count = browser_requests = raw_total = local_count = 0
    top_suspect = Counter()

    # Only aggregate fields leave this function. Never serialize row['ip'].
    for when, row in read_json_lines(access_file):
        ip = str(row.get("ip", ""))
        if start - timedelta(days=7) <= when < start and ip:
            previously_seen.add(ip)
        if not (start <= when < end):
            continue
        raw_total += 1
        path = str(row.get("path", ""))
        ua = str(row.get("ua", ""))
        code = str(row.get("status", ""))
        method = str(row.get("method", ""))
        is_bot = bool(BOT.search(ua))
        is_scan = bool(SCAN.search(path))
        status[code] += 1
        referrers[str(row.get("referrer_source", "other"))] += 1
        if path in PAGES:
            paths[PAGES[path]] += 1
        if is_bot:
            bot_count += 1
        if is_scan:
            scan_count += 1
            top_suspect[path[:100]] += 1
        if ip:
            seen_ips.add(ip)
            if ip in WATCHED:
                watched[ip] += 1
            if ip == "187.126.126.42" or ip.startswith("127."):
                local_count += 1
            if (method == "GET" and code in {"200", "304"}
                    and path in PAGES and ua.startswith("Mozilla/")
                    and not is_bot and not is_scan):
                browser_requests += 1
                browser_ips.add(ip)

    views = Counter()
    contacts = Counter()
    valid_events = 0
    for when, row in read_json_lines(events_file):
        if not (start <= when < end) or row.get("status") != 204:
            continue
        label = str(row.get("event", "")).strip("/").split("/")
        if len(label) == 3 and label[:2] == ["__rt_events", "page"] and label[2] in PAGES.values():
            views[label[2]] += 1
            valid_events += 1
        elif (len(label) == 4 and label[:2] == ["__rt_events", "contact"]
              and label[2] in PAGES.values()
              and label[3] in {"whatsapp", "email", "phone"}):
            contacts[(label[2], label[3])] += 1
            valid_events += 1

    return {
        "schema_version": 1,
        "site": "rithantechnologies.com",
        "slot": slot,
        "generated_at_ist": now.astimezone(IST).isoformat(timespec="seconds"),
        "window_start_ist": start.isoformat(timespec="seconds"),
        "window_end_ist": end.isoformat(timespec="seconds"),
        "interpretation_note": (
            "Counts reflect HTTP requests, not identified visitors. IPs can represent "
            "proxies, shared networks or bots. A browser-like request does not confirm "
            "a human visit; none of these data identify meeting participants."
        ),
        "access": {
            "total_requests": raw_total,
            "unique_network_ips": len(seen_ips),
            "network_ips_seen_in_previous_7_days": len(seen_ips & previously_seen),
            "http_status_counts": dict(sorted(status.items())),
            "coarse_referrer_request_counts": dict(referrers.most_common()),
            "top_known_page_request_counts": dict(paths.most_common()),
            "recognizable_bot_requests": bot_count,
            "suspicious_scan_requests": scan_count,
            "top_suspicious_paths": dict(top_suspect.most_common(6)),
            "browser_like_successful_page_requests": browser_requests,
            "browser_like_network_ips": len(browser_ips),
            "own_vps_requests": local_count,
            "historically_investigated_ip_request_counts": {
                ip: watched[ip] for ip in WATCHED
            },
        },
        "events": {
            "total_valid": valid_events,
            "page_views": sum(views.values()),
            "page_views_by_page": dict(views.most_common()),
            "contact_clicks": sum(contacts.values()),
            "contact_clicks_by_channel": dict(Counter({
                channel: sum(n for (page, ch), n in contacts.items() if ch == channel)
                for channel in ("whatsapp", "email", "phone")
            })),
            "contact_clicks_by_page_and_channel": {
                f"{page}:{channel}": n for (page, channel), n in sorted(contacts.items())
            },
        },
    }


def save_report(report: dict, dest: Path):
    if not dest.is_dir():
        raise RuntimeError(f"Report directory must exist: {dest}")
    if dest.is_symlink() or (dest.stat().st_mode & 0o022):
        raise RuntimeError("Report directory must not be a symlink or group/world writable")
    owner = pwd.getpwnam("rithan-ai")
    payload = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
    fd, temp_path = tempfile.mkstemp(prefix=".report-", dir=dest)
    try:
        os.fchown(fd, 0, owner.pw_gid)
        os.fchmod(fd, 0o640)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, dest / f"{report['slot']}-latest.json")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", required=True, choices=("morning", "evening"))
    parser.add_argument("--access-file", type=Path, default=DEFAULT_ACCESS)
    parser.add_argument("--events-file", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--reference-time", help="ISO 8601 timestamp, for testing only")
    parser.add_argument("--stdout", action="store_true", help="Print a report, do not save")
    args = parser.parse_args()
    now = (datetime.fromisoformat(args.reference_time) if args.reference_time
           else datetime.now(tz=timezone.utc))
    if now.tzinfo is None:
        parser.error("--reference-time must include a UTC offset")
    report = build_report(args.slot, args.access_file, args.events_file, now)
    if args.stdout:
        print(json.dumps(report, indent=2))
    else:
        save_report(report, args.output_dir)
        print(f"Exported {args.slot} aggregate report for {report['window_end_ist']}")


if __name__ == "__main__":
    main()
