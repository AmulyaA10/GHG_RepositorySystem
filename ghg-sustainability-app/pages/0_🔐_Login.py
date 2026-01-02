"""
Login Page
"""
import streamlit as st
from core.db import get_db
from core.auth import authenticate_user
from core.config import settings
from core.ui import load_custom_css, page_header, info_card

st.set_page_config(
    page_title=f"{settings.APP_NAME} - Login",
    page_icon="🔐",
    layout="centered"
)

# Load custom CSS
load_custom_css()

# Add sidebar title and hide default "app" text
with st.sidebar:
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
            setTimeout(function() {
                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
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

def login_page():
    """Render login page"""
    page_header(
        title="Login",
        subtitle="Access the GHG Sustainability Reporting System",
        icon="🔐"
    )

    # Show logout confirmation if just logged out
    if st.session_state.get("just_logged_out"):
        st.success("✅ **Logged out successfully!** Please login again to continue.")
        del st.session_state.just_logged_out

    # Check if already logged in
    if st.session_state.get("user"):
        st.success(f"✅ Already logged in as {st.session_state.user.full_name} ({st.session_state.user.role})")
        st.info("Navigate to other pages using the sidebar")

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
        return

    # Login form
    with st.form("login_form"):
        st.subheader("Enter Credentials")

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
                return

            # Authenticate
            db = next(get_db())
            try:
                user = authenticate_user(db, username, password)

                if user:
                    # Store in session
                    st.session_state.user = user
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.session_state.role = user.role
                    st.session_state.full_name = user.full_name

                    st.success(f"✅ Login successful! Welcome {user.full_name}")
                    st.info(f"Role: {settings.ROLES[user.role]}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
            finally:
                db.close()

    # Info section
    st.markdown("<br>", unsafe_allow_html=True)

    info_card(
        title="Default Users (for development)",
        content="""
        <strong>L1 User:</strong> <code>user_l1</code> / <code>password123</code><br>
        <strong>L2 User:</strong> <code>user_l2</code> / <code>password123</code><br>
        <strong>L3 User:</strong> <code>user_l3</code> / <code>password123</code><br>
        <strong>L4 User:</strong> <code>user_l4</code> / <code>password123</code><br><br>
        <em>Note: Change default passwords in production</em>
        """,
        icon="👥",
        color="blue"
    )

if __name__ == "__main__":
    login_page()
