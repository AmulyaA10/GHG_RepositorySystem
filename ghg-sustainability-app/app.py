"""
GHG Sustainability Reporting System - Main Application
"""
import streamlit as st
from core.config import settings
from core.db import get_db
from core.ui import load_custom_css, page_header, metric_card, info_card
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

# Add sidebar title and hide default "app" text
with st.sidebar:
    # Custom title
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 1.5rem;
                    background: linear-gradient(135deg, #E8EFF6 0%, #F0F4F8 100%);
                    border-radius: 12px; border: 2px solid #1E40AF;">
            <h2 style="margin: 0; color: #0C1E2E; font-size: 1.25rem; font-weight: 700;">
                🌍 GHG Sustainability App
            </h2>
        </div>

        <script>
            // Hide the default "app" text
            setTimeout(function() {
                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
                    const firstDiv = sidebar.querySelector('div > div:first-child');
                    if (firstDiv && firstDiv.textContent.trim() === 'app') {
                        firstDiv.style.display = 'none';
                    }

                    // Alternative: remove all small text before navigation
                    const allDivs = sidebar.querySelectorAll('div');
                    allDivs.forEach(div => {
                        if (div.textContent.trim() === 'app' && div.children.length === 0) {
                            div.remove();
                        }
                    });
                }
            }, 100);
        </script>
        """,
        unsafe_allow_html=True
    )

# Cached query functions for home page dashboard
@st.cache_data(ttl=180)  # Cache for 3 minutes
def get_home_stats(db_url: str, user_id: int):
    """Get home page statistics - cached for 3 minutes"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        stats = {
            'total_projects': db.query(Project).count(),
            'my_projects': db.query(Project).filter(Project.created_by == user_id).count(),
            'pending': db.query(Project).filter(
                Project.status.in_(["DRAFT", "SUBMITTED", "UNDER_CALCULATION", "PENDING_REVIEW"])
            ).count(),
            'completed': db.query(Project).filter(
                Project.status.in_(["APPROVED", "LOCKED"])
            ).count()
        }
        return stats
    finally:
        db.close()

@st.cache_data(ttl=180)  # Cache for 3 minutes
def get_home_emissions(db_url: str):
    """Get total emissions for home page - cached for 3 minutes"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        totals = {
            'scope1': db.query(func.sum(Project.total_scope1)).filter(
                Project.status.in_(["APPROVED", "LOCKED"])
            ).scalar() or 0.0,
            'scope2': db.query(func.sum(Project.total_scope2)).filter(
                Project.status.in_(["APPROVED", "LOCKED"])
            ).scalar() or 0.0,
            'scope3': db.query(func.sum(Project.total_scope3)).filter(
                Project.status.in_(["APPROVED", "LOCKED"])
            ).scalar() or 0.0,
            'total': db.query(func.sum(Project.total_emissions)).filter(
                Project.status.in_(["APPROVED", "LOCKED"])
            ).scalar() or 0.0
        }
        return totals
    finally:
        db.close()

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

    # Get cached statistics
    stats = get_home_stats(settings.DATABASE_URL, st.session_state.user.id)

    # Overall statistics - using cached data
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Total Projects", str(stats['total_projects']), icon="📁")

    with col2:
        metric_card("My Projects", str(stats['my_projects']), icon="👤")

    with col3:
        metric_card("Pending", str(stats['pending']), icon="⏳")

    with col4:
        metric_card("Completed", str(stats['completed']), icon="✅")

    # Total emissions - using cached data
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 🌍 Total Emissions (All Projects)", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    totals = get_home_emissions(settings.DATABASE_URL)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Scope 1", f"{totals['scope1']:,.2f} tCO2e", icon="🏭")
    with col2:
        metric_card("Scope 2", f"{totals['scope2']:,.2f} tCO2e", icon="⚡")
    with col3:
        metric_card("Scope 3", f"{totals['scope3']:,.2f} tCO2e", icon="🚛")
    with col4:
        metric_card("Total Emissions", f"{totals['total']:,.2f} tCO2e", icon="🌍")

    db = next(get_db())

    try:

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
