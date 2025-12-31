"""
GHG Sustainability Reporting System - Main Application
"""
import streamlit as st
from core.config import settings
from core.db import get_db
from core.ui import load_custom_css, page_header, metric_card, info_card, empty_state
from models import Project
from sqlalchemy import func

st.set_page_config(
    page_title=settings.APP_NAME,
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_custom_css()

def main():
    """Main application entry point"""
    page_header(
        title="GHG Sustainability Reporting System",
        subtitle="ISO 14064-1 Compliant Emissions Calculation & Reporting",
        icon="🌍"
    )

    # Check if user is logged in
    if not st.session_state.get("user"):
        info_card(
            title="Please Login",
            content="Use the Login page from the sidebar to access the system",
            icon="🔐",
            color="blue"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            info_card(
                title="System Features",
                content="""
                • 4-level role-based workflow<br>
                • 23 GHG Protocol categories<br>
                • Ecoinvent emission factors database<br>
                • Automated calculations<br>
                • Review & approval workflow<br>
                • Excel & PDF report generation<br>
                • Complete audit trail
                """,
                icon="✨",
                color="blue"
            )

        with col2:
            info_card(
                title="User Roles",
                content="""
                <strong>L1:</strong> Data Entry Specialist<br>
                <strong>L2:</strong> Calculation Specialist<br>
                <strong>L3:</strong> QA Reviewer<br>
                <strong>L4:</strong> Approver/Manager
                """,
                icon="👥",
                color="green"
            )

        return

    # User is logged in - show dashboard
    st.success(f"✅ Logged in as: **{st.session_state.user.full_name}** ({st.session_state.user.role})")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Quick Overview", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    db = next(get_db())

    try:
        # Overall statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_projects = db.query(Project).count()
            metric_card("Total Projects", str(total_projects), icon="📁")

        with col2:
            my_projects = db.query(Project).filter(
                Project.created_by == st.session_state.user.id
            ).count()
            metric_card("My Projects", str(my_projects), icon="👤")

        with col3:
            pending_count = db.query(Project).filter(
                Project.status.in_(["DRAFT", "SUBMITTED", "UNDER_CALCULATION", "PENDING_REVIEW"])
            ).count()
            metric_card("Pending", str(pending_count), icon="⏳")

        with col4:
            completed_count = db.query(Project).filter(
                Project.status.in_(["APPROVED", "LOCKED"])
            ).count()
            metric_card("Completed", str(completed_count), icon="✅")

        # Total emissions
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### 🌍 Total Emissions (All Projects)", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        total_emissions = db.query(func.sum(Project.total_emissions)).filter(
            Project.status.in_(["APPROVED", "LOCKED"])
        ).scalar() or 0.0

        total_scope1 = db.query(func.sum(Project.total_scope1)).filter(
            Project.status.in_(["APPROVED", "LOCKED"])
        ).scalar() or 0.0

        total_scope2 = db.query(func.sum(Project.total_scope2)).filter(
            Project.status.in_(["APPROVED", "LOCKED"])
        ).scalar() or 0.0

        total_scope3 = db.query(func.sum(Project.total_scope3)).filter(
            Project.status.in_(["APPROVED", "LOCKED"])
        ).scalar() or 0.0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            metric_card("Scope 1", f"{total_scope1:,.2f} tCO2e", icon="🏭")
        with col2:
            metric_card("Scope 2", f"{total_scope2:,.2f} tCO2e", icon="⚡")
        with col3:
            metric_card("Scope 3", f"{total_scope3:,.2f} tCO2e", icon="🚛")
        with col4:
            metric_card("Total Emissions", f"{total_emissions:,.2f} tCO2e", icon="🌍")

        # Navigation instructions
        st.markdown("<br><br>", unsafe_allow_html=True)

        info_card(
            title="Navigation",
            content="Use the sidebar to navigate to your role-specific pages",
            icon="👈",
            color="blue"
        )

        # Role-specific quick links
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🚀 Quick Actions", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.user.role == "L1":
            info_card(
                title="Level 1 - Data Entry",
                content="Create projects and enter activity data for GHG emissions calculations",
                icon="📝",
                color="blue"
            )
        elif st.session_state.user.role == "L2":
            info_card(
                title="Level 2 - Calculations",
                content="Perform emission calculations using Ecoinvent database factors",
                icon="🧮",
                color="green"
            )
        elif st.session_state.user.role == "L3":
            info_card(
                title="Level 3 - Quality Review",
                content="Review calculated emissions and approve or reject projects",
                icon="✅",
                color="yellow"
            )
        elif st.session_state.user.role == "L4":
            info_card(
                title="Level 4 - Dashboard & Approval",
                content="View aggregated metrics, export reports, and lock projects",
                icon="📊",
                color="blue"
            )

    finally:
        db.close()

if __name__ == "__main__":
    main()
