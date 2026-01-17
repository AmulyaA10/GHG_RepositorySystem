"""
Change Password Page
Allows logged-in users to change their password
"""
import streamlit as st
from core.db import get_db
from core.auth import verify_password, hash_password, get_current_user
from core.config import settings
from core.ui import load_custom_css, page_header, info_card, render_ecotrack_sidebar
from models import User
import logging

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{settings.APP_NAME} - Change Password",
    page_icon="🔑",
    layout="centered"
)

# Load custom CSS
load_custom_css()

# Render sidebar
render_ecotrack_sidebar()

def change_password_page():
    """Render change password page"""

    # Check if user is logged in
    user = get_current_user()
    if not user:
        st.error("⛔ Please log in to access this page")
        st.info("Use the Login page from the sidebar")
        st.stop()
        return

    page_header(
        title="Change Password",
        subtitle=f"Update your password - {user.full_name}",
        icon="🔑"
    )

    # Show success message if password was just changed
    if st.session_state.get("password_changed"):
        st.success("✅ **Password changed successfully!**")
        del st.session_state.password_changed

    # Password change form
    with st.form("change_password_form"):
        st.subheader("Enter New Password")

        current_password = st.text_input(
            "Current Password",
            type="password",
            placeholder="Enter your current password"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Enter new password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            placeholder="Re-enter new password"
        )

        submit = st.form_submit_button("Change Password", use_container_width=True, type="primary")

        if submit:
            # Validation
            if not current_password or not new_password or not confirm_password:
                st.error("❌ All fields are required")
                return

            if new_password != confirm_password:
                st.error("❌ New passwords do not match")
                return

            if len(new_password) < 8:
                st.error("❌ Password must be at least 8 characters long")
                return

            if current_password == new_password:
                st.error("❌ New password must be different from current password")
                return

            # Verify current password
            db = next(get_db())
            try:
                db_user = db.query(User).filter(User.id == user.id).first()

                if not db_user:
                    st.error("❌ User not found")
                    return

                # Verify current password
                if not verify_password(current_password, db_user.password_hash):
                    st.error("❌ Current password is incorrect")
                    return

                # Update password
                db_user.password_hash = hash_password(new_password)
                db.commit()

                # Log the change
                logger.info(f"Password changed for user: {db_user.username}")

                # Update session
                st.session_state.password_changed = True
                st.success("✅ Password changed successfully!")
                st.balloons()

                # Add to audit log if needed
                from models import AuditLog
                audit = AuditLog(
                    user_id=user.id,
                    action="PASSWORD_CHANGED",
                    details=f"User {user.username} changed their password",
                    ip_address=st.session_state.get("client_ip", "unknown")
                )
                db.add(audit)
                db.commit()

                st.rerun()

            except Exception as e:
                db.rollback()
                logger.error(f"Error changing password: {e}")
                st.error(f"❌ Error changing password: {str(e)}")
            finally:
                db.close()

    # Password requirements info
    st.markdown("<br>", unsafe_allow_html=True)

    info_card(
        title="Password Requirements",
        content="""
        <strong>Your new password must:</strong><br>
        • Be at least 8 characters long<br>
        • Be different from your current password<br>
        • Not be a commonly used password<br><br>
        <strong>Tips for a strong password:</strong><br>
        • Use a mix of letters, numbers, and symbols<br>
        • Avoid personal information<br>
        • Use a unique password for this system
        """,
        icon="🔒",
        color="blue"
    )

if __name__ == "__main__":
    change_password_page()
