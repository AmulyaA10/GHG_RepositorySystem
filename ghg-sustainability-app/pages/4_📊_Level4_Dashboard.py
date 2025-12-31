"""
Level 4 - Dashboard & Approval Page
"""
import streamlit as st
from core.db import get_db
from core.auth import require_role
from core.config import settings
from core.ui import load_custom_css, sidebar_logout_button
from core.workflow import WorkflowManager
from core.reporting import report_generator
from core.emailer import send_workflow_email
from models import Project, Calculation, Approval
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pathlib import Path
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title=f"{settings.APP_NAME} - Dashboard",
    page_icon="📊",
    layout="wide"
)

# Load custom CSS
load_custom_css()

def check_auth():
    """Check if user is logged in and has L4 role"""
    if not st.session_state.get("user"):
        st.error("❌ Please login first")
        st.stop()

    # require_role handles the check and stops if unauthorized
    require_role(["L4"])

def dashboard_metrics(db: Session):
    """Display high-level metrics"""
    st.subheader("📊 GHG Reporting Dashboard")

    # Overall statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_projects = db.query(Project).count()
        st.metric("Total Projects", total_projects)

    with col2:
        approved_projects = db.query(Project).filter(
            or_(Project.status == "APPROVED", Project.status == "LOCKED")
        ).count()
        st.metric("Approved Projects", approved_projects)

    with col3:
        pending_approval = db.query(Project).filter(Project.status == "APPROVED").count()
        st.metric("Pending Final Approval", pending_approval)

    with col4:
        locked_projects = db.query(Project).filter(Project.status == "LOCKED").count()
        st.metric("Locked Projects", locked_projects)

    st.markdown("---")

    # Emissions aggregates
    st.subheader("🌍 Total Emissions Across All Projects")

    total_scope1 = db.query(func.sum(Project.total_scope1)).filter(
        or_(Project.status == "APPROVED", Project.status == "LOCKED")
    ).scalar() or 0.0

    total_scope2 = db.query(func.sum(Project.total_scope2)).filter(
        or_(Project.status == "APPROVED", Project.status == "LOCKED")
    ).scalar() or 0.0

    total_scope3 = db.query(func.sum(Project.total_scope3)).filter(
        or_(Project.status == "APPROVED", Project.status == "LOCKED")
    ).scalar() or 0.0

    total_emissions = total_scope1 + total_scope2 + total_scope3

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Scope 1", f"{total_scope1:,.2f} tCO2e")

    with col2:
        st.metric("Scope 2", f"{total_scope2:,.2f} tCO2e")

    with col3:
        st.metric("Scope 3", f"{total_scope3:,.2f} tCO2e")

    with col4:
        st.metric("**TOTAL**", f"{total_emissions:,.2f} tCO2e")

    st.markdown("---")

def projects_by_year(db: Session):
    """Show projects grouped by reporting year"""
    with st.expander("📅 Projects by Reporting Year", expanded=False):
        projects = db.query(Project).filter(
            or_(Project.status == "APPROVED", Project.status == "LOCKED")
        ).order_by(Project.reporting_year.desc()).all()

        if projects:
            # Group by year
            years = {}
            for p in projects:
                if p.reporting_year not in years:
                    years[p.reporting_year] = []
                years[p.reporting_year].append(p)

            for year, year_projects in years.items():
                st.markdown(f"### Year {year}")

                year_total = sum(p.total_emissions for p in year_projects)
                st.write(f"**Total Emissions:** {year_total:,.2f} tCO2e")
                st.write(f"**Projects:** {len(year_projects)}")

                # Show table
                data = []
                for p in year_projects:
                    data.append({
                        "Project": p.project_name,
                        "Organization": p.organization_name,
                        "Scope 1": f"{p.total_scope1:.2f}",
                        "Scope 2": f"{p.total_scope2:.2f}",
                        "Scope 3": f"{p.total_scope3:.2f}",
                        "Total": f"{p.total_emissions:.2f}",
                        "Status": p.status
                    })

                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.markdown("---")

        else:
            st.info("No approved projects yet.")

