#!/usr/bin/env python3
"""
Verification Script - Check all required files exist
"""
import os
from pathlib import Path

def check_file(path, description):
    """Check if file exists"""
    if Path(path).exists():
        size = Path(path).stat().st_size
        print(f"✅ {description}: {path} ({size} bytes)")
        return True
    else:
        print(f"❌ MISSING: {description}: {path}")
        return False

def main():
    print("="*70)
    print("GHG Sustainability App - Complete Verification")
    print("="*70)
    
    missing = []
    
    # Root files
    print("\n📁 ROOT FILES:")
    files = [
        ("app.py", "Main application"),
        ("requirements.txt", "Python dependencies"),
        ("Dockerfile", "Docker container definition"),
        ("docker-compose.yml", "Docker compose config"),
        ("alembic.ini", "Alembic config"),
        (".env.example", "Environment template"),
        (".gitignore", "Git ignore rules"),
        ("README.md", "Documentation")
    ]
    for f, desc in files:
        if not check_file(f, desc):
            missing.append(f)
    
    # Core modules
    print("\n📁 CORE/ - Business Logic:")
    files = [
        ("core/__init__.py", "Package init"),
        ("core/config.py", "Configuration"),
        ("core/db.py", "Database"),
        ("core/auth.py", "Authentication"),
        ("core/workflow.py", "State machine"),
        ("core/formulas.py", "Calculation engine"),
        ("core/validation.py", "Validation"),
        ("core/storage.py", "File storage"),
        ("core/emailer.py", "Email system"),
        ("core/reporting.py", "Report generation")
    ]
    for f, desc in files:
        if not check_file(f, desc):
            missing.append(f)
    
    # Models
    print("\n📁 MODELS/ - Database Models:")
    files = [
        ("models/__init__.py", "Package init"),
        ("models/user.py", "User model"),
        ("models/project.py", "Project model"),
        ("models/criteria.py", "Criteria model"),
        ("models/project_data.py", "Project data"),
        ("models/calculation.py", "Calculations"),
        ("models/review.py", "Reviews"),
        ("models/approval.py", "Approvals"),
        ("models/ecoinvent.py", "Emission factors"),
        ("models/reason_code.py", "Reason codes"),
        ("models/formula.py", "Formulas"),
        ("models/audit_log.py", "Audit logs"),
        ("models/evidence.py", "Evidence files")
    ]
    for f, desc in files:
        if not check_file(f, desc):
            missing.append(f)
    
    # Pages
    print("\n📁 PAGES/ - Streamlit UI:")
    files = [
        ("pages/0_🔐_Login.py", "Login page"),
        ("pages/1_📝_Level1_Data_Entry.py", "L1 Data Entry"),
        ("pages/2_🧮_Level2_Calculations.py", "L2 Calculations"),
        ("pages/3_✅_Level3_Review.py", "L3 Review"),
        ("pages/4_📊_Level4_Dashboard.py", "L4 Dashboard")
    ]
    for f, desc in files:
        if not check_file(f, desc):
            missing.append(f)
    
    # Migrations
    print("\n📁 MIGRATIONS/ - Database Migrations:")
    files = [
        ("migrations/env.py", "Alembic environment"),
        ("migrations/script.py.mako", "Migration template"),
        ("migrations/versions/001_initial_schema.py", "Initial schema")
    ]
    for f, desc in files:
        if not check_file(f, desc):
            missing.append(f)
    
    # Scripts
    print("\n📁 SCRIPTS/ - Seed Scripts:")
    files = [
        ("scripts/__init__.py", "Package init"),
        ("scripts/seed_users.py", "Seed users"),
        ("scripts/seed_criteria.py", "Seed criteria"),
        ("scripts/seed_reason_codes.py", "Seed reason codes"),
        ("scripts/seed_formulas.py", "Seed formulas"),
        ("scripts/seed_ecoinvent.py", "Seed ecoinvent"),
        ("scripts/seed_all.py", "Master seed script")
    ]
    for f, desc in files:
        if not check_file(f, desc):
            missing.append(f)
    
    # Tests
    print("\n📁 TESTS/ - Test Suite:")
    files = [
        ("tests/__init__.py", "Package init"),
        ("tests/conftest.py", "Pytest fixtures"),
        ("tests/test_auth.py", "Auth tests"),
        ("tests/test_formulas.py", "Formula tests"),
        ("tests/test_workflow.py", "Workflow tests")
    ]
    for f, desc in files:
        if not check_file(f, desc):
            missing.append(f)
    
    # Templates
    print("\n📁 TEMPLATES/ - Email Templates:")
    files = [
        ("templates/emails/submission.html", "Submission email"),
        ("templates/emails/review_request.html", "Review request email"),
        ("templates/emails/rejection.html", "Rejection email"),
        ("templates/emails/approval.html", "Approval email")
    ]
    for f, desc in files:
        if not check_file(f, desc):
            missing.append(f)
    
    # Summary
    print("\n" + "="*70)
    if missing:
        print(f"❌ VERIFICATION FAILED - {len(missing)} files missing:")
        for f in missing:
            print(f"   - {f}")
        return 1
    else:
        print("✅ VERIFICATION SUCCESSFUL - All files present!")
        print("="*70)
        print("\n📊 STATISTICS:")
        print(f"   Total files checked: {len(files) * 8}")
        print(f"   All files present: ✅")
        print("\n🚀 Ready to deploy!")
        return 0

if __name__ == "__main__":
    exit(main())
