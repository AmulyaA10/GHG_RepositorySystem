"""
EcoTrack - GHG Sustainability Reporting System
Main Application
"""
import streamlit as st
from sqlalchemy import func

from core.config import settings
from core.ui import load_custom_css, metric_card, info_card, render_ecotrack_sidebar
from models import Project

st.set_page_config(
    page_title="EcoTrack",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_custom_css()

# Render EcoTrack sidebar
render_ecotrack_sidebar()

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

    # Check if user is logged in
    if not st.session_state.get("user"):
        # Welcome page for logged out users
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px;">
            <div style="display: inline-flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                <svg width="48" height="48" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M16 4C16 4 8 8 8 16C8 20 10 24 16 28C22 24 24 20 24 16C24 8 16 4 16 4Z"
                          stroke="#2563eb" stroke-width="2" fill="none"/>
                    <path d="M16 8C16 8 12 10 12 16C12 18 13 20 16 22C19 20 20 18 20 16C20 10 16 8 16 8Z"
                          fill="#2563eb" opacity="0.3"/>
                </svg>
                <span style="font-size: 36px; font-weight: 700; color: #2563eb;">EcoTrack</span>
            </div>
            <p style="font-size: 18px; color: #6b7280; margin-bottom: 40px;">
                GHG Sustainability Reporting System
            </p>
        </div>
        """, unsafe_allow_html=True)

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
                • ISO 14064-1 Compliant<br>
                • GHG Protocol Standards<br>
                • Ecoinvent emission factors<br>
                • Automated calculations<br>
                • Review & approval workflow<br>
                • Excel & PDF reports
                """,
                icon="✨",
                color="blue"
            )

        with col2:
            info_card(
                title="User Roles",
                content="""
                <strong>L1:</strong> Data Collection<br>
                <strong>L2:</strong> Emission Factors<br>
                <strong>L3:</strong> QA Review<br>
                <strong>L4:</strong> Dashboard & Approval
                """,
                icon="👥",
                color="green"
            )

        return

    # User is logged in - show dashboard
    user = st.session_state.user
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        padding: 16px 20px;
        border-radius: 12px;
        border: 1px solid #bfdbfe;
        margin-bottom: 24px;
    ">
        <span style="color: #1e40af; font-weight: 500;">
            👤 Welcome back, <strong>{user.full_name}</strong> ({user.role})
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Overview", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Get cached statistics
    stats = get_home_stats(settings.DATABASE_URL, st.session_state.user.id)

    # Overall statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Total Projects", str(stats['total_projects']), icon="📁")

    with col2:
        metric_card("My Projects", str(stats['my_projects']), icon="👤")

    with col3:
        metric_card("Pending", str(stats['pending']), icon="⏳")

    with col4:
        metric_card("Completed", str(stats['completed']), icon="✅")

    # Total emissions
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🌍 Total Emissions", unsafe_allow_html=True)
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
        metric_card("Total", f"{totals['total']:,.2f} tCO2e", icon="🌍")

    # Quick actions
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🚀 Quick Actions", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 Data Collection", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Data_Collection.py")

    with col2:
        if st.button("⚙️ Emission Factors", use_container_width=True, type="secondary"):
            st.switch_page("pages/2_Emission_Factors.py")

    with col3:
        if st.button("📊 Dashboard", use_container_width=True, type="secondary"):
            st.switch_page("pages/4_Dashboard.py")

if __name__ == "__main__":
    main()
