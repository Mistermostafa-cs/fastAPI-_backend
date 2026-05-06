#!/usr/bin/env python
"""
migrate_to_offerings.py
------------------------
Standalone script to migrate existing ClassSubject rows → SubjectOfferings.

Run from the project root:
    python migrate_to_offerings.py [--year ACADEMIC_YEAR_ID] [--dry-run]

The script is safe to run multiple times; already-migrated rows are skipped.
"""
from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate ClassSubjects to SubjectOfferings (Term 1)."
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Restrict migration to a single AcademicYearID (default: all years).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview counts without writing to the database.",
    )
    args = parser.parse_args()

    # Import here so the script can be run before the app server starts.
    from app.db.models import prepare_models
    from app.db.session import SessionLocal
    from app.services.term_offering_service import migrate_class_subjects_to_offerings

    # Ensure new tables exist
    prepare_models()

    db = SessionLocal()
    try:
        print(
            f"Starting migration "
            f"(year={'all' if args.year is None else args.year}, "
            f"dry_run={args.dry_run}) …"
        )
        result = migrate_class_subjects_to_offerings(
            db=db,
            academic_year_id=args.year,
            dry_run=args.dry_run,
        )
        print(f"  ✓ Migrated : {result.migrated}")
        print(f"  ↷ Skipped  : {result.skipped}")
        if result.errors:
            print(f"  ✗ Errors ({len(result.errors)}):")
            for err in result.errors:
                print(f"      {err}")
        if args.dry_run:
            print("\n[DRY RUN] No changes were committed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