def project_approval_interface(db: Session, project: Project):
    """Interface for final approval and locking"""
    st.subheader(f"🔒 Final Approval - {project.project_name}")

    # Show lock confirmation if just locked
    if st.session_state.get(f"l4_locked_{project.id}"):
        st.success("✅ **Project locked successfully!** This project is now permanently archived and cannot be modified.")
        st.balloons()
        del st.session_state[f"l4_locked_{project.id}"]

    # Project summary
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Project Information:**")
        st.write(f"- **Organization:** {project.organization_name}")
        st.write(f"- **Reporting Year:** {project.reporting_year}")
        st.write(f"- **Status:** `{project.status}`")
        st.write(f"- **Created:** {project.created_at.strftime('%Y-%m-%d')}")

        if project.approved_at:
            st.write(f"- **L3 Approved:** {project.approved_at.strftime('%Y-%m-%d')}")

    with col2:
        st.markdown("**Emissions Summary:**")
        st.metric("Scope 1", f"{project.total_scope1:.2f} tCO2e")
        st.metric("Scope 2", f"{project.total_scope2:.2f} tCO2e")
        st.metric("Scope 3", f"{project.total_scope3:.2f} tCO2e")
        st.metric("**Total**", f"{project.total_emissions:.2f} tCO2e")

    st.markdown("---")

    # Calculations breakdown
    with st.expander("📋 View Calculations", expanded=False):
        calculations = db.query(Calculation).filter(
            Calculation.project_id == project.id
        ).order_by(Calculation.scope, Calculation.category).all()

        if calculations:
            data = []
            for calc in calculations:
                data.append({
                    "Scope": calc.scope,
                    "Category": calc.category,
                    "Activity Data": f"{calc.activity_data:.2f}",
                    "Emission Factor": f"{calc.emission_factor:.4f}",
                    "Emissions (tCO2e)": f"{calc.emissions_tco2e:.4f}"
                })

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Report export
    st.subheader("📄 Export Reports")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Download Excel Report", use_container_width=True):
            try:
                # Prepare calculations data
                calculations = db.query(Calculation).filter(
                    Calculation.project_id == project.id
                ).all()

                calc_dicts = []
                for calc in calculations:
                    calc_dicts.append({
                        'scope': calc.scope,
                        'category': calc.category,
                        'activity_data': calc.activity_data,
                        'emission_factor': calc.emission_factor,
                        'emissions_tco2e': calc.emissions_tco2e
                    })

                # Generate report
                output_dir = Path(settings.UPLOAD_DIR) / str(project.id)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"project_{project.id}_report.xlsx"

                success = report_generator.generate_excel_report(
                    project=project,
                    calculations=calc_dicts,
                    output_path=output_path
                )

                if success:
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download Excel File",
                            data=f,
                            file_name=f"GHG_Report_{project.id}_{project.reporting_year}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    st.success("✅ Excel report generated!")

            except Exception as e:
                st.error(f"Error generating Excel report: {e}")

    with col2:
        if st.button("📥 Download PDF Report", use_container_width=True):
            try:
                # Prepare calculations data
                calculations = db.query(Calculation).filter(
                    Calculation.project_id == project.id
                ).all()

                calc_dicts = []
                for calc in calculations:
                    calc_dicts.append({
                        'scope': calc.scope,
                        'category': calc.category,
                        'activity_data': calc.activity_data,
                        'emission_factor': calc.emission_factor,
                        'emissions_tco2e': calc.emissions_tco2e
                    })

                # Generate report
                output_dir = Path(settings.UPLOAD_DIR) / str(project.id)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"project_{project.id}_report.pdf"

                success = report_generator.generate_pdf_report(
                    project=project,
                    calculations=calc_dicts,
                    output_path=output_path
                )

                if success:
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download PDF File",
                            data=f,
                            file_name=f"GHG_Report_{project.id}_{project.reporting_year}.pdf",
                            mime="application/pdf"
                        )
                    st.success("✅ PDF report generated!")

            except Exception as e:
                st.error(f"Error generating PDF report: {e}")

    st.markdown("---")

    # Final approval and locking
    if project.status == "APPROVED":
        st.subheader("🔒 Lock Project")

        st.warning("""
        **⚠️ Warning: Locking is Permanent**

        Once locked, this project:
        - Cannot be edited or modified
        - Is permanently archived
        - Serves as official record

        Ensure all data is correct before proceeding.
        """)

        with st.form("lock_form"):
            comments = st.text_area(
                "Approval Comments*",
                placeholder="Enter final approval comments...",
                help="Document the final approval decision"
            )

            confirm = st.checkbox("I confirm that I have reviewed and approve this project for locking")

            submit = st.form_submit_button("🔒 Lock Project", type="primary")

            if submit:
                if not comments:
                    st.error("Comments are required")
                elif not confirm:
                    st.error("Please confirm before locking")
                else:
                    try:
                        # Create snapshot
                        calculations = db.query(Calculation).filter(
                            Calculation.project_id == project.id
                        ).all()

                        snapshot = {
                            "project_id": project.id,
                            "project_name": project.project_name,
                            "organization": project.organization_name,
                            "reporting_year": project.reporting_year,
                            "total_scope1": project.total_scope1,
                            "total_scope2": project.total_scope2,
                            "total_scope3": project.total_scope3,
                            "total_emissions": project.total_emissions,
                            "calculations": [
                                {
                                    "scope": c.scope,
                                    "category": c.category,
                                    "emissions_tco2e": c.emissions_tco2e
                                } for c in calculations
                            ],
                            "locked_at": datetime.utcnow().isoformat(),
                            "locked_by": st.session_state.user.id
                        }

                        # Create approval record
                        approval = Approval(
                            project_id=project.id,
                            comments=comments,
                            snapshot=snapshot,
                            approved_by=st.session_state.user.id
                        )

                        db.add(approval)

                        # Transition to LOCKED
                        can_transition, message = WorkflowManager.can_transition(
                            project.status,
                            "LOCKED",
                            st.session_state.user.role
                        )

                        if can_transition:
                            WorkflowManager.transition(
                                db=db,
                                project=project,
                                new_status="LOCKED",
                                user_id=st.session_state.user.id,
                                user_role=st.session_state.user.role,
                                comments=comments
                            )

                            # Send email notification
                            try:
                                send_workflow_email(
                                    project=project,
                                    transition="APPROVED_to_LOCKED",
                                    comments=comments
                                )
                            except Exception as e:
                                st.warning(f"Email notification failed: {e}")

                            db.commit()

                            # Store lock confirmation in session
                            st.session_state[f"l4_locked_{project.id}"] = True
                            st.rerun()

                        else:
                            st.error(f"Cannot lock: {message}")
                            db.rollback()

                    except Exception as e:
                        st.error(f"Error locking project: {e}")
                        db.rollback()

    elif project.status == "LOCKED":
        st.success("✅ This project is locked and archived")

        # Show approval details
        approval = db.query(Approval).filter(Approval.project_id == project.id).first()
        if approval:
            st.markdown("**Approval Details:**")
            st.write(f"- **Approved By:** User ID {approval.approved_by}")
            st.write(f"- **Approved At:** {approval.approved_at.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"- **Comments:** {approval.comments}")

def main():
    """Main function"""
    check_auth()

    st.title("📊 Level 4 - Dashboard & Approval")
    st.markdown("View aggregates, approve projects, and export reports")
    st.markdown("---")

    # Logout button in sidebar
    sidebar_logout_button()

    db = next(get_db())

    try:
        # Show dashboard
        dashboard_metrics(db)
        projects_by_year(db)

        st.markdown("---")

        # Project approval section
        st.header("🔒 Project Approval")

        # Get approved projects pending lock
        projects = db.query(Project).filter(
            or_(
                Project.status == "APPROVED",
                Project.status == "LOCKED"
            )
        ).order_by(Project.approved_at.desc()).all()

        if projects:
            project_options = {
                f"[{p.status}] {p.project_name} - {p.organization_name} ({p.reporting_year})": p.id
                for p in projects
            }

            selected_project_str = st.selectbox(
                "Select Project for Approval",
                options=list(project_options.keys())
            )

            selected_project_id = project_options[selected_project_str]
            selected_project = db.query(Project).filter(Project.id == selected_project_id).first()

            st.markdown("---")

            project_approval_interface(db, selected_project)

        else:
            st.info("No projects ready for final approval.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
