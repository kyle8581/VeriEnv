from __future__ import annotations

import argparse

from app.core.config import settings
from app.db.init_db import reset_db_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Backend management commands")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("reset-db", help="Delete local DB and re-seed")

    args = parser.parse_args()
    if args.cmd == "reset-db":
        reset_db_file(settings.DATABASE_URL)
        print("OK: reset-db")


if __name__ == "__main__":
    main()

