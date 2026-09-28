"""Summarize lifecycle probe JSON lines into candidate-hit bursts."""

import argparse
from datetime import datetime
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--gap", type=float, default=0.5,
                        help="Seconds of quiet that start a new hit burst")
    args = parser.parse_args()
    with open(args.path, encoding="utf-8-sig") as file:
        records = [json.loads(line) for line in file if line.lstrip().startswith("{")]
    hits = [record for record in records if record["kind"] == "hit"]
    bursts = []
    for hit in hits:
        instant = datetime.fromisoformat(hit["at"])
        if bursts and bursts[-1]["name"] == hit["name"] and \
                (instant - bursts[-1]["last"]).total_seconds() <= args.gap:
            bursts[-1]["last"] = instant
            bursts[-1]["count"] += 1
        else:
            bursts.append({"name": hit["name"], "first": instant,
                           "last": instant, "count": 1, "tid": hit["tid"]})
    for burst in bursts:
        print(f"{burst['first'].isoformat(timespec='milliseconds')} "
              f"to {burst['last'].isoformat(timespec='milliseconds')} "
              f"{burst['name']}: {burst['count']} hit(s), thread {burst['tid']}")
    print(f"Total: {len(hits)} hit(s); "
          f"detached: {any(item['kind'] == 'detached' for item in records)}")


if __name__ == "__main__":
    main()
