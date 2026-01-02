# 🚀 Streamlit Cloud Deployment Guide
## GHG Sustainability Reporting System

**Last Updated:** January 1, 2026

---

## 📋 Prerequisites

Before deploying, ensure you have:
- ✅ GitHub account
- ✅ Streamlit Cloud account (sign up at https://streamlit.io/cloud)
- ✅ PostgreSQL database (hosted - see Database Setup section)
- ✅ Your code pushed to a GitHub repository

---

## 🗄️ Step 1: Set Up Production Database

### Option A: Supabase (Recommended - Free Tier Available)

1. **Go to:** https://supabase.com
2. **Sign up** and create a new project
3. **Project Settings:**
   - Project Name: `ghg-sustainability-db`
   - Database Password: (create a strong password)
   - Region: Choose closest to your users

4. **Get Connection String:**
   - Go to: Settings → Database
   - Copy the **Connection String (URI)**
   - It looks like: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`

5. **Run Database Setup:**
   ```sql
   -- In Supabase SQL Editor, run:

   -- Create tables (copy from init_db.py or use alembic)
   -- You'll need to run your migrations
   ```

### Option B: Neon (Free Tier with Generous Limits)

1. **Go to:** https://neon.tech
2. **Sign up** and create a project
3. **Get connection string** from dashboard
4. Format: `postgresql://[user]:[password]@[host]/[dbname]?sslmode=require`

### Option C: Railway (Simple Deploy)

1. **Go to:** https://railway.app
2. **Create PostgreSQL database**
3. **Copy connection string** from dashboard

### Option D: ElephantSQL (Classic Choice)

1. **Go to:** https://www.elephantsql.com
2. **Create Tiny Turtle plan** (free)
3. **Copy URL** from details page

---

## 📦 Step 2: Prepare Your Repository

### 2.1 Required Files (Already Created ✅)

Your repository must have these files:

```
ghg-sustainability-app/
├── app.py                          # Main Streamlit app
├── requirements.txt                # Python dependencies ✅
├── packages.txt                    # System dependencies ✅
├── .streamlit/
│   └── config.toml                 # Streamlit config ✅
├── core/                           # Core modules
├── models/                         # Database models
├── pages/                          # Streamlit pages
└── migrations/                     # Database migrations
```

### 2.2 Verify Files

```bash
# Check files exist
ls -la requirements.txt packages.txt .streamlit/config.toml

# View requirements
cat requirements.txt

# View system packages
cat packages.txt
```

---

## 🌐 Step 3: Push to GitHub

### 3.1 Initialize Git (if not already done)

```bash
cd /Users/amulyaalva/Documents/GHGProject/ghg-sustainability-app

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit for Streamlit deployment"
```

### 3.2 Create GitHub Repository

1. Go to: https://github.com/new
2. **Repository name:** `ghg-sustainability-app`
3. **Description:** `ISO 14064-1 Compliant GHG Emissions Reporting System`
4. **Visibility:** Choose Public or Private
5. Click **"Create repository"**

### 3.3 Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/ghg-sustainability-app.git

# Push code
git branch -M main
git push -u origin main
```

---

## ☁️ Step 4: Deploy to Streamlit Cloud

### 4.1 Connect GitHub

1. **Go to:** https://share.streamlit.io
2. **Sign in** with GitHub
3. Click **"New app"**

### 4.2 Configure Deployment

**App Settings:**
- **Repository:** `YOUR_USERNAME/ghg-sustainability-app`
- **Branch:** `main`
- **Main file path:** `app.py`

**Advanced Settings:**
- **Python version:** `3.11` (recommended)

### 4.3 Add Secrets

Click **"Advanced settings"** → **"Secrets"**

Add this TOML configuration (replace with your values):

```toml
# Database Configuration
DATABASE_URL = "postgresql://user:password@host:5432/database?sslmode=require"

# Application Settings
APP_NAME = "GHG Sustainability Reporting System"
SECRET_KEY = "your-secret-key-change-this-in-production"
DEBUG = false

# SMTP Email Configuration (optional)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
SMTP_FROM = "noreply@yourcompany.com"
SMTP_USE_TLS = true

# File Storage
UPLOAD_DIR = "./uploads"
MAX_UPLOAD_SIZE_MB = 10
```

**Important:**
- Replace `DATABASE_URL` with your actual database connection string
- Generate a strong `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Keep `DEBUG = false` for production

### 4.4 Deploy

Click **"Deploy!"**

Streamlit will:
1. ✅ Clone your repository
2. ✅ Install system packages from `packages.txt`
3. ✅ Install Python packages from `requirements.txt`
4. ✅ Run database migrations (if configured)
5. ✅ Start your app

**Deployment takes 2-5 minutes.**

---

## 🗄️ Step 5: Initialize Production Database

### 5.1 Run Migrations

After deployment, you need to set up the database schema.

**Option A: Using Streamlit Terminal (If Available)**

In your Streamlit Cloud app logs, you might see a terminal. If so:

```bash
alembic upgrade head
```

**Option B: Local Migration to Production DB**

From your local machine:

```bash
# Set production database URL temporarily
export DATABASE_URL="your-production-db-url"

# Run migrations
alembic upgrade head

# Create initial users (use create_users.py script)
python create_initial_users.py
```

### 5.2 Create Initial Users

Create a file `create_initial_users.py`:

```python
from core.db import get_db
from models import User
from core.auth import hash_password

def create_users():
    db = next(get_db())

    users = [
        {
            "username": "admin_l4",
            "email": "admin@yourcompany.com",
            "password": "ChangeMe123!",  # CHANGE THIS
            "full_name": "System Administrator",
            "role": "L4"
        },
        {
            "username": "user_l1",
            "email": "l1@yourcompany.com",
            "password": "ChangeMe123!",  # CHANGE THIS
            "full_name": "Data Entry User",
            "role": "L1"
        }
    ]

    for user_data in users:
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=True
            )
            db.add(user)

    db.commit()
    print("✅ Users created successfully!")

if __name__ == "__main__":
    create_users()
```

Run it:
```bash
python create_initial_users.py
```

---

## ✅ Step 6: Verify Deployment

### 6.1 Check App Status

Your app will be available at:
```
https://YOUR_APP_NAME.streamlit.app
```

### 6.2 Test Basic Functions

1. ✅ **Home Page** loads
2. ✅ **Login Page** works
3. ✅ **Database connection** successful
4. ✅ **User login** works
5. ✅ **Create project** works
6. ✅ **Navigation** between pages works

### 6.3 Check Logs

In Streamlit Cloud dashboard:
- Click **"Manage app"**
- View **"Logs"** for errors
- Monitor **"Resource usage"**

---

## 🔧 Step 7: Post-Deployment Configuration

### 7.1 Custom Domain (Optional)

1. Go to app settings
2. Click **"Custom domain"**
3. Add your domain: `ghg.yourcompany.com`
4. Update DNS records as instructed

### 7.2 Update Secrets

To update environment variables:
1. Go to app settings
2. Click **"Secrets"**
3. Edit and save
4. App will auto-restart

### 7.3 Enable Analytics (Optional)

In `.streamlit/config.toml`:
```toml
[browser]
gatherUsageStats = true  # Enable Streamlit analytics
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError"

**Solution:** Add missing package to `requirements.txt`

```bash
# Add package
echo "missing-package==1.0.0" >> requirements.txt

# Commit and push
git add requirements.txt
git commit -m "Add missing package"
git push
```

### Issue: "Database connection failed"

**Checks:**
1. ✅ Verify `DATABASE_URL` in secrets
2. ✅ Check database is running
3. ✅ Verify connection string format includes `?sslmode=require`
4. ✅ Check database allows connections from Streamlit Cloud IPs

**Fix:** Update secrets with correct connection string

### Issue: "Import errors"

**Solution:** Check file structure and imports

```python
# app.py should have
from core.db import get_db
from models import Project

# Not
from .core.db import get_db  # Wrong!
```

### Issue: "Alembic migrations not running"

**Solution:** Run migrations manually:

1. Connect to production DB locally:
   ```bash
   export DATABASE_URL="production-url"
   alembic upgrade head
   ```

2. Or create a startup script in `app.py`:
   ```python
   # Add at top of app.py
   from core.db import init_db

   # Initialize DB on first run
   try:
       init_db()
   except Exception as e:
       st.error(f"Database initialization error: {e}")
   ```

### Issue: "App keeps restarting"

**Checks:**
1. Check logs for errors
2. Verify all secrets are set
3. Check resource limits not exceeded
4. Verify requirements.txt has correct versions

---

## 📊 Monitoring & Maintenance

### Monitor App Health

**Streamlit Cloud Dashboard:**
- View real-time logs
- Monitor CPU/Memory usage
- Track app restarts

### Database Monitoring

**Check Database Size:**
```sql
SELECT
    pg_size_pretty(pg_database_size('your_database')) as size;
```

**Check Active Connections:**
```sql
SELECT count(*) FROM pg_stat_activity;
```

### Update App

```bash
# Make changes locally
git add .
git commit -m "Update feature X"
git push

# Streamlit Cloud auto-deploys!
```

---

## 🔒 Security Best Practices

### 1. Environment Variables

✅ **NEVER** commit secrets to git
✅ Use Streamlit secrets for all sensitive data
✅ Rotate secrets periodically

### 2. Database

✅ Use SSL/TLS connections (`?sslmode=require`)
✅ Limit database user permissions
✅ Enable connection pooling (already configured)
✅ Regular backups

### 3. Authentication

✅ Change default passwords immediately
✅ Use strong passwords (12+ characters)
✅ Implement session timeouts
✅ Enable HTTPS (automatic on Streamlit Cloud)

### 4. File Uploads

✅ Limit file sizes (configured in config.toml)
✅ Validate file types
✅ Scan uploaded files if possible

---

## 📈 Scaling Considerations

### Free Tier Limits

Streamlit Cloud Free:
- ✅ 1 private app OR unlimited public apps
- ✅ Shared resources
- ✅ Auto-sleep after inactivity

### Upgrade to Pro

For production use, consider:
- **Streamlit Community Cloud Pro:** $20/month per developer
- **Streamlit Enterprise:** Custom pricing
- **Self-hosting:** On AWS, Azure, or Google Cloud

---

## 🎯 Deployment Checklist

Before going live:

- [ ] Database set up and tested
- [ ] Migrations run successfully
- [ ] Initial users created
- [ ] All secrets configured
- [ ] Test all user roles (L1, L2, L3, L4)
- [ ] Test project creation workflow
- [ ] Test calculations
- [ ] Test reviews and approvals
- [ ] Test report generation
- [ ] Verify email notifications (if enabled)
- [ ] Check mobile responsiveness
- [ ] Monitor logs for errors
- [ ] Document admin procedures
- [ ] Train users
- [ ] Set up backups

---

## 📞 Support Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Streamlit Forum:** https://discuss.streamlit.io
- **Streamlit Cloud Status:** https://status.streamlit.io

---

## 🎓 Next Steps After Deployment

1. **User Training:** Create user guides for each role
2. **Data Migration:** Import existing data if needed
3. **Monitoring:** Set up alerts for errors
4. **Backups:** Schedule regular database backups
5. **Updates:** Plan regular maintenance windows

---

**Deployment Guide Version:** 1.0
**Last Updated:** January 1, 2026
**Prepared By:** Claude Code Assistant
