#!/usr/bin/env python3
"""
Cleanup duplicate evidence files from database
"""
from core.db import get_db
from models import Evidence
from sqlalchemy import func
from core.storage import storage

def cleanup_duplicates():
    """Remove duplicate evidence entries, keeping only the oldest one"""
    db = next(get_db())

    try:
        # Find duplicates (same project_id, criteria_id, filename)
        duplicates = db.query(
            Evidence.project_id,
            Evidence.criteria_id,
            Evidence.filename,
            func.count(Evidence.id).label('count')
        ).group_by(
            Evidence.project_id,
            Evidence.criteria_id,
            Evidence.filename
        ).having(
            func.count(Evidence.id) > 1
        ).all()

        if not duplicates:
            print("✅ No duplicates found!")
            return

        print(f"Found {len(duplicates)} sets of duplicate files")

        total_deleted = 0

        for dup in duplicates:
            project_id, criteria_id, filename, count = dup
            print(f"\nProcessing: {filename} (Project: {project_id}, Criteria: {criteria_id}) - {count} copies")

            # Get all evidence records for this file (ordered by uploaded_at, oldest first)
            evidence_records = db.query(Evidence).filter(
                Evidence.project_id == project_id,
                Evidence.criteria_id == criteria_id,
                Evidence.filename == filename
            ).order_by(Evidence.uploaded_at.asc()).all()

            # Keep the first (oldest) record, delete the rest
            for i, record in enumerate(evidence_records):
                if i == 0:
                    print(f"  ✅ Keeping: ID {record.id} (uploaded: {record.uploaded_at})")
                else:
                    print(f"  🗑️  Deleting: ID {record.id} (uploaded: {record.uploaded_at})")

                    # Delete the physical file
                    try:
                        storage.delete_evidence_file(record.file_path)
                    except Exception as e:
                        print(f"     Warning: Could not delete file {record.file_path}: {e}")

                    # Delete database record
                    db.delete(record)
                    total_deleted += 1

        # Commit all deletions
        db.commit()
        print(f"\n✅ Cleanup complete! Deleted {total_deleted} duplicate records.")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧹 Starting evidence cleanup...")
    print("This will remove duplicate evidence files, keeping only the oldest copy of each file.\n")

    response = input("Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        cleanup_duplicates()
    else:
        print("Cancelled.")
