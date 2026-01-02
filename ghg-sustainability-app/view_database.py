#!/usr/bin/env python3
"""
Database Viewer - Quick way to view database contents
"""
from core.db import get_db
from models import Project, User, Calculation, Ecoinvent
from sqlalchemy import func
import pandas as pd

def view_all_tables():
    """View summary of all tables"""
    db = next(get_db())

    try:
        print("\n" + "="*80)
        print("📊 GHG DATABASE OVERVIEW")
        print("="*80 + "\n")

        # Table counts
        print("📋 TABLE RECORD COUNTS:")
        print("-" * 40)
        tables = {
            'users': db.query(User).count(),
            'projects': db.query(Project).count(),
            'calculations': db.query(Calculation).count(),
            'ecoinvent': db.query(Ecoinvent).count(),
        }

        for table, count in tables.items():
            print(f"  {table:20s}: {count:,} records")

        print("\n")

    finally:
        db.close()

def view_users():
    """View all users"""
    db = next(get_db())

    try:
        print("👥 USERS:")
        print("-" * 80)
        users = db.query(User).all()

        data = []
        for u in users:
            data.append({
                'ID': u.id,
                'Username': u.username,
                'Email': u.email,
                'Full Name': u.full_name,
                'Role': u.role,
                'Active': '✓' if u.is_active else '✗'
            })

        if data:
            df = pd.DataFrame(data)
            print(df.to_string(index=False))
        else:
            print("  No users found")

        print("\n")

    finally:
        db.close()

def view_projects():
    """View all projects"""
    db = next(get_db())

    try:
        print("📁 PROJECTS:")
        print("-" * 120)
        projects = db.query(Project).order_by(Project.created_at.desc()).all()

        data = []
        for p in projects:
            data.append({
                'ID': p.id,
                'Project Name': p.project_name[:30],
                'Organization': p.organization_name[:25],
                'Year': p.reporting_year,
                'Status': p.status,
                'Scope 1': f"{p.total_scope1:.2f}",
                'Scope 2': f"{p.total_scope2:.2f}",
                'Scope 3': f"{p.total_scope3:.2f}",
                'Total': f"{p.total_emissions:.2f}"
            })

        if data:
            df = pd.DataFrame(data)
            print(df.to_string(index=False))
        else:
            print("  No projects found")

        print("\n")

    finally:
        db.close()

def view_project_details(project_id: int):
    """View detailed information for a specific project"""
    db = next(get_db())

    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            print(f"❌ Project {project_id} not found")
            return

        print("\n" + "="*80)
        print(f"📋 PROJECT DETAILS - {project.project_name}")
        print("="*80 + "\n")

        print(f"  ID:              {project.id}")
        print(f"  Name:            {project.project_name}")
        print(f"  Organization:    {project.organization_name}")
        print(f"  Reporting Year:  {project.reporting_year}")
        print(f"  Status:          {project.status}")
        print(f"  Created:         {project.created_at}")
        print(f"  Created By:      {project.created_by}")

        if project.description:
            print(f"  Description:     {project.description}")

        print(f"\n  📊 EMISSIONS SUMMARY:")
        print(f"     Scope 1:      {project.total_scope1:,.2f} tCO2e")
        print(f"     Scope 2:      {project.total_scope2:,.2f} tCO2e")
        print(f"     Scope 3:      {project.total_scope3:,.2f} tCO2e")
        print(f"     TOTAL:        {project.total_emissions:,.2f} tCO2e")

        # Get calculations
        calculations = db.query(Calculation).filter(
            Calculation.project_id == project_id
        ).order_by(Calculation.scope, Calculation.category).all()

        if calculations:
            print(f"\n  🧮 CALCULATIONS ({len(calculations)} total):")
            print("  " + "-" * 76)

            data = []
            for c in calculations:
                data.append({
                    'ID': c.id,
                    'Scope': c.scope,
                    'Category': c.category[:30],
                    'Activity': f"{c.activity_data:.2f}",
                    'EF': f"{c.emission_factor:.4f}",
                    'Emissions': f"{c.emissions_tco2e:.4f}"
                })

            df = pd.DataFrame(data)
            print("  " + df.to_string(index=False).replace('\n', '\n  '))

        print("\n")

    finally:
        db.close()

def view_emissions_summary():
    """View emissions summary by scope"""
    db = next(get_db())

    try:
        print("🌍 EMISSIONS SUMMARY (Approved & Locked Projects):")
        print("-" * 80)

        total_scope1 = db.query(func.sum(Project.total_scope1)).filter(
            Project.status.in_(["APPROVED", "LOCKED"])
        ).scalar() or 0.0

        total_scope2 = db.query(func.sum(Project.total_scope2)).filter(
            Project.status.in_(["APPROVED", "LOCKED"])
        ).scalar() or 0.0

        total_scope3 = db.query(func.sum(Project.total_scope3)).filter(
            Project.status.in_(["APPROVED", "LOCKED"])
        ).scalar() or 0.0

        total = total_scope1 + total_scope2 + total_scope3

        print(f"  Scope 1:  {total_scope1:>15,.2f} tCO2e  ({total_scope1/total*100 if total > 0 else 0:.1f}%)")
        print(f"  Scope 2:  {total_scope2:>15,.2f} tCO2e  ({total_scope2/total*100 if total > 0 else 0:.1f}%)")
        print(f"  Scope 3:  {total_scope3:>15,.2f} tCO2e  ({total_scope3/total*100 if total > 0 else 0:.1f}%)")
        print(f"  {'─'*60}")
        print(f"  TOTAL:    {total:>15,.2f} tCO2e")
        print("\n")

    finally:
        db.close()

def search_projects(search_term: str):
    """Search projects by name or organization"""
    db = next(get_db())

    try:
        from sqlalchemy import or_

        projects = db.query(Project).filter(
            or_(
                Project.project_name.ilike(f"%{search_term}%"),
                Project.organization_name.ilike(f"%{search_term}%")
            )
        ).all()

        print(f"\n🔍 SEARCH RESULTS for '{search_term}':")
        print("-" * 100)

        if projects:
            data = []
            for p in projects:
                data.append({
                    'ID': p.id,
                    'Project Name': p.project_name[:35],
                    'Organization': p.organization_name[:30],
                    'Year': p.reporting_year,
                    'Status': p.status,
                    'Total Emissions': f"{p.total_emissions:.2f}"
                })

            df = pd.DataFrame(data)
            print(df.to_string(index=False))
            print(f"\nFound {len(projects)} project(s)")
        else:
            print(f"  No projects found matching '{search_term}'")

        print("\n")

    finally:
        db.close()

def main():
    """Main menu"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "overview":
            view_all_tables()
            view_emissions_summary()

        elif command == "users":
            view_users()

        elif command == "projects":
            view_projects()

        elif command == "project" and len(sys.argv) > 2:
            project_id = int(sys.argv[2])
            view_project_details(project_id)

        elif command == "search" and len(sys.argv) > 2:
            search_term = sys.argv[2]
            search_projects(search_term)

        else:
            print_help()
    else:
        # Default: show everything
        view_all_tables()
        view_users()
        view_projects()
        view_emissions_summary()

def print_help():
    """Print usage instructions"""
    print("""
📖 DATABASE VIEWER USAGE:

python view_database.py                    # View all data
python view_database.py overview           # Quick overview
python view_database.py users              # View all users
python view_database.py projects           # View all projects
python view_database.py project <ID>       # View specific project details
python view_database.py search <term>      # Search projects

Examples:
  python view_database.py project 1
  python view_database.py search "ABC Corp"
""")

if __name__ == "__main__":
    main()
