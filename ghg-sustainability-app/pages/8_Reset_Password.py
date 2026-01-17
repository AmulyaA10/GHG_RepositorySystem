"""
Reset Password Page
Allows users to reset their password using a token from email
"""
import streamlit as st
from core.db import get_db
from core.config import settings
from core.ui import load_custom_css, page_header, info_card, render_ecotrack_sidebar
from core.password_reset import validate_reset_token, reset_password
from core.auth import hash_password
import logging

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{settings.APP_NAME} - Reset Password",
    page_icon="🔑",
    layout="centered"
)

# Load custom CSS
load_custom_css()

# Render sidebar
render_ecotrack_sidebar()

def reset_password_page():
    """Render reset password page"""

    page_header(
        title="Reset Password",
        subtitle="Set your new password",
        icon="🔑"
    )

    # Get token from URL query parameters
    query_params = st.query_params
    token = query_params.get("token", None)

    if not token:
        st.error("❌ **Invalid Reset Link**")
        st.warning("No reset token provided. Please use the link from your email.")

        if st.button("Request New Reset Link"):
            st.switch_page("pages/7_Forgot_Password.py")

        return

    # Show success message if password was reset
    if st.session_state.get("password_reset_success"):
        st.success("✅ **Password Reset Successful!**")
        st.balloons()

        st.markdown("""
        Your password has been reset successfully. You can now log in with your new password.
        """)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Go to Login", use_container_width=True, type="primary"):
            del st.session_state.password_reset_success
            st.switch_page("pages/0_Login.py")

        return

    # Validate token
    db = next(get_db())
    try:
        reset_token = validate_reset_token(db, token)

        if not reset_token:
            st.error("❌ **Invalid or Expired Reset Link**")
            st.warning("""
            This reset link is either invalid or has expired. Reset links are valid for 24 hours and can only be used once.
            """)

            if st.button("Request New Reset Link"):
                st.switch_page("pages/7_Forgot_Password.py")

            return

        # Get user info for display
        from models import User
        user = db.query(User).filter(User.id == reset_token.user_id).first()

        if not user:
            st.error("❌ User not found")
            return

        # Show user info
        st.info(f"🔐 Resetting password for: **{user.username}** ({user.email})")

        st.markdown("<br>", unsafe_allow_html=True)

        # Password reset form
        with st.form("reset_password_form"):
            st.subheader("Enter New Password")

            new_password = st.text_input(
                "New Password",
                type="password",
                placeholder="Enter new password (min 8 characters)",
                help="Your new password must be at least 8 characters long"
            )

            confirm_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter new password"
            )

            submit = st.form_submit_button("Reset Password", use_container_width=True, type="primary")

            if submit:
                # Validation
                if not new_password or not confirm_password:
                    st.error("❌ Both fields are required")
                    return

                if new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                    return

                if len(new_password) < 8:
                    st.error("❌ Password must be at least 8 characters long")
                    return

                # Additional password strength checks
                if new_password.lower() == user.username.lower():
                    st.error("❌ Password cannot be the same as your username")
                    return

                if new_password.lower() in ['password', 'password123', '12345678', 'qwerty']:
                    st.error("❌ Password is too common. Please choose a stronger password")
                    return

                # Reset password
                with st.spinner("Resetting password..."):
                    new_password_hash = hash_password(new_password)
                    success, message = reset_password(db, token, new_password_hash)

                if success:
                    logger.info(f"Password reset successful for user: {user.username}")

                    # Add to audit log
                    from models import AuditLog
                    audit = AuditLog(
                        user_id=user.id,
                        action="PASSWORD_RESET_COMPLETED",
                        details=f"Password reset completed via email token",
                        ip_address=st.session_state.get("client_ip", "unknown")
                    )
                    db.add(audit)
                    db.commit()

                    st.session_state.password_reset_success = True
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
                    logger.error(f"Password reset failed: {message}")

        # Password requirements
        st.markdown("<br>", unsafe_allow_html=True)

        info_card(
            title="Password Requirements",
            content="""
            <strong>Your new password must:</strong><br>
            • Be at least 8 characters long<br>
            • Not be the same as your username<br>
            • Not be a commonly used password<br><br>
            <strong>Tips for a strong password:</strong><br>
            • Use a mix of uppercase and lowercase letters<br>
            • Include numbers and special characters<br>
            • Avoid personal information<br>
            • Use a unique password for this system
            """,
            icon="🔒",
            color="blue"
        )

        # Token expiration info
        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("ℹ️ About Reset Links"):
            expires_in = reset_token.expires_at - reset_token.created_at
            hours_remaining = int((reset_token.expires_at - st.session_state.get("current_time", reset_token.created_at)).total_seconds() / 3600)

            st.markdown(f"""
            ### Reset Link Information:
            - **Created:** {reset_token.created_at.strftime('%Y-%m-%d %H:%M:%S')}
            - **Expires:** {reset_token.expires_at.strftime('%Y-%m-%d %H:%M:%S')}
            - **Valid for:** {int(expires_in.total_seconds() / 3600)} hours
            - **Approximate time remaining:** ~{max(0, hours_remaining)} hours

            ### Security Features:
            - This link can only be used once
            - After resetting, you'll need to request a new link for future resets
            - All password reset actions are logged
            """)

    finally:
        db.close()

if __name__ == "__main__":
    # Store current time for expiration calculations
    from datetime import datetime
    if "current_time" not in st.session_state:
        st.session_state.current_time = datetime.utcnow()

    reset_password_page()
