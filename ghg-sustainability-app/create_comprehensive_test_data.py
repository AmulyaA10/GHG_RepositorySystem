#!/usr/bin/env python3
"""
Create comprehensive test data for all workflow stages
"""
from core.db import get_db
from models import Project, ProjectData, Calculation, Criteria, User
from datetime import datetime, timedelta

def create_comprehensive_test_data():
    """Create projects in each workflow stage"""
    db = next(get_db())

    try:
        # Get users
        l1_user = db.query(User).filter(User.username == "user_l1").first()
        l2_user = db.query(User).filter(User.username == "user_l2").first()
        l3_user = db.query(User).filter(User.username == "user_l3").first()
        l4_user = db.query(User).filter(User.username == "user_l4").first()

        if not all([l1_user, l2_user, l3_user, l4_user]):
            print("❌ Required users not found")
            return

        # Get criteria
        criteria_list = db.query(Criteria).filter(Criteria.is_active == True).limit(5).all()

        if not criteria_list:
            print("❌ No criteria found. Run seed_criteria.py first")
            return

        print("🧪 Creating comprehensive test data...\n")

        # 1. DRAFT project (for L1 testing)
        draft_project = Project(
            project_name="TechCorp 2024 - DRAFT",
            organization_name="TechCorp Industries",
            reporting_year=2024,
            description="Draft project for L1 data entry testing",
            status="DRAFT",
            created_by=l1_user.id,
            created_by_email=l1_user.email,
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        db.add(draft_project)
        db.commit()
        db.refresh(draft_project)

        # Add partial data to draft
        for i, criterion in enumerate(criteria_list[:2]):
            project_data = ProjectData(
                project_id=draft_project.id,
                criteria_id=criterion.id,
                activity_data=float((i + 1) * 100),
                unit=criterion.unit,
                notes=f"Draft data for {criterion.category}",
                entered_by=l1_user.id
            )
            db.add(project_data)

        db.commit()
        print(f"✅ Created DRAFT project: {draft_project.project_name} (ID: {draft_project.id})")

        # 2. SUBMITTED project (for L2 to pick up)
        submitted_project = Project(
            project_name="GreenEnergy Solutions 2024",
            organization_name="GreenEnergy Solutions Ltd",
            reporting_year=2024,
            description="Complete project submitted for calculations",
            status="SUBMITTED",
            created_by=l1_user.id,
            created_by_email=l1_user.email,
            created_at=datetime.utcnow() - timedelta(days=4),
            submitted_at=datetime.utcnow() - timedelta(days=3)
        )
        db.add(submitted_project)
        db.commit()
        db.refresh(submitted_project)

        # Add complete data
        for i, criterion in enumerate(criteria_list):
            project_data = ProjectData(
                project_id=submitted_project.id,
                criteria_id=criterion.id,
                activity_data=float((i + 1) * 250),
                unit=criterion.unit,
                notes=f"Activity data for {criterion.category}",
                entered_by=l1_user.id,
                has_evidence=0
            )
            db.add(project_data)

        db.commit()
        print(f"✅ Created SUBMITTED project: {submitted_project.project_name} (ID: {submitted_project.id})")

        # 3. UNDER_CALCULATION project (for L2 testing - with partial calculations)
        calc_project = Project(
            project_name="Manufacturing Co 2024",
            organization_name="Manufacturing Co Ltd",
            reporting_year=2024,
            description="Project with partial calculations",
            status="UNDER_CALCULATION",
            created_by=l1_user.id,
            created_by_email=l1_user.email,
            created_at=datetime.utcnow() - timedelta(days=3),
            submitted_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(calc_project)
        db.commit()
        db.refresh(calc_project)

        # Add data and some calculations
        for i, criterion in enumerate(criteria_list):
            project_data = ProjectData(
                project_id=calc_project.id,
                criteria_id=criterion.id,
                activity_data=float((i + 1) * 300),
                unit=criterion.unit,
                notes=f"Data for {criterion.category}",
                entered_by=l1_user.id
            )
            db.add(project_data)
            db.commit()
            db.refresh(project_data)

            # Add calculation for first 2 items only
            if i < 2:
                calculation = Calculation(
                    project_id=calc_project.id,
                    criteria_id=criterion.id,
                    project_data_id=project_data.id,
                    activity_data=project_data.activity_data,
                    emission_factor=0.5,
                    emission_factor_source="Test Factor",
                    gwp=1.0,
                    unit_conversion=1.0,
                    emissions_kg=(project_data.activity_data * 0.5),
                    emissions_tco2e=(project_data.activity_data * 0.5) / 1000,
                    scope=criterion.scope,
                    category=criterion.category,
                    formula_used="Activity Data × EF × GWP × UC",
                    calculated_by=l2_user.id
                )
                db.add(calculation)

        db.commit()

        # Update totals
        calc_project.total_scope1 = 0.15
        calc_project.total_scope2 = 0.30
        calc_project.total_scope3 = 0.0
        calc_project.total_emissions = 0.45
        db.commit()

        print(f"✅ Created UNDER_CALCULATION project: {calc_project.project_name} (ID: {calc_project.id})")

        # 4. PENDING_REVIEW project (for L3 testing)
        review_project = Project(
            project_name="RetailChain 2024 Emissions",
            organization_name="RetailChain Stores Inc",
            reporting_year=2024,
            description="Complete project ready for L3 review",
            status="PENDING_REVIEW",
            created_by=l1_user.id,
            created_by_email=l1_user.email,
            created_at=datetime.utcnow() - timedelta(days=6),
            submitted_at=datetime.utcnow() - timedelta(days=5),
            calculated_at=datetime.utcnow() - timedelta(days=4)
        )
        db.add(review_project)
        db.commit()
        db.refresh(review_project)

        # Add complete data and calculations
        total_scope1 = 0.0
        total_scope2 = 0.0
        total_scope3 = 0.0

        for i, criterion in enumerate(criteria_list):
            project_data = ProjectData(
                project_id=review_project.id,
                criteria_id=criterion.id,
                activity_data=float((i + 1) * 500),
                unit=criterion.unit,
                notes=f"Complete data for {criterion.category}",
                entered_by=l1_user.id,
                has_evidence=1
            )
            db.add(project_data)
            db.commit()
            db.refresh(project_data)

            # Calculate emissions
            emissions_tco2e = (project_data.activity_data * 0.8) / 1000

            calculation = Calculation(
                project_id=review_project.id,
                criteria_id=criterion.id,
                project_data_id=project_data.id,
                activity_data=project_data.activity_data,
                emission_factor=0.8,
                emission_factor_source="Ecoinvent Database",
                gwp=1.0,
                unit_conversion=1.0,
                emissions_kg=(project_data.activity_data * 0.8),
                emissions_tco2e=emissions_tco2e,
                scope=criterion.scope,
                category=criterion.category,
                formula_used="Activity Data × EF × GWP × UC",
                calculated_by=l2_user.id
            )
            db.add(calculation)

            # Aggregate by scope
            if criterion.scope == "Scope 1":
                total_scope1 += emissions_tco2e
            elif criterion.scope == "Scope 2":
                total_scope2 += emissions_tco2e
            elif criterion.scope == "Scope 3":
                total_scope3 += emissions_tco2e

        db.commit()

        # Update totals
        review_project.total_scope1 = total_scope1
        review_project.total_scope2 = total_scope2
        review_project.total_scope3 = total_scope3
        review_project.total_emissions = total_scope1 + total_scope2 + total_scope3
        db.commit()

        print(f"✅ Created PENDING_REVIEW project: {review_project.project_name} (ID: {review_project.id})")
        print(f"   Total Emissions: {review_project.total_emissions:.2f} tCO2e")

        # 5. APPROVED project (for L4 testing)
        approved_project = Project(
            project_name="FinanceCorp 2024 Footprint",
            organization_name="FinanceCorp Banking Group",
            reporting_year=2024,
            description="Approved project ready for L4 final locking",
            status="APPROVED",
            created_by=l1_user.id,
            created_by_email=l1_user.email,
            created_at=datetime.utcnow() - timedelta(days=10),
            submitted_at=datetime.utcnow() - timedelta(days=9),
            calculated_at=datetime.utcnow() - timedelta(days=8),
            reviewed_at=datetime.utcnow() - timedelta(days=7),
            approved_at=datetime.utcnow() - timedelta(days=7)
        )
        db.add(approved_project)
        db.commit()
        db.refresh(approved_project)

        # Add complete data and calculations
        total_scope1 = 0.0
        total_scope2 = 0.0
        total_scope3 = 0.0

        for i, criterion in enumerate(criteria_list):
            project_data = ProjectData(
                project_id=approved_project.id,
                criteria_id=criterion.id,
                activity_data=float((i + 1) * 750),
                unit=criterion.unit,
                notes=f"Verified data for {criterion.category}",
                entered_by=l1_user.id,
                has_evidence=2
            )
            db.add(project_data)
            db.commit()
            db.refresh(project_data)

            # Calculate emissions
            emissions_tco2e = (project_data.activity_data * 1.2) / 1000

            calculation = Calculation(
                project_id=approved_project.id,
                criteria_id=criterion.id,
                project_data_id=project_data.id,
                activity_data=project_data.activity_data,
                emission_factor=1.2,
                emission_factor_source="Ecoinvent Database v3.8",
                gwp=1.0,
                unit_conversion=1.0,
                emissions_kg=(project_data.activity_data * 1.2),
                emissions_tco2e=emissions_tco2e,
                scope=criterion.scope,
                category=criterion.category,
                formula_used="Activity Data × EF × GWP × UC",
                calculated_by=l2_user.id
            )
            db.add(calculation)

            # Aggregate by scope
            if criterion.scope == "Scope 1":
                total_scope1 += emissions_tco2e
            elif criterion.scope == "Scope 2":
                total_scope2 += emissions_tco2e
            elif criterion.scope == "Scope 3":
                total_scope3 += emissions_tco2e

        db.commit()

        # Update totals
        approved_project.total_scope1 = total_scope1
        approved_project.total_scope2 = total_scope2
        approved_project.total_scope3 = total_scope3
        approved_project.total_emissions = total_scope1 + total_scope2 + total_scope3
        db.commit()

        print(f"✅ Created APPROVED project: {approved_project.project_name} (ID: {approved_project.id})")
        print(f"   Total Emissions: {approved_project.total_emissions:.2f} tCO2e")

        print("\n" + "="*60)
        print("✅ COMPREHENSIVE TEST DATA CREATED SUCCESSFULLY!")
        print("="*60)
        print("\nProjects by Status:")
        print("  - DRAFT: 1 project (for L1 testing)")
        print("  - SUBMITTED: 1 project (for L2 to start)")
        print("  - UNDER_CALCULATION: 1 project (for L2 testing)")
        print("  - PENDING_REVIEW: 1 project (for L3 testing)")
        print("  - APPROVED: 1 project (for L4 testing)")
        print("\n👉 You can now test the complete workflow:")
        print("   1. Login as user_l1 to test data entry")
        print("   2. Login as user_l2 to test calculations")
        print("   3. Login as user_l3 to test reviews")
        print("   4. Login as user_l4 to test final approval & locking")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_comprehensive_test_data()
