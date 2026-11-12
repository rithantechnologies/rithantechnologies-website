#!/usr/bin/env python3
"""Summarize first-party Rithan website logs without printing visitor identifiers.

Uses only the Python standard library. Run with privileges that can read
/var/log/nginx/rithantechnologies-*.log; no databases or external services.
"""
import argparse
import collections
import datetime as dt
import gzip
import json
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
ACCESS = Path("/var/log/nginx/rithantechnologies-access.log")
EVENTS = Path("/var/log/nginx/rithantechnologies-events.log")


def rows(base: Path):
    # Existing logrotate rule covers /var/log/nginx/*.log and compressed rotations.
    files = [base] + sorted(base.parent.glob(base.name + ".*"))
    for path in files:
        if not path.is_file():
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    try:
                        item = json.loads(line)
                        when = dt.datetime.fromisoformat(item["time"])
                        if when.tzinfo is not None:
                            yield when.astimezone(IST), item
                    except (ValueError, KeyError, TypeError):
                        continue
        except OSError as exc:
            print(f"Cannot read {path}: {exc}")


def report(access: Path, events: Path, days: int):
    since = dt.datetime.now(IST) - dt.timedelta(days=days)
    views = collections.Counter()
    contacts = collections.Counter()
    source = collections.Counter()
    statuses = collections.Counter()
    paths = collections.Counter()
    unknown = 0

    for when, row in rows(events):
        if when < since or row.get("status") != 204:
            continue
        label = str(row.get("event", ""))
        day = when.strftime("%Y-%m-%d")
        parts = label.strip("/").split("/")
        if len(parts) == 3 and parts[:2] == ["__rt_events", "page"]:
            views[(day, parts[2])] += 1
        elif (len(parts) == 4 and parts[:2] == ["__rt_events", "contact"]
              and parts[3] in {"phone", "email", "whatsapp"}):
            contacts[(day, parts[2], parts[3])] += 1
        else:
            unknown += 1

    for when, row in rows(access):
        if when < since:
            continue
        day = when.strftime("%Y-%m-%d")
        statuses[(day, str(row.get("status", "")))] += 1
        path = str(row.get("path", "/"))
        if path in {"/", "/whatsapp-ai/", "/privacy/", "/terms/",
                    "/rithan-ai/privacy/", "/rithan-ai/data-deletion/"}:
            paths[(day, path)] += 1
        category = str(row.get("referrer_source", "other"))
        source[category] += 1

    print(f"Rithan website analytics — last {days} day(s), IST")
    print("Events are counts of requests, NOT unique visitors or named identities.")
    print(f"Page views recorded: {sum(views.values())}")
    print(f"Contact clicks recorded: {sum(contacts.values())}")
    if unknown:
        print(f"Unrecognized event records ignored: {unknown}")

    print("\nDaily page views")
    if not views:
        print("  No events yet (site may be blocked or tracking not deployed).")
    for (day, page), count in sorted(views.items()):
        print(f"  {day}  {page:16} {count:5}")

    print("\nDaily contact clicks")
    if not contacts:
        print("  No clicks recorded.")
    for (day, page, channel), count in sorted(contacts.items()):
        print(f"  {day}  {page:16} {channel:9} {count:5}")

    print("\nAccess-log HTTP status counts")
    if not statuses:
        print("  No dedicated access-log records yet.")
    for day in sorted({day for day, _ in statuses}):
        detail = ", ".join(f"{code}={n}" for (d, code), n in sorted(statuses.items())
                           if d == day)
        print(f"  {day}: {detail}")

    print("\nAccess-log page requests (includes crawlers and refreshes)")
    for (day, path), count in sorted(paths.items()):
        print(f"  {day}  {path:30} {count:5}")

    print("\nCoarse referrer sources (requests, NOT people)")
    for category, count in source.most_common():
        print(f"  {category:15} {count:5}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--access-log", type=Path, default=ACCESS)
    parser.add_argument("--events-log", type=Path, default=EVENTS)
    args = parser.parse_args()
    if not 1 <= args.days <= 365:
        parser.error("--days must be between 1 and 365")
    report(args.access_log, args.events_log, args.days)


if __name__ == "__main__":
    main()
