#!/usr/bin/env python3
"""
Test Password Reset Functionality
Quick script to test password reset email sending
"""
import sys
from core.db import get_db
from core.password_reset import send_password_reset_email
from core.email import email_service

def test_email_configuration():
    """Test if email service is configured"""
    print("\n" + "="*60)
    print("🔧 Testing Email Configuration")
    print("="*60)

    if email_service.is_configured():
        print("✅ Email service is configured")
        print(f"   SMTP Host: {email_service.smtp_host}")
        print(f"   SMTP Port: {email_service.smtp_port}")
        print(f"   From Email: {email_service.smtp_from}")
        print(f"   Use TLS: {email_service.smtp_use_tls}")
        return True
    else:
        print("❌ Email service is NOT configured")
        print("\nPlease configure email settings in .env file:")
        print("  SMTP_HOST=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SMTP_USERNAME=your-email@gmail.com")
        print("  SMTP_PASSWORD=your-app-password")
        print("  SMTP_FROM=noreply@yourcompany.com")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n" + "="*60)
    print("🗄️  Testing Database Connection")
    print("="*60)

    try:
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_password_reset_request(username_or_email: str):
    """Test password reset request"""
    print("\n" + "="*60)
    print(f"📧 Testing Password Reset for: {username_or_email}")
    print("="*60)

    db = next(get_db())
    try:
        reset_url_base = "http://localhost:8501/Reset_Password"

        print(f"\n📤 Sending password reset email...")
        success, message = send_password_reset_email(
            db,
            username_or_email,
            reset_url_base
        )

        if success:
            print(f"✅ {message}")
            print("\n📧 Check your email for the reset link!")

            # Show token details if user exists
            from models import User, PasswordResetToken
            user = db.query(User).filter(
                (User.email == username_or_email) | (User.username == username_or_email)
            ).first()

            if user:
                latest_token = db.query(PasswordResetToken).filter(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used == False
                ).order_by(PasswordResetToken.created_at.desc()).first()

                if latest_token:
                    print("\n🔑 Token Details (for debugging):")
                    print(f"   Token: {latest_token.token}")
                    print(f"   Expires: {latest_token.expires_at}")
                    print(f"   Reset Link: {reset_url_base}?token={latest_token.token}")

            return True
        else:
            print(f"❌ Failed: {message}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def interactive_test():
    """Interactive testing mode"""
    print("\n" + "="*60)
    print("🧪 PASSWORD RESET INTERACTIVE TEST")
    print("="*60)

    # Test email configuration
    if not test_email_configuration():
        return

    # Test database connection
    if not test_database_connection():
        return

    print("\n" + "="*60)
    print("Available test users:")
    print("  - user_l1 (l1@example.com)")
    print("  - user_l2 (l2@example.com)")
    print("  - user_l3 (l3@example.com)")
    print("  - user_l4 (l4@example.com)")
    print("="*60)

    # Get user input
    username_or_email = input("\nEnter username or email to test: ").strip()

    if not username_or_email:
        print("❌ No username/email provided. Exiting.")
        return

    # Test password reset
    test_password_reset_request(username_or_email)

    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Check your email inbox")
    print("2. Click the reset link in the email")
    print("3. Set a new password")
    print("4. Try logging in with the new password")
    print("")

def quick_test():
    """Quick non-interactive test"""
    print("\n🚀 Running Quick Test...")

    if not test_email_configuration():
        sys.exit(1)

    if not test_database_connection():
        sys.exit(1)

    # Test with default user
    test_password_reset_request("user_l1")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            quick_test()
        elif sys.argv[1] == "--user":
            if len(sys.argv) < 3:
                print("Usage: python test_password_reset.py --user <username_or_email>")
                sys.exit(1)
            test_email_configuration()
            test_database_connection()
            test_password_reset_request(sys.argv[2])
        else:
            print("Usage:")
            print("  python test_password_reset.py              # Interactive mode")
            print("  python test_password_reset.py --quick       # Quick test with user_l1")
            print("  python test_password_reset.py --user <email>  # Test specific user")
            sys.exit(1)
    else:
        interactive_test()
