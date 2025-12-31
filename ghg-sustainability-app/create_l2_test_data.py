#!/usr/bin/env python3
"""
Create test data for L2 calculations
"""
from core.db import get_db
from models import Project, ProjectData, Criteria, User
from datetime import datetime

def create_l2_test_project():
    """Create a test project with data for L2 to calculate"""
    db = next(get_db())

    try:
        # Get L1 user
        l1_user = db.query(User).filter(User.username == "user_l1").first()
        if not l1_user:
            print("❌ L1 user not found")
            return

        # Create project
        project = Project(
            project_name="ABC Manufacturing 2024 Emissions",
            organization_name="ABC Manufacturing Inc",
            reporting_year=2024,
            description="Manufacturing facility carbon footprint for L2 calculations",
            status="SUBMITTED",
            created_by=l1_user.id,
            created_by_email=l1_user.email,
            submitted_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        print(f"✅ Created project: {project.project_name} (ID: {project.id})")

        # Get first 8 criteria for variety
        criteria_list = db.query(Criteria).filter(Criteria.is_active == True).limit(8).all()

        for i, criterion in enumerate(criteria_list):
            # Create project data with different values
            activity_data = (i + 1) * 250.0  # 250, 500, 750, 1000, 1250, 1500, 1750, 2000

            project_data = ProjectData(
                project_id=project.id,
                criteria_id=criterion.id,
                activity_data=activity_data,
                unit=criterion.unit,
                notes=f"Data for {criterion.category} - {activity_data} {criterion.unit}",
                entered_by=l1_user.id,
                has_evidence=0
            )
            db.add(project_data)

            print(f"  ✅ Added data: {criterion.category} - {activity_data} {criterion.unit}")

        db.commit()

        print(f"\n✅ Project ready for L2 calculations!")
        print(f"   Status: {project.status}")
        print(f"   Data entries: 8")
        print(f"\n👉 Login as L2 (user_l2/password123) to calculate emissions")
        print(f"   - Search Ecoinvent database for emission factors")
        print(f"   - Calculate emissions for each data entry")
        print(f"   - Submit for L3 review when complete")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Creating test data for L2 calculations...\n")
    create_l2_test_project()
