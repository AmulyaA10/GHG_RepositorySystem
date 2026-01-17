# 🚀 Deployment Guide - Streamlit Cloud

This guide will help you deploy your GHG Sustainability App to Streamlit Cloud.

## Prerequisites

- GitHub account
- Code pushed to a GitHub repository
- Streamlit Cloud account (free at https://streamlit.io/cloud)

## Step 1: Set Up Cloud PostgreSQL Database

You need a cloud-hosted PostgreSQL database. Here are your options:

### Option A: Neon (Recommended - Free Tier Available)

1. Go to https://neon.tech
2. Sign up for a free account
3. Create a new project
4. Copy the connection string (looks like: `postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb`)
5. Save this for Step 3

### Option B: Supabase (Alternative)

1. Go to https://supabase.com
2. Create a new project
3. Go to Settings → Database
4. Copy the "Connection string" (URI format)
5. Save this for Step 3

### Option C: ElephantSQL (Alternative)

1. Go to https://www.elephantsql.com
2. Create a free "Tiny Turtle" instance
3. Copy the connection URL
4. Save this for Step 3

## Step 2: Initialize Database Schema

Once you have your cloud database URL, you need to set up the tables and seed data.

### Method 1: Using Local Terminal

```bash
# Set your cloud database URL
export DATABASE_URL="your-cloud-database-url-here"

# Run migrations
alembic upgrade head

# Seed initial data
python3 scripts/seed_all.py
```

### Method 2: Using Python Script

Create a temporary file `init_cloud_db.py`:

```python
import os
os.environ['DATABASE_URL'] = 'your-cloud-database-url-here'

# Run migrations
from alembic import command
from alembic.config import Config
alembic_cfg = Config("alembic.ini")
command.upgrade(alembic_cfg, "head")

# Run seed script
exec(open('scripts/seed_all.py').read())
```

Then run:
```bash
python3 init_cloud_db.py
```

## Step 3: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit https://share.streamlit.io
   - Sign in with GitHub

2. **Create New App**
   - Click "New app"
   - Select your repository
   - Set main file path: `ghg-sustainability-app/app.py`
   - Click "Advanced settings..."

3. **Configure Secrets**
   Click "Advanced settings" → "Secrets" and add:

   ```toml
   # Database
   DATABASE_URL = "postgresql://your-connection-string-here"

   # Application
   APP_NAME = "GHG Sustainability Reporting System"
   SECRET_KEY = "your-random-secret-key-here"
   DEBUG = "False"

   # Optional: Email settings
   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = "587"
   SMTP_USERNAME = "your-email@gmail.com"
   SMTP_PASSWORD = "your-app-password"
   SMTP_FROM = "noreply@ghg-app.com"
   ```

   **Important**: Replace `DATABASE_URL` with your actual cloud database URL from Step 1!

4. **Deploy**
   - Click "Deploy!"
   - Wait for the app to build and start

## Step 4: Verify Deployment

Once deployed:

1. Open your app URL (e.g., https://your-app.streamlit.app)
2. Login with default credentials:
   - Username: `user_l1`
   - Password: `password123`
3. Create a test project to verify database connectivity

## Troubleshooting

### Error: "Cannot connect to database"

**Cause**: Database URL is incorrect or not set

**Fix**:
1. Go to Streamlit Cloud → Your App → Settings → Secrets
2. Verify `DATABASE_URL` is correct
3. Test connection locally first:
   ```bash
   psql "your-database-url-here"
   ```

### Error: "No module named 'psycopg2'"

**Cause**: Missing dependency

**Fix**: Make sure `requirements.txt` includes:
```
psycopg2-binary
```

### Error: "relation 'users' does not exist"

**Cause**: Database schema not initialized

**Fix**: Run migrations on your cloud database (see Step 2)

### Error: "Permission denied for database"

**Cause**: Database user doesn't have proper permissions

**Fix**: Make sure your database user has CREATE and WRITE permissions

## Security Best Practices

1. **Never commit secrets to Git**
   - Add `.streamlit/secrets.toml` to `.gitignore`
   - Use Streamlit Cloud secrets manager

2. **Change default passwords**
   - After deployment, change all default user passwords
   - Use the User Management page (L4 access)

3. **Use strong SECRET_KEY**
   - Generate a random secret key:
     ```python
     import secrets
     print(secrets.token_hex(32))
     ```

4. **Enable HTTPS**
   - Streamlit Cloud automatically provides HTTPS
   - Verify the lock icon in your browser

## Database Backup

**Important**: Set up regular backups!

- **Neon**: Automatic backups included
- **Supabase**: Daily backups on free tier
- **Manual backup**:
  ```bash
  pg_dump "your-database-url" > backup.sql
  ```

## Updating Your App

1. Push changes to GitHub
2. Streamlit Cloud automatically redeploys
3. Or click "Reboot app" in Streamlit Cloud dashboard

## Need Help?

- Streamlit Docs: https://docs.streamlit.io/streamlit-community-cloud
- GitHub Issues: Report issues in your repository
- Streamlit Community: https://discuss.streamlit.io

---

## Quick Reference

**Default Login Credentials:**
```
L1 User: user_l1 / password123
L2 User: user_l2 / password123
L3 User: user_l3 / password123
L4 User: user_l4 / password123
```

**Important Files:**
- `app.py` - Main application
- `requirements.txt` - Python dependencies
- `.streamlit/config.toml` - Streamlit configuration
- `.streamlit/secrets.toml` - Secrets (local only, not in Git)
- `alembic/` - Database migrations

**Database Connection:**
- Local: `postgresql://ghg_user:ghg_password@localhost:5432/ghg_db`
- Cloud: Set via `DATABASE_URL` in Streamlit Cloud secrets

---

🎉 **You're all set!** Your GHG Sustainability App is now live on Streamlit Cloud!
