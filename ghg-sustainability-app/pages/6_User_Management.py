"""
User Management Page (L4 Admin Only)
Allows L4 users to manage system users
"""
import streamlit as st
import pandas as pd
from core.db import get_db
from core.auth import require_role, hash_password
from core.config import settings
from core.ui import load_custom_css, page_header, render_ecotrack_sidebar
from models import User
import logging

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{settings.APP_NAME} - User Management",
    page_icon="👥",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Render sidebar
render_ecotrack_sidebar()

# Require L4 role
require_role(['L4'])

def user_management_page():
    """Render user management page"""

    page_header(
        title="User Management",
        subtitle="Manage system users and permissions",
        icon="👥"
    )

    # Tabs for different actions
    tab1, tab2, tab3 = st.tabs(["📋 All Users", "➕ Create User", "🔧 User Actions"])

    # ========== TAB 1: View All Users ==========
    with tab1:
        st.subheader("System Users")

        db = next(get_db())
        try:
            users = db.query(User).order_by(User.created_at.desc()).all()

            if not users:
                st.info("No users found in the system")
                return

            # Convert to dataframe for display
            user_data = []
            for user in users:
                user_data.append({
                    "ID": user.id,
                    "Username": user.username,
                    "Full Name": user.full_name,
                    "Email": user.email,
                    "Role": user.role,
                    "Active": "✅" if user.is_active else "❌",
                    "Created": user.created_at.strftime("%Y-%m-%d %H:%M")
                })

            df = pd.DataFrame(user_data)

            # Display with filters
            col1, col2 = st.columns([1, 1])
            with col1:
                role_filter = st.multiselect(
                    "Filter by Role",
                    options=["L1", "L2", "L3", "L4"],
                    default=["L1", "L2", "L3", "L4"]
                )
            with col2:
                status_filter = st.selectbox(
                    "Filter by Status",
                    options=["All", "Active Only", "Inactive Only"],
                    index=0
                )

            # Apply filters
            filtered_df = df[df["Role"].isin(role_filter)]
            if status_filter == "Active Only":
                filtered_df = filtered_df[filtered_df["Active"] == "✅"]
            elif status_filter == "Inactive Only":
                filtered_df = filtered_df[filtered_df["Active"] == "❌"]

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users", len(users))
            with col2:
                active_count = sum(1 for u in users if u.is_active)
                st.metric("Active Users", active_count)
            with col3:
                inactive_count = sum(1 for u in users if not u.is_active)
                st.metric("Inactive Users", inactive_count)
            with col4:
                l4_count = sum(1 for u in users if u.role == "L4")
                st.metric("Admins (L4)", l4_count)

        finally:
            db.close()

    # ========== TAB 2: Create New User ==========
    with tab2:
        st.subheader("Create New User")

        with st.form("create_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_username = st.text_input(
                    "Username *",
                    placeholder="e.g., john.doe",
                    help="Must be unique"
                )
                new_email = st.text_input(
                    "Email *",
                    placeholder="e.g., john.doe@company.com",
                    help="Must be unique"
                )
                new_full_name = st.text_input(
                    "Full Name *",
                    placeholder="e.g., John Doe"
                )

            with col2:
                new_role = st.selectbox(
                    "Role *",
                    options=["L1", "L2", "L3", "L4"],
                    format_func=lambda x: f"{x} - {settings.ROLES[x]}"
                )
                new_password = st.text_input(
                    "Initial Password *",
                    type="password",
                    placeholder="At least 8 characters",
                    help="User can change this after first login"
                )
                confirm_password = st.text_input(
                    "Confirm Password *",
                    type="password",
                    placeholder="Re-enter password"
                )

            new_is_active = st.checkbox("Active", value=True, help="Allow user to log in")

            submit_create = st.form_submit_button("Create User", use_container_width=True, type="primary")

            if submit_create:
                # Validation
                if not all([new_username, new_email, new_full_name, new_password, confirm_password]):
                    st.error("❌ All fields are required")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif len(new_password) < 8:
                    st.error("❌ Password must be at least 8 characters")
                else:
                    db = next(get_db())
                    try:
                        # Check if username or email already exists
                        existing_user = db.query(User).filter(
                            (User.username == new_username) | (User.email == new_email)
                        ).first()

                        if existing_user:
                            if existing_user.username == new_username:
                                st.error(f"❌ Username '{new_username}' already exists")
                            else:
                                st.error(f"❌ Email '{new_email}' already exists")
                        else:
                            # Create new user
                            new_user = User(
                                username=new_username,
                                email=new_email,
                                password_hash=hash_password(new_password),
                                full_name=new_full_name,
                                role=new_role,
                                is_active=new_is_active
                            )
                            db.add(new_user)
                            db.commit()

                            logger.info(f"New user created: {new_username} by {st.session_state.user.username}")

                            # Add to audit log
                            from models import AuditLog
                            audit = AuditLog(
                                user_id=st.session_state.user.id,
                                action="USER_CREATED",
                                details=f"Created user: {new_username} ({new_role})",
                                ip_address=st.session_state.get("client_ip", "unknown")
                            )
                            db.add(audit)
                            db.commit()

                            st.success(f"✅ User '{new_username}' created successfully!")
                            st.balloons()

                    except Exception as e:
                        db.rollback()
                        logger.error(f"Error creating user: {e}")
                        st.error(f"❌ Error creating user: {str(e)}")
                    finally:
                        db.close()

    # ========== TAB 3: User Actions ==========
    with tab3:
        st.subheader("User Actions")

        db = next(get_db())
        try:
            users = db.query(User).order_by(User.username).all()
            user_options = {f"{u.username} ({u.full_name})": u.id for u in users}

            selected_user_display = st.selectbox(
                "Select User",
                options=list(user_options.keys())
            )

            if selected_user_display:
                selected_user_id = user_options[selected_user_display]
                selected_user = db.query(User).filter(User.id == selected_user_id).first()

                if selected_user:
                    # Display user info
                    st.markdown("---")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"**Username:** {selected_user.username}")
                    with col2:
                        st.write(f"**Email:** {selected_user.email}")
                    with col3:
                        st.write(f"**Role:** {selected_user.role} - {settings.ROLES[selected_user.role]}")
                    with col4:
                        status_color = "green" if selected_user.is_active else "red"
                        st.markdown(f"**Status:** :{status_color}[{'Active' if selected_user.is_active else 'Inactive'}]")

                    st.markdown("---")

                    # Action buttons
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button(
                            "🔄 Toggle Active Status",
                            use_container_width=True,
                            help=f"{'Deactivate' if selected_user.is_active else 'Activate'} this user"
                        ):
                            # Prevent deactivating yourself
                            if selected_user.id == st.session_state.user.id:
                                st.error("❌ You cannot deactivate your own account")
                            else:
                                selected_user.is_active = not selected_user.is_active
                                action_text = "activated" if selected_user.is_active else "deactivated"

                                # Add to audit log
                                from models import AuditLog
                                audit = AuditLog(
                                    user_id=st.session_state.user.id,
                                    action="USER_STATUS_CHANGED",
                                    details=f"{action_text.capitalize()} user: {selected_user.username}",
                                    ip_address=st.session_state.get("client_ip", "unknown")
                                )
                                db.add(audit)
                                db.commit()

                                logger.info(f"User {selected_user.username} {action_text} by {st.session_state.user.username}")
                                st.success(f"✅ User {action_text} successfully!")
                                st.rerun()

                    with col2:
                        with st.expander("🔐 Reset Password"):
                            with st.form(f"reset_password_{selected_user.id}"):
                                new_pwd = st.text_input("New Password", type="password", key=f"new_pwd_{selected_user.id}")
                                confirm_pwd = st.text_input("Confirm Password", type="password", key=f"confirm_pwd_{selected_user.id}")

                                if st.form_submit_button("Reset Password"):
                                    if not new_pwd or not confirm_pwd:
                                        st.error("❌ Both fields are required")
                                    elif new_pwd != confirm_pwd:
                                        st.error("❌ Passwords do not match")
                                    elif len(new_pwd) < 8:
                                        st.error("❌ Password must be at least 8 characters")
                                    else:
                                        selected_user.password_hash = hash_password(new_pwd)

                                        # Add to audit log
                                        from models import AuditLog
                                        audit = AuditLog(
                                            user_id=st.session_state.user.id,
                                            action="PASSWORD_RESET",
                                            details=f"Reset password for user: {selected_user.username}",
                                            ip_address=st.session_state.get("client_ip", "unknown")
                                        )
                                        db.add(audit)
                                        db.commit()

                                        logger.info(f"Password reset for {selected_user.username} by {st.session_state.user.username}")
                                        st.success("✅ Password reset successfully!")
                                        st.info("📧 Notify the user about the password change")

                    with col3:
                        with st.expander("✏️ Edit Role"):
                            with st.form(f"change_role_{selected_user.id}"):
                                new_role = st.selectbox(
                                    "New Role",
                                    options=["L1", "L2", "L3", "L4"],
                                    index=["L1", "L2", "L3", "L4"].index(selected_user.role),
                                    format_func=lambda x: f"{x} - {settings.ROLES[x]}",
                                    key=f"role_{selected_user.id}"
                                )

                                if st.form_submit_button("Update Role"):
                                    # Prevent changing your own role
                                    if selected_user.id == st.session_state.user.id:
                                        st.error("❌ You cannot change your own role")
                                    elif new_role != selected_user.role:
                                        old_role = selected_user.role
                                        selected_user.role = new_role

                                        # Add to audit log
                                        from models import AuditLog
                                        audit = AuditLog(
                                            user_id=st.session_state.user.id,
                                            action="USER_ROLE_CHANGED",
                                            details=f"Changed role for {selected_user.username} from {old_role} to {new_role}",
                                            ip_address=st.session_state.get("client_ip", "unknown")
                                        )
                                        db.add(audit)
                                        db.commit()

                                        logger.info(f"Role changed for {selected_user.username} from {old_role} to {new_role} by {st.session_state.user.username}")
                                        st.success(f"✅ Role updated from {old_role} to {new_role}")
                                        st.rerun()
                                    else:
                                        st.info("ℹ️ Role is already set to this value")

        finally:
            db.close()

if __name__ == "__main__":
    user_management_page()
