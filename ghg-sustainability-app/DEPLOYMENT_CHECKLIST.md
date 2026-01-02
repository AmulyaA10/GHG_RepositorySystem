# ✅ Streamlit Deployment Checklist

Use this checklist to ensure smooth deployment.

---

## 📋 Pre-Deployment (Local)

### Files Ready
- [ ] `requirements.txt` - All dependencies listed
- [ ] `packages.txt` - System packages for PostgreSQL
- [ ] `.streamlit/config.toml` - Streamlit configuration
- [ ] `.gitignore` - Excludes .env and secrets
- [ ] `DEPLOYMENT_GUIDE.md` - Documentation complete

### Code Ready
- [ ] All tests passing locally
- [ ] No hardcoded credentials
- [ ] Database connection uses environment variables
- [ ] All imports working correctly
- [ ] No debug print statements in production code

### Database Schema
- [ ] Alembic migrations created
- [ ] Migration files committed to git
- [ ] Tested migrations locally

---

## 🗄️ Database Setup

### Production Database
- [ ] Production PostgreSQL database created
- [ ] Connection string obtained
- [ ] Database accessible from internet (with proper security)
- [ ] SSL/TLS enabled (`?sslmode=require` in connection string)

### Database Configuration
- [ ] User credentials created
- [ ] Proper permissions set (no superuser access needed)
- [ ] Connection pooling enabled (already in code)
- [ ] Backup strategy planned

---

## 🌐 GitHub Repository

### Repository Setup
- [ ] GitHub repository created
- [ ] Repository is Public or Private (based on your needs)
- [ ] All code committed
- [ ] `.gitignore` properly excluding secrets
- [ ] No `.env` file in repository
- [ ] `README.md` updated

### Push Code
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

---

## ☁️ Streamlit Cloud Setup

### Account & App
- [ ] Streamlit Cloud account created (https://share.streamlit.io)
- [ ] GitHub connected to Streamlit Cloud
- [ ] New app created

### App Configuration
- [ ] Repository: `YOUR_USERNAME/ghg-sustainability-app`
- [ ] Branch: `main`
- [ ] Main file: `app.py`
- [ ] Python version: `3.11`

### Secrets Configuration
Add in Advanced Settings → Secrets:

```toml
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"
APP_NAME = "GHG Sustainability Reporting System"
SECRET_KEY = "your-secret-key-generated"
DEBUG = false
UPLOAD_DIR = "./uploads"
MAX_UPLOAD_SIZE_MB = 10
```

- [ ] `DATABASE_URL` set correctly
- [ ] `SECRET_KEY` generated (use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `DEBUG` set to `false`
- [ ] All other required secrets added

---

## 🚀 Deployment

### Deploy App
- [ ] Click "Deploy" in Streamlit Cloud
- [ ] Wait for deployment (2-5 minutes)
- [ ] Check deployment logs for errors

### Database Initialization
- [ ] Run migrations on production database:
  ```bash
  export DATABASE_URL="your-production-url"
  alembic upgrade head
  ```
- [ ] Create initial users:
  ```bash
  python create_initial_users.py
  ```
- [ ] Verify tables created in database

---

## ✅ Post-Deployment Testing

### Basic Functionality
- [ ] App loads at `https://your-app.streamlit.app`
- [ ] Home page displays correctly
- [ ] No errors in browser console (F12)
- [ ] Theme/styling looks correct

### Authentication
- [ ] Login page accessible
- [ ] Can login with L1 user
- [ ] Can login with L2 user
- [ ] Can login with L3 user
- [ ] Can login with L4 user
- [ ] Logout works
- [ ] Session persists across page navigation

### Database Operations
- [ ] Can create a new project (L1)
- [ ] Can view projects list
- [ ] Can add project data (L1)
- [ ] Can submit project (L1)
- [ ] Can perform calculations (L2)
- [ ] Can review projects (L3)
- [ ] Can approve projects (L4)
- [ ] Can generate reports (L4)

### Performance
- [ ] Pages load in < 3 seconds
- [ ] Pagination working
- [ ] Search functionality working
- [ ] Dashboard metrics cached (check load time)
- [ ] No memory errors in logs

### Edge Cases
- [ ] Try invalid login credentials
- [ ] Try accessing pages without login
- [ ] Try L1 user accessing L4 page (should deny)
- [ ] Create project with 20+ data entries
- [ ] Test with special characters in project names

---

## 🔒 Security Review

### Credentials
- [ ] Default passwords changed
- [ ] Strong passwords enforced
- [ ] No credentials in git history
- [ ] Secrets properly stored in Streamlit

### Database
- [ ] SSL connection enforced
- [ ] Database user has minimal permissions
- [ ] No direct database access from public
- [ ] Prepared statements used (SQLAlchemy handles this)

### Application
- [ ] XSRF protection enabled (in config.toml)
- [ ] CORS properly configured
- [ ] File upload size limited
- [ ] Input validation working

---

## 📊 Monitoring Setup

### Streamlit Cloud
- [ ] Monitoring dashboard accessible
- [ ] Email notifications enabled
- [ ] Resource usage checked
- [ ] Logs reviewed for errors

### Database
- [ ] Can connect to database directly
- [ ] Backup schedule configured
- [ ] Monitoring queries performance
- [ ] Connection pool utilization checked

---

## 📖 Documentation

### For Users
- [ ] User guide created for each role
- [ ] Training materials prepared
- [ ] FAQ document created
- [ ] Support contact information available

### For Admins
- [ ] Admin procedures documented
- [ ] Database backup/restore process
- [ ] Troubleshooting guide
- [ ] Update deployment process

---

## 🎓 User Training

### Training Sessions
- [ ] L1 users trained (Data Entry)
- [ ] L2 users trained (Calculations)
- [ ] L3 users trained (Review)
- [ ] L4 users trained (Dashboard & Approval)

### Materials Provided
- [ ] Login credentials sent securely
- [ ] User guides distributed
- [ ] Training videos (if created)
- [ ] Support contact information

---

## 🔄 Ongoing Maintenance

### Regular Tasks
- [ ] Weekly: Check logs for errors
- [ ] Weekly: Monitor resource usage
- [ ] Monthly: Review user access
- [ ] Monthly: Database backup verification
- [ ] Quarterly: Update dependencies
- [ ] Quarterly: Security review

### Update Process
- [ ] Document change management process
- [ ] Test updates locally first
- [ ] Plan maintenance windows
- [ ] Notify users of updates

---

## 🆘 Emergency Contacts

**Streamlit Cloud Support:**
- Status: https://status.streamlit.io
- Community: https://discuss.streamlit.io

**Database Support:**
- Provider support portal
- Emergency contact number

**Internal Contacts:**
- System Administrator: _____________
- Database Admin: _____________
- App Owner: _____________

---

## 📝 Sign-Off

### Deployment Approved By:

- [ ] **Technical Lead:** _____________ Date: _______
- [ ] **Security Review:** _____________ Date: _______
- [ ] **Database Admin:** _____________ Date: _______
- [ ] **Business Owner:** _____________ Date: _______

### Go-Live Date: ______________

### Notes:
_________________________________________________
_________________________________________________
_________________________________________________

---

**Checklist Version:** 1.0
**Last Updated:** January 1, 2026
