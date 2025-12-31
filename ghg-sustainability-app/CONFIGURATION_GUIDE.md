# 🔧 Environment Configuration Guide

Your `.env` file has been created! Here's what you need to configure:

---

## ✅ ALREADY CONFIGURED:
- ✓ SECRET_KEY (secure random key generated)
- ✓ APP_NAME
- ✓ DEBUG mode set to False
- ✓ File upload directory
- ✓ Email template directory

---

## 📋 CONFIGURATION OPTIONS:

### **OPTION 1: Using Docker (Recommended - No PostgreSQL Install Needed)**

✅ **Your current .env is already configured for Docker!**

**Database settings (already correct):**
```env
DATABASE_URL=postgresql://ghg_user:ghg_password@localhost:5432/ghg_db
POSTGRES_USER=ghg_user
POSTGRES_PASSWORD=ghg_password
POSTGRES_DB=ghg_db
```

**Next steps:**
```bash
# 1. Start Docker services
docker-compose up -d

# 2. Initialize database
docker-compose exec app alembic upgrade head

# 3. Seed data
docker-compose exec app python scripts/seed_all.py

# 4. Access the app
open http://localhost:8501
```

**That's it! Docker handles everything!** ✅

---

### **OPTION 2: Using Local PostgreSQL (Manual Setup)**

If you have PostgreSQL installed locally, follow these steps:

**Step 1: Install PostgreSQL (if not installed)**
```bash
# macOS
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian
sudo apt-get install postgresql-14
sudo systemctl start postgresql

# Windows
# Download from: https://www.postgresql.org/download/windows/
```

**Step 2: Create Database**
```bash
# Login to PostgreSQL
psql postgres

# In psql, run:
CREATE USER ghg_user WITH PASSWORD 'ghg_password';
CREATE DATABASE ghg_db OWNER ghg_user;
GRANT ALL PRIVILEGES ON DATABASE ghg_db TO ghg_user;

# Enable pg_trgm extension
\c ghg_db
CREATE EXTENSION IF NOT EXISTS pg_trgm;

# Exit
\q
```

**Step 3: Update .env (if needed)**

Your DATABASE_URL is already correct for local PostgreSQL:
```env
DATABASE_URL=postgresql://ghg_user:ghg_password@localhost:5432/ghg_db
```

**Step 4: Run the app**
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_all.py

# Start app
streamlit run app.py
```

---

## 📧 EMAIL CONFIGURATION (Optional)

Email notifications are **optional** but recommended for production.

### **Using Gmail:**

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Copy the generated 16-character password

3. **Update .env:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App password from step 2
SMTP_FROM=your-gmail@gmail.com
SMTP_USE_TLS=True
```

### **Using Other Email Providers:**

**Microsoft 365 / Outlook:**
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_FROM=your-email@outlook.com
SMTP_USE_TLS=True
```

**SendGrid:**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM=noreply@yourdomain.com
SMTP_USE_TLS=True
```

**Mailgun:**
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
SMTP_FROM=noreply@yourdomain.com
SMTP_USE_TLS=True
```

### **Skip Email (for testing):**

If you don't need email notifications yet, leave the default values. The app will:
- ✅ Still work perfectly
- ⚠️ Show warning: "SMTP credentials not configured, skipping email"
- ✅ All other features work normally

---

## 🔒 SECURITY SETTINGS:

### **Production Checklist:**

```env
# ✅ Use strong database password
POSTGRES_PASSWORD=your-strong-password-here

# ✅ Secret key is already secure (generated)
SECRET_KEY=K-a,ScAhBmEPu)PG2H=1/1`_}Vx&DQa'ivQLtaD=]1AZ"h-La$

# ✅ Debug mode OFF in production
DEBUG=False

# ✅ Change default user passwords after first login!
# Login and update via: pages/admin or database directly
```

---

## 🧪 TEST YOUR CONFIGURATION:

```bash
# Test database connection
python << 'PYEOF'
from sqlalchemy import create_engine
from core.config import settings

try:
    engine = create_engine(settings.DATABASE_URL)
    connection = engine.connect()
    print("✅ Database connection successful!")
    connection.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
PYEOF

# Test email configuration (optional)
python << 'PYEOF'
from core.emailer import emailer
from core.config import settings

if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
    result = emailer.send_email(
        to=[settings.SMTP_USERNAME],
        subject="Test Email - GHG App",
        body="<h1>Test successful!</h1><p>Email configuration works!</p>",
        html=True
    )
    if result:
        print("✅ Email configuration successful!")
    else:
        print("❌ Email configuration failed - check credentials")
else:
    print("ℹ️ Email not configured (optional)")
PYEOF
```

---

## 📊 CURRENT CONFIGURATION STATUS:

```
✅ Database:     Configured (PostgreSQL)
✅ SECRET_KEY:   Secure key generated
✅ App Name:     Set
✅ File Upload:  Configured (./uploads)
⚠️ Email:        Not configured (optional)
```

---

## 🚀 QUICK START COMMANDS:

### **Docker (Recommended):**
```bash
docker-compose up -d
docker-compose exec app python scripts/seed_all.py
open http://localhost:8501
```

### **Local:**
```bash
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_all.py
streamlit run app.py
```

---

## ❓ TROUBLESHOOTING:

**Problem: "database does not exist"**
```bash
# Docker: Restart services
docker-compose down -v
docker-compose up -d

# Local: Create database manually
createdb ghg_db -O ghg_user
```

**Problem: "pg_trgm extension does not exist"**
```bash
# Docker: Automatically created
# Local:
psql ghg_db -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

**Problem: "Email not sending"**
- ✓ Check SMTP credentials
- ✓ Enable 2FA and use app password for Gmail
- ✓ Check firewall allows port 587
- ℹ️ Email is optional - app works without it

---

**Your .env is ready! Choose Docker or Local PostgreSQL and run the app!** 🎉
