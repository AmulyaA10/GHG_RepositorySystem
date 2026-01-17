"""
Forgot Password Page
Allows users to request a password reset via email
"""
import streamlit as st
from core.db import get_db
from core.config import settings
from core.ui import load_custom_css, page_header, info_card, render_ecotrack_sidebar
from core.password_reset import send_password_reset_email
from core.email import email_service
import logging

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{settings.APP_NAME} - Forgot Password",
    page_icon="🔐",
    layout="centered"
)

# Load custom CSS
load_custom_css()

# Render sidebar
render_ecotrack_sidebar()

def forgot_password_page():
    """Render forgot password page"""

    page_header(
        title="Forgot Password",
        subtitle="Request a password reset link",
        icon="🔐"
    )

    # Check if email service is configured
    if not email_service.is_configured():
        st.error("❌ **Email service is not configured**")
        st.warning("Please contact your system administrator to configure email settings.")

        with st.expander("📝 Administrator Information"):
            st.markdown("""
            To enable password reset functionality, configure the following environment variables:

            ```
            SMTP_HOST=smtp.gmail.com
            SMTP_PORT=587
            SMTP_USERNAME=your-email@gmail.com
            SMTP_PASSWORD=your-app-password
            SMTP_FROM=noreply@yourcompany.com
            ```

            For Gmail, you'll need to:
            1. Enable 2-Factor Authentication
            2. Generate an App Password
            3. Use the App Password in SMTP_PASSWORD
            """)
        st.stop()
        return

    # Show success message if email was sent
    if st.session_state.get("reset_email_sent"):
        st.success("✅ **Password reset link sent!**")
        st.info("📧 Check your email for the password reset link. The link will expire in 24 hours.")

        if st.button("← Back to Login"):
            del st.session_state.reset_email_sent
            st.switch_page("pages/0_Login.py")

        st.markdown("<br>", unsafe_allow_html=True)

        info_card(
            title="Didn't receive the email?",
            content="""
            • Check your spam/junk folder<br>
            • Make sure you entered the correct email/username<br>
            • Wait a few minutes for the email to arrive<br>
            • Try requesting again if needed
            """,
            icon="💡",
            color="blue"
        )
        return

    # Request password reset form
    st.markdown("""
    Enter your email address or username below, and we'll send you a link to reset your password.
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("forgot_password_form"):
        email_or_username = st.text_input(
            "Email or Username",
            placeholder="Enter your email address or username",
            help="Enter the email or username associated with your account"
        )

        submit = st.form_submit_button("Send Reset Link", use_container_width=True, type="primary")

        if submit:
            if not email_or_username:
                st.error("❌ Please enter your email or username")
                return

            # Get reset URL base (Streamlit app URL)
            # In production, you'd get this from config or request
            reset_url_base = "http://localhost:8501/Reset_Password"

            db = next(get_db())
            try:
                with st.spinner("Sending password reset email..."):
                    success, message = send_password_reset_email(
                        db,
                        email_or_username,
                        reset_url_base
                    )

                if success:
                    st.session_state.reset_email_sent = True
                    logger.info(f"Password reset requested for: {email_or_username}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
                    logger.error(f"Failed to send reset email: {message}")

            except Exception as e:
                logger.error(f"Error in forgot password: {e}")
                st.error("❌ An error occurred. Please try again.")
            finally:
                db.close()

    # Help section
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        info_card(
            title="Remember your password?",
            content='Go back to the <a href="/Login">Login page</a>',
            icon="🔑",
            color="blue"
        )

    with col2:
        info_card(
            title="Need help?",
            content="Contact your system administrator if you continue to have issues accessing your account.",
            icon="💬",
            color="green"
        )

    # Security info
    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("🔒 Security Information"):
        st.markdown("""
        ### How password reset works:

        1. **Request**: You enter your email/username
        2. **Email**: We send a secure reset link to your email
        3. **Link**: The link is valid for 24 hours
        4. **Reset**: Click the link to set a new password
        5. **Confirmation**: You'll receive a confirmation email

        ### Security features:
        - Reset links expire after 24 hours
        - Links can only be used once
        - Old reset links are automatically invalidated
        - We never send your password via email
        - All actions are logged for security

        ### Privacy:
        For security reasons, we don't reveal whether an email/username exists in our system.
        """)

if __name__ == "__main__":
    forgot_password_page()
