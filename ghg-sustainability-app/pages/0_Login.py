"""
Login Page
"""
import streamlit as st
from core.db import get_db
from core.auth import authenticate_user
from core.config import settings
from core.ui import load_custom_css, page_header, info_card, render_ecotrack_sidebar

st.set_page_config(
    page_title=f"{settings.APP_NAME} - Login",
    page_icon="🔐",
    layout="centered"
)

# Load custom CSS
load_custom_css()

# Render unified sidebar
render_ecotrack_sidebar()

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

    # Check if already logged in - redirect to home
    if st.session_state.get("user"):
        st.success(f"✅ Already logged in as {st.session_state.user.full_name} ({st.session_state.user.role})")
        st.info("Redirecting to home page...")

        # Add a small delay to show the message, then redirect
        import time
        time.sleep(1)
        st.switch_page("app.py")
        return

    # Login form
    with st.form("login_form"):
        st.subheader("Enter Credentials")

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        col1, col2 = st.columns([2, 1])
        with col1:
            submit = st.form_submit_button("Login", use_container_width=True)
        with col2:
            forgot_password = st.form_submit_button("Forgot Password?", use_container_width=True, type="secondary")

        if forgot_password:
            st.switch_page("pages/7_Forgot_Password.py")

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

                    # Redirect to home page after successful login
                    import time
                    time.sleep(1)
                    st.switch_page("app.py")
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
