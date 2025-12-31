#!/usr/bin/env python3
"""
Create test data for L3 review
"""
from core.db import get_db
from models import Project, ProjectData, Calculation, Criteria, User
from datetime import datetime

def create_test_project():
    """Create a test project with calculations for L3 review"""
    db = next(get_db())

    try:
        # Get L1 user
        l1_user = db.query(User).filter(User.username == "user_l1").first()
        if not l1_user:
            print("❌ L1 user not found")
            return

        # Create project
        project = Project(
            project_name="Test Company 2024 Carbon Footprint",
            organization_name="Test Company Ltd",
            reporting_year=2024,
            description="Test project for reviewing in L3",
            status="PENDING_REVIEW",
            created_by=l1_user.id,
            created_by_email=l1_user.email,
            submitted_at=datetime.utcnow(),
            calculated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        print(f"✅ Created project: {project.project_name} (ID: {project.id})")

        # Get first 5 criteria
        criteria_list = db.query(Criteria).filter(Criteria.is_active == True).limit(5).all()

        total_scope1 = 0.0
        total_scope2 = 0.0
        total_scope3 = 0.0

        for i, criterion in enumerate(criteria_list):
            # Create project data
            activity_data = (i + 1) * 100.0  # 100, 200, 300, 400, 500
            project_data = ProjectData(
                project_id=project.id,
                criteria_id=criterion.id,
                activity_data=activity_data,
                unit=criterion.unit,
                notes=f"Test data for {criterion.category}",
                entered_by=l1_user.id,
                has_evidence=0
            )
            db.add(project_data)
            db.commit()
            db.refresh(project_data)

            # Create calculation
            emission_factor = 0.5  # Example emission factor
            gwp = 1.0
            emissions_kg = activity_data * emission_factor * gwp
            emissions_tco2e = emissions_kg / 1000

            calculation = Calculation(
                project_id=project.id,
                criteria_id=criterion.id,
                project_data_id=project_data.id,
                activity_data=activity_data,
                emission_factor=emission_factor,
                emission_factor_source="Test data - Ecoinvent ID: 1",
                gwp=gwp,
                unit_conversion=1.0,
                emissions_kg=emissions_kg,
                emissions_tco2e=emissions_tco2e,
                scope=criterion.scope,
                category=criterion.category,
                formula_used="activity_data × emission_factor × gwp",
                calculation_breakdown={
                    'formula': 'activity_data × emission_factor × gwp',
                    'calculation': f'{activity_data} × {emission_factor} × {gwp}',
                    'emissions_kg': emissions_kg,
                    'emissions_tco2e': emissions_tco2e
                },
                calculated_by=l1_user.id
            )
            db.add(calculation)

            # Add to totals
            if criterion.scope == "Scope 1":
                total_scope1 += emissions_tco2e
            elif criterion.scope == "Scope 2":
                total_scope2 += emissions_tco2e
            elif criterion.scope == "Scope 3":
                total_scope3 += emissions_tco2e

            print(f"  ✅ Added: {criterion.category} - {emissions_tco2e:.4f} tCO2e")

        # Update project totals
        project.total_scope1 = total_scope1
        project.total_scope2 = total_scope2
        project.total_scope3 = total_scope3
        project.total_emissions = total_scope1 + total_scope2 + total_scope3

        db.commit()

        print(f"\n📊 Project Totals:")
        print(f"  Scope 1: {total_scope1:.2f} tCO2e")
        print(f"  Scope 2: {total_scope2:.2f} tCO2e")
        print(f"  Scope 3: {total_scope3:.2f} tCO2e")
        print(f"  TOTAL: {project.total_emissions:.2f} tCO2e")
        print(f"\n✅ Project ready for L3 review!")
        print(f"   Status: {project.status}")
        print(f"   Login as L3 (user_l3/password123) to review this project")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Creating test data for L3 review...\n")
    create_test_project()
