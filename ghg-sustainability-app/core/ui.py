"""
Modern UI Components and Utilities
"""
import streamlit as st
from pathlib import Path
from core.auth import logout

def load_custom_css():
    """Load custom CSS styling"""
    css_file = Path(__file__).parent.parent / "assets" / "style.css"

    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def status_badge(status: str) -> str:
    """
    Generate HTML for a status badge

    Args:
        status: Project status

    Returns:
        str: HTML string for status badge
    """
    status_classes = {
        "DRAFT": "status-badge status-draft",
        "SUBMITTED": "status-badge status-submitted",
        "UNDER_CALCULATION": "status-badge status-submitted",
        "PENDING_REVIEW": "status-badge status-submitted",
        "APPROVED": "status-badge status-approved",
        "REJECTED": "status-badge status-rejected",
        "LOCKED": "status-badge status-locked"
    }

    status_icons = {
        "DRAFT": "📝",
        "SUBMITTED": "📤",
        "UNDER_CALCULATION": "🧮",
        "PENDING_REVIEW": "⏳",
        "APPROVED": "✅",
        "REJECTED": "❌",
        "LOCKED": "🔒"
    }

    css_class = status_classes.get(status, "status-badge")
    icon = status_icons.get(status, "")

    return f'<span class="{css_class}">{icon} {status}</span>'

def metric_card(label: str, value: str, delta: str = None, icon: str = "📊"):
    """
    Display a modern metric card

    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta/change value
        icon: Optional emoji icon
    """
    delta_html = f'<div style="color: #10b981; font-size: 0.875rem; margin-top: 0.5rem;">↗ {delta}</div>' if delta else ''

    html = f"""
    <div style="
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #bae6fd;
        text-align: center;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="
            font-size: 0.875rem;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        ">{label}</div>
        <div style="
            font-size: 2rem;
            font-weight: 700;
            color: #2563eb;
        ">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def info_card(title: str, content: str, icon: str = "ℹ️", color: str = "blue"):
    """
    Display an information card

    Args:
        title: Card title
        content: Card content
        icon: Optional emoji icon
        color: Color theme (blue, green, red, yellow)
    """
    colors = {
        "blue": {"bg": "#dbeafe", "border": "#93c5fd", "text": "#1e40af"},
        "green": {"bg": "#d1fae5", "border": "#6ee7b7", "text": "#065f46"},
        "red": {"bg": "#fee2e2", "border": "#fca5a5", "text": "#991b1b"},
        "yellow": {"bg": "#fef3c7", "border": "#fcd34d", "text": "#92400e"}
    }

    theme = colors.get(color, colors["blue"])

    html = f"""
    <div style="
        background: linear-gradient(135deg, {theme['bg']} 0%, {theme['bg']} 100%);
        border: 1px solid {theme['border']};
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="font-size: 1.5rem;">{icon}</div>
            <div style="flex: 1;">
                <div style="
                    font-weight: 600;
                    color: {theme['text']};
                    margin-bottom: 0.25rem;
                ">{title}</div>
                <div style="
                    color: {theme['text']};
                    opacity: 0.9;
                    font-size: 0.95rem;
                ">{content}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def page_header(title: str, subtitle: str = None, icon: str = None):
    """
    Display a modern page header

    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Optional emoji icon
    """
    icon_html = f'<span style="margin-right: 1rem; font-size: 3rem;">{icon}</span>' if icon else ''
    subtitle_html = f'<p style="font-size: 1.125rem; color: #6b7280; margin-top: 0.5rem;">{subtitle}</p>' if subtitle else ''

    html = f"""
    <div style="margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 2px solid #e5e7eb;">
        <div style="display: flex; align-items: center;">
            {icon_html}
            <div>
                <h1 style="margin: 0 !important;">{title}</h1>
                {subtitle_html}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def section_divider(text: str = None):
    """
    Display a section divider with optional text

    Args:
        text: Optional text to display in the middle
    """
    if text:
        html = f"""
        <div style="
            display: flex;
            align-items: center;
            margin: 2rem 0;
            gap: 1rem;
        ">
            <div style="flex: 1; height: 1px; background: linear-gradient(90deg, transparent, #e5e7eb, transparent);"></div>
            <div style="
                font-weight: 600;
                color: #6b7280;
                text-transform: uppercase;
                font-size: 0.875rem;
                letter-spacing: 0.1em;
            ">{text}</div>
            <div style="flex: 1; height: 1px; background: linear-gradient(90deg, transparent, #e5e7eb, transparent);"></div>
        </div>
        """
    else:
        html = '<hr style="margin: 2rem 0; border: none; height: 1px; background: linear-gradient(90deg, transparent, #e5e7eb, transparent);">'

    st.markdown(html, unsafe_allow_html=True)

def progress_card(title: str, current: int, total: int, description: str = None):
    """
    Display a progress card

    Args:
        title: Progress title
        current: Current value
        total: Total value
        description: Optional description
    """
    percentage = int((current / total) * 100) if total > 0 else 0

    desc_html = f'<p style="color: #6b7280; font-size: 0.875rem; margin-top: 0.5rem;">{description}</p>' if description else ''

    html = f"""
    <div style="
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="margin: 0 !important; font-size: 1.125rem !important;">{title}</h3>
            <span style="
                font-weight: 700;
                color: #2563eb;
                font-size: 1.125rem;
            ">{current} / {total}</span>
        </div>
        <div style="
            width: 100%;
            height: 12px;
            background: #f3f4f6;
            border-radius: 10px;
            overflow: hidden;
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: linear-gradient(90deg, #2563eb 0%, #10b981 100%);
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
        <div style="
            display: flex;
            justify-content: space-between;
            margin-top: 0.5rem;
            font-size: 0.875rem;
            color: #6b7280;
        ">
            <span>{percentage}% Complete</span>
            <span>{total - current} Remaining</span>
        </div>
        {desc_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def empty_state(icon: str, title: str, description: str, action_label: str = None):
    """
    Display an empty state message

    Args:
        icon: Emoji icon
        title: Empty state title
        description: Description text
        action_label: Optional action button label
    """
    action_html = f'<button style="margin-top: 1rem; padding: 0.75rem 2rem; background: #2563eb; color: white; border: none; border-radius: 12px; font-weight: 600; cursor: pointer;">{action_label}</button>' if action_label else ''

    html = f"""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
        border-radius: 16px;
        border: 2px dashed #e5e7eb;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
        <h3 style="color: #1f2937; margin-bottom: 0.5rem;">{title}</h3>
        <p style="color: #6b7280; max-width: 400px; margin: 0 auto;">{description}</p>
        {action_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def sidebar_logout_button():
    """
    Display a logout button in the sidebar
    Shows current user info and logout button
    """
    if st.session_state.get("user"):
        user = st.session_state.user
        username = user.username if hasattr(user, 'username') else user.get('username', 'User')
        role = user.role if hasattr(user, 'role') else user.get('role', 'N/A')

        with st.sidebar:
            st.markdown("---")
            st.markdown("**👤 Current User**")
            st.write(f"**Username:** {username}")
            st.write(f"**Role:** {role}")

            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                logout()
                # Set flag to show logout message on login page
                st.session_state.just_logged_out = True
                # Use switch_page to redirect to login page
                st.switch_page("pages/0_🔐_Login.py")
