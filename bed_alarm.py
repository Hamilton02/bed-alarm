"""Firm up the bed when the alarm goes off; put it back at bedtime.

  bed_alarm.py wake     -> set your side to WAKE_NUMBER (default 100)
  bed_alarm.py sleep    -> set your side back to its favorite sleep number
  bed_alarm.py status   -> print every sleeper's current state

Credentials and settings come from .env next to this file (see .env.example).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from asyncsleepiq import AsyncSleepIQ

HERE = Path(__file__).resolve().parent


def load_env() -> None:
    env_file = HERE / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def pick_sleeper(api: AsyncSleepIQ, who: str):
    """Match SLEEPER against a first name or a side (L/R/Left/Right)."""
    who = who.strip().lower()
    for bed in api.beds.values():
        for sleeper in bed.sleepers:
            if who in (sleeper.name.lower(), sleeper.side.value.lower(), sleeper.side_full.lower()):
                return sleeper
    names = [f"{s.name} ({s.side_full})" for b in api.beds.values() for s in b.sleepers]
    sys.exit(f"No sleeper matches {who!r}. Found: {', '.join(names) or 'none'}")


async def run(command: str) -> None:
    api = AsyncSleepIQ()
    try:
        await api.login(os.environ["SLEEPIQ_EMAIL"], os.environ["SLEEPIQ_PASSWORD"])
        await api.init_beds()
        await api.fetch_bed_statuses()

        if command == "status":
            for bed in api.beds.values():
                print(f"{bed.name} ({bed.model})")
                for s in bed.sleepers:
                    await s.fetch_favsleepnumber()
                    print(f"  {s.side_full}: {s.name or '-'}  in_bed={s.in_bed}  "
                          f"sleep_number={s.sleep_number}  favorite={s.fav_sleep_number}")
            return

        sleeper = pick_sleeper(api, os.environ.get("SLEEPER", "L"))
        if command == "wake":
            target = int(os.environ.get("WAKE_NUMBER", "100"))
        else:
            await sleeper.fetch_favsleepnumber()
            target = sleeper.fav_sleep_number
        await sleeper.set_sleepnumber(target)
        print(f"{sleeper.name} ({sleeper.side_full}): {sleeper.sleep_number} -> {target}")
    finally:
        await api.close_session()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["wake", "sleep", "status"])
    args = parser.parse_args()
    load_env()
    if not os.environ.get("SLEEPIQ_EMAIL") or not os.environ.get("SLEEPIQ_PASSWORD"):
        sys.exit("Set SLEEPIQ_EMAIL and SLEEPIQ_PASSWORD in .env")
    asyncio.run(run(args.command))


if __name__ == "__main__":
    main()
