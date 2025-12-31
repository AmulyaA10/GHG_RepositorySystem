"""
Level 3 - Review Page
"""
import streamlit as st
from core.db import get_db
from core.auth import require_role
from core.config import settings
from core.ui import load_custom_css, page_header, sidebar_logout_button
from core.workflow import WorkflowManager
from core.emailer import send_workflow_email
from models import Project, ProjectData, Calculation, ReasonCode, Review
from sqlalchemy.orm import Session
from sqlalchemy import or_
import pandas as pd

st.set_page_config(
    page_title=f"{settings.APP_NAME} - Review",
    page_icon="✅",
    layout="wide"
)

# Load custom CSS
load_custom_css()

def check_auth():
    """Check if user is logged in and has L3 role"""
    if not st.session_state.get("user"):
        st.error("❌ Please login first")
        st.stop()

    # require_role handles the check and stops if unauthorized
    require_role(["L3"])

def review_summary(db: Session, project: Project):
    """Display project summary for review"""
    st.subheader(f"📊 Project Review - {project.project_name}")

    # Project info
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Project Details:**")
        st.write(f"- **Organization:** {project.organization_name}")
        st.write(f"- **Reporting Year:** {project.reporting_year}")
        st.write(f"- **Created By:** ID {project.created_by}")
        st.write(f"- **Status:** `{project.status}`")

    with col2:
        st.markdown("**Emissions Summary:**")
        st.metric("Scope 1", f"{project.total_scope1:.2f} tCO2e")
        st.metric("Scope 2", f"{project.total_scope2:.2f} tCO2e")
        st.metric("Scope 3", f"{project.total_scope3:.2f} tCO2e")

    with col3:
        st.markdown("**Totals:**")
        st.metric("**Total Emissions**", f"{project.total_emissions:.2f} tCO2e", delta=None)

        # Data completeness
        data_count = db.query(ProjectData).filter(ProjectData.project_id == project.id).count()
        calc_count = db.query(Calculation).filter(Calculation.project_id == project.id).count()
        st.write(f"- **Data Entries:** {data_count}")
        st.write(f"- **Calculations:** {calc_count}")

    st.markdown("---")

def detailed_breakdown(db: Session, project: Project):
    """Show detailed breakdown of calculations"""
    with st.expander("📋 Detailed Calculations Breakdown", expanded=False):
        calculations = db.query(Calculation).filter(
            Calculation.project_id == project.id
        ).order_by(Calculation.criteria_id).all()

        if calculations:
            # Convert to DataFrame
            data = []
            for calc in calculations:
                data.append({
                    "Criteria": calc.criteria.criteria_number,
                    "Category": calc.category,
                    "Scope": calc.scope,
                    "Activity Data": f"{calc.activity_data:.2f}",
                    "Unit": calc.project_data.unit,
                    "Emission Factor": f"{calc.emission_factor:.4f}",
                    "GWP": f"{calc.gwp:.2f}",
                    "Emissions (tCO2e)": f"{calc.emissions_tco2e:.4f}",
                    "Source": calc.emission_factor_source or "Manual"
                })

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Download CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Calculations CSV",
                data=csv,
                file_name=f"project_{project.id}_calculations.csv",
                mime="text/csv"
            )

        else:
            st.warning("No calculations found.")

def review_decision_form(db: Session, project: Project):
    """Form for review decision"""
    st.markdown("---")
    st.subheader("Review Decision")

    # Show approval/rejection confirmation if just submitted
    if st.session_state.get(f"l3_approved_{project.id}"):
        st.success("✅ **Project approved successfully!** It has been forwarded to Level 4 for final approval.")
        st.balloons()
        del st.session_state[f"l3_approved_{project.id}"]

    if st.session_state.get(f"l3_rejected_{project.id}"):
        st.warning("⚠️ **Project rejected.** It has been sent back for revision.")
        del st.session_state[f"l3_rejected_{project.id}"]

    # Get reason codes
    reason_codes = db.query(ReasonCode).filter(ReasonCode.is_active == True).all()

    with st.form("review_form"):
        decision = st.radio(
            "Decision",
            options=["Approve", "Reject"],
            horizontal=True,
            help="Approve to proceed to L4 approval, or Reject to send back for revision"
        )

        reason_code = None
        if decision == "Reject":
            reason_code_options = {
                f"{rc.code} - {rc.description}": rc.id
                for rc in reason_codes
            }

            selected_reason_str = st.selectbox(
                "Reason Code*",
                options=list(reason_code_options.keys()),
                help="Select the primary reason for rejection"
            )

            reason_code = reason_code_options[selected_reason_str]

        comments = st.text_area(
            "Comments*",
            placeholder="Enter your review comments...",
            help="Provide detailed feedback"
        )

        suggestions = st.text_area(
            "Suggestions",
            placeholder="Optional suggestions for improvement...",
            help="Provide actionable suggestions"
        )

        submit = st.form_submit_button("Submit Review Decision", type="primary", use_container_width=True)

        if submit:
            if not comments:
                st.error("Comments are required")
                return

            try:
                # Create review record
                review = Review(
                    project_id=project.id,
                    is_approved=(decision == "Approve"),
                    reason_code_id=reason_code if decision == "Reject" else None,
                    comments=comments,
                    suggestions=suggestions,
                    reviewed_by=st.session_state.user.id
                )

                db.add(review)

                # Transition project status
                new_status = "APPROVED" if decision == "Approve" else "REJECTED"

                can_transition, message = WorkflowManager.can_transition(
                    project.status,
                    new_status,
                    st.session_state.user.role
                )

                if can_transition:
                    WorkflowManager.transition(
                        db=db,
                        project=project,
                        new_status=new_status,
                        user_id=st.session_state.user.id,
                        user_role=st.session_state.user.role,
                        comments=comments,
                        reason_code=reason_code
                    )

                    # Send email notification
                    try:
                        send_workflow_email(
                            project=project,
                            transition=f"{project.status}_to_{new_status}",
                            comments=comments,
                            reason_code=reason_code
                        )
                    except Exception as e:
                        st.warning(f"Email notification failed: {e}")

                    db.commit()

                    # Store confirmation in session
                    if decision == "Approve":
                        st.session_state[f"l3_approved_{project.id}"] = True
                    else:
                        st.session_state[f"l3_rejected_{project.id}"] = True

                    st.rerun()

                else:
                    st.error(f"Cannot proceed: {message}")
                    db.rollback()

            except Exception as e:
                st.error(f"Error submitting review: {e}")
                db.rollback()

