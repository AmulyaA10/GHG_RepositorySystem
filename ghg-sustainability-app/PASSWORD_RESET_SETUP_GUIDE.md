# Password Reset Setup & Testing Guide

## 📋 Overview

This guide explains how to set up and test the email-based password reset functionality in the GHG Sustainability App.

## 🔧 Email Configuration

### Option 1: Gmail (Recommended for Testing)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (custom name)"
   - Name it "GHG App"
   - Copy the 16-character password

3. **Update `.env` file**:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM=your-email@gmail.com
SMTP_USE_TLS=True
```

### Option 2: Other Email Providers

#### **Outlook/Office 365**
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_FROM=your-email@outlook.com
SMTP_USE_TLS=True
```

#### **SendGrid** (Production Recommended)
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM=noreply@yourdomain.com
SMTP_USE_TLS=True
```

#### **Amazon SES**
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-aws-smtp-username
SMTP_PASSWORD=your-aws-smtp-password
SMTP_FROM=verified-sender@yourdomain.com
SMTP_USE_TLS=True
```

## 📦 Required Dependencies

Ensure these packages are installed:

```bash
pip install python-dotenv
pip install bcrypt
pip install sqlalchemy
pip install psycopg2-binary
pip install streamlit
```

## 🗄️ Database Setup

The password reset tokens table is already created via Alembic migration. Verify it exists:

```bash
python3 -m alembic current
```

You should see migration: `b46f57520577 (head)`

## 🚀 Testing the Password Reset Flow

### Step 1: Configure Email (Development Testing)

For quick testing without real email, you can use **MailHog** (fake SMTP server):

```bash
# Install MailHog
brew install mailhog  # macOS
# or
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog  # Docker

# Update .env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=noreply@ghgapp.local
SMTP_USE_TLS=False
```

Access MailHog web UI at: http://localhost:8025

### Step 2: Start the Application

```bash
python3 -m streamlit run app.py
```

Access at: http://localhost:8501

### Step 3: Test Password Reset Flow

#### **A. Request Password Reset**

1. Go to **Login** page
2. Click **"Forgot Password?"** button
3. Enter username or email: `user_l1` or `l1@example.com`
4. Click **"Send Reset Link"**
5. Check email (or MailHog at http://localhost:8025)

#### **B. Use Reset Link**

1. Open the email
2. Click the **"Reset Password"** button (or copy/paste the link)
3. You'll be taken to the Reset Password page
4. Enter a new password (min 8 characters)
5. Confirm the password
6. Click **"Reset Password"**

#### **C. Verify New Password**

1. Go back to **Login** page
2. Login with your new password
3. Should be successful!

### Step 4: Test Edge Cases

#### **Invalid Token**
- Try accessing reset page without token: http://localhost:8501/Reset_Password
- Should show error: "Invalid Reset Link"

#### **Expired Token**
- Wait 24 hours (or manually change `expires_at` in database)
- Try using old link
- Should show: "Invalid or Expired Reset Link"

#### **Used Token**
- Use a reset link once successfully
- Try using the same link again
- Should show: "Invalid or Expired Reset Link"

#### **Non-existent User**
- Request reset for: `nonexistent@example.com`
- Should show success message (security: doesn't reveal if user exists)
- No email should be sent

## 🔍 Monitoring & Debugging

### Check Database Tokens

```bash
psql "postgresql://ghg_user:ghg_password@localhost:5432/ghg_db" -c "SELECT id, user_id, token, expires_at, used, created_at FROM password_reset_tokens ORDER BY created_at DESC LIMIT 5;"
```

### View Application Logs

The application logs password reset events:
- Token creation
- Email sending
- Token validation
- Password reset success/failure

Check Streamlit console output for log messages.

### Check Audit Logs

All password reset actions are logged:

```bash
psql "postgresql://ghg_user:ghg_password@localhost:5432/ghg_db" -c "SELECT user_id, action, details, created_at FROM audit_logs WHERE action LIKE '%PASSWORD%' ORDER BY created_at DESC LIMIT 10;"
```

## 🛡️ Security Features

### Built-in Security

✅ **Token Security**
- Tokens are cryptographically secure (using `secrets` module)
- 32-byte URL-safe tokens
- Stored hashed in database (optional enhancement)

✅ **Expiration**
- Tokens expire after 24 hours
- Configurable expiration time

✅ **Single Use**
- Tokens can only be used once
- Used tokens are marked and cannot be reused

✅ **User Enumeration Prevention**
- Same response whether user exists or not
- Prevents attackers from discovering valid usernames/emails

✅ **Audit Trail**
- All password reset actions logged
- Includes IP address (when available)
- Timestamp for all events

✅ **Rate Limiting** (Recommended to add)
- Consider adding rate limiting on forgot password requests
- Prevent abuse/spam

### Additional Security Recommendations

1. **Add CAPTCHA** to forgot password form
2. **Rate limit** password reset requests (e.g., max 3 per hour per IP)
3. **Hash tokens** before storing in database
4. **Add email verification** for new accounts
5. **Implement account lockout** after multiple failed attempts

## 📊 Production Checklist

Before deploying to production:

- [ ] Configure production email service (SendGrid, SES, etc.)
- [ ] Update `SMTP_FROM` to your domain email
- [ ] Test email delivery to multiple email providers
- [ ] Set up email monitoring/alerts
- [ ] Configure proper SSL certificates
- [ ] Update reset URL base to production domain
- [ ] Set up automated cleanup of expired tokens (cron job)
- [ ] Add rate limiting for password reset requests
- [ ] Review and test email templates
- [ ] Monitor email deliverability
- [ ] Set up proper logging and monitoring

## 🔧 Troubleshooting

### Email Not Sending

**Symptom**: User requests reset but no email arrives

**Solutions**:
1. Check email configuration in `.env`
2. Verify SMTP credentials are correct
3. Check application logs for error messages
4. Test SMTP connection manually:

```python
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
server.quit()
print("Connection successful!")
```

5. Check spam/junk folder
6. Verify "from" email is not blacklisted

### Token Validation Fails

**Symptom**: Reset link shows "Invalid or Expired"

**Solutions**:
1. Check token in database:
   ```sql
   SELECT * FROM password_reset_tokens WHERE token = 'YOUR_TOKEN';
   ```
2. Verify token hasn't expired (`expires_at` > now)
3. Verify token hasn't been used (`used = false`)
4. Check for URL encoding issues in token

### Password Reset Fails

**Symptom**: Error when submitting new password

**Solutions**:
1. Check database connection
2. Verify user account is active
3. Review application logs for specific error
4. Ensure password meets requirements

## 📞 Support

For issues or questions:
1. Check application logs
2. Review database audit logs
3. Test email configuration
4. Contact system administrator

## 🎯 Testing Script

Quick test script to verify functionality:

```python
# test_password_reset.py
from core.db import get_db
from core.password_reset import send_password_reset_email

db = next(get_db())
success, message = send_password_reset_email(
    db,
    "user_l1",  # or email
    "http://localhost:8501/Reset_Password"
)
print(f"Success: {success}, Message: {message}")
db.close()
```

Run with:
```bash
python3 test_password_reset.py
```

---

## 📝 Summary

The password reset system provides:
- ✅ Secure token-based password reset
- ✅ Email notifications
- ✅ Token expiration (24 hours)
- ✅ Single-use tokens
- ✅ Audit logging
- ✅ User-friendly interface
- ✅ Production-ready security

All features are ready to use once email is configured!