def review_history(db: Session, project: Project):
    """Show review history"""
    with st.expander("📜 Review History", expanded=False):
        reviews = db.query(Review).filter(
            Review.project_id == project.id
        ).order_by(Review.reviewed_at.desc()).all()

        if reviews:
            for review in reviews:
                status = "✅ APPROVED" if review.is_approved else "❌ REJECTED"
                st.markdown(f"**{status}** - {review.reviewed_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Reviewer:** User ID {review.reviewed_by}")

                if review.reason_code:
                    st.write(f"**Reason Code:** {review.reason_code.code} - {review.reason_code.description}")

                st.write(f"**Comments:** {review.comments}")

                if review.suggestions:
                    st.write(f"**Suggestions:** {review.suggestions}")

                st.markdown("---")
        else:
            st.info("No review history yet.")

def main():
    """Main function"""
    check_auth()

    st.title("✅ Level 3 - Quality Review")
    st.markdown("Review calculated emissions and approve or reject projects")
    st.markdown("---")

    db = next(get_db())

    try:
        # Sidebar - Project selection
        with st.sidebar:
            st.header("Review Queue")

            # Show pending reviews
            projects = db.query(Project).filter(
                or_(
                    Project.status == "PENDING_REVIEW",
                    Project.status == "APPROVED",
                    Project.status == "REJECTED"
                )
            ).order_by(Project.updated_at.desc()).all()

            if projects:
                # Categorize projects
                pending = [p for p in projects if p.status == "PENDING_REVIEW"]
                reviewed = [p for p in projects if p.status in ["APPROVED", "REJECTED"]]

                if pending:
                    st.markdown(f"**⏳ Pending Review ({len(pending)})**")
                    project_options = {
                        f"[PENDING] {p.project_name} - {p.organization_name}": p.id
                        for p in pending
                    }

                    for reviewed_proj in reviewed:
                        project_options[f"[{reviewed_proj.status}] {reviewed_proj.project_name}"] = reviewed_proj.id

                    selected_project_str = st.selectbox(
                        "Select Project",
                        options=list(project_options.keys())
                    )

                    selected_project_id = project_options[selected_project_str]
                    selected_project = db.query(Project).filter(Project.id == selected_project_id).first()

                    st.markdown("---")
                    st.markdown(f"**Status:** `{selected_project.status}`")
                    st.markdown(f"**Organization:** {selected_project.organization_name}")
                    st.markdown(f"**Year:** {selected_project.reporting_year}")

                    # Show quick stats
                    st.metric("Total Emissions", f"{selected_project.total_emissions:.2f} tCO2e")

                else:
                    st.info("No projects pending review.")
                    selected_project = None

            else:
                st.info("No projects in review queue.")
                selected_project = None

        # Logout button in sidebar
        sidebar_logout_button()

        # Main content
        if selected_project:
            review_summary(db, selected_project)
            detailed_breakdown(db, selected_project)
            review_history(db, selected_project)

            if selected_project.status == "PENDING_REVIEW":
                review_decision_form(db, selected_project)
            elif selected_project.status == "APPROVED":
                st.success("✅ This project has been approved and is awaiting L4 final approval")
            elif selected_project.status == "REJECTED":
                st.error("❌ This project was rejected and sent back for revision")

        else:
            st.info("Select a project from the sidebar to begin review.")

            # Show statistics
            st.subheader("📊 Review Statistics")

            col1, col2, col3 = st.columns(3)

            with col1:
                pending_count = db.query(Project).filter(Project.status == "PENDING_REVIEW").count()
                st.metric("Pending Reviews", pending_count)

            with col2:
                approved_count = db.query(Project).filter(Project.status == "APPROVED").count()
                st.metric("Approved", approved_count)

            with col3:
                rejected_count = db.query(Project).filter(Project.status == "REJECTED").count()
                st.metric("Rejected", rejected_count)

    finally:
        db.close()

if __name__ == "__main__":
    main()
