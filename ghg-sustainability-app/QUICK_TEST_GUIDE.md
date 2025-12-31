# 🚀 Quick Test Guide
## How to Test Your GHG App

---

## 📋 Test Data Available

I've created comprehensive test data for you:

### Test Users (all password: `password123`)
```
user_l1 → Level 1 Data Entry
user_l2 → Level 2 Calculations
user_l3 → Level 3 Quality Review
user_l4 → Level 4 Dashboard & Approval
```

### Test Projects Created
1. **TechCorp 2024 - DRAFT** → For L1 testing (partial data)
2. **GreenEnergy Solutions 2024 - SUBMITTED** → For L2 to pick up
3. **Manufacturing Co 2024 - UNDER_CALCULATION** → For L2 testing (partial calcs)
4. **RetailChain 2024 Emissions - PENDING_REVIEW** → For L3 testing
5. **FinanceCorp 2024 Footprint - APPROVED** → For L4 testing

---

## 🧪 Quick Testing Steps

### 1. Test Level 1 (Data Entry)
```bash
# Login as L1
Username: user_l1
Password: password123

# What to test:
✅ View existing DRAFT project (TechCorp 2024)
✅ Add/edit activity data for criteria
✅ Upload evidence file
✅ Save data (including 0 values)
✅ Submit project for calculation
✅ Create new project
✅ Logout button
```

### 2. Test Level 2 (Calculations)
```bash
# Login as L2
Username: user_l2
Password: password123

# What to test:
✅ See SUBMITTED project (GreenEnergy Solutions)
✅ Search Ecoinvent database (try: "electricity", "diesel", "natural gas")
✅ Filter by scope
✅ Select emission factor
✅ Adjust GWP and unit conversion
✅ Calculate emissions
✅ Complete all calculations
✅ Submit for review
✅ Try to submit incomplete project (Manufacturing Co) - should block
✅ Logout button
```

### 3. Test Level 3 (Review)
```bash
# Login as L3
Username: user_l3
Password: password123

# What to test:
✅ View PENDING_REVIEW project (RetailChain 2024)
✅ Review project summary
✅ View calculations breakdown
✅ Download CSV
✅ Approve project
✅ Or reject project with reason code
✅ View review history
✅ Logout button
```

### 4. Test Level 4 (Dashboard & Lock)
```bash
# Login as L4
Username: user_l4
Password: password123

# What to test:
✅ View dashboard metrics
✅ See total emissions across all projects
✅ View projects by year
✅ Select APPROVED project (FinanceCorp 2024)
✅ Download Excel report
✅ Download PDF report
✅ Lock project with comments
✅ View locked project details
✅ Logout button
```

---

## 🎯 Key Features to Verify

### Navigation
- ✅ Sidebar shows all pages
- ✅ Can navigate between pages
- ✅ Logout button visible on all level pages
- ✅ User info displayed in sidebar

### Data Entry (L1)
- ✅ Project details card shows at top
- ✅ Progress counter (X/23)
- ✅ Criteria organized by scope
- ✅ Can save data including 0 values
- ✅ Evidence upload works
- ✅ No duplicate file uploads

### Calculations (L2)
- ✅ Ecoinvent search works
- ✅ Calculations save correctly
- ✅ Project totals update
- ✅ Completion check blocks incomplete submissions
- ✅ Error message is clear and helpful

### Review (L3)
- ✅ Can approve or reject
- ✅ Reason codes work
- ✅ Comments required
- ✅ Review history visible

### Dashboard (L4)
- ✅ All metrics display correctly
- ✅ Reports generate successfully
- ✅ Locking is permanent
- ✅ Snapshot created

---

## ✅ What Was Fixed

### Issues Resolved
1. **Evidence Upload Infinite Loop** → Fixed with session tracking
2. **Activity Data = 0 Not Saving** → Now allows zero values
3. **L2 Completion Validation** → Better error messages
4. **Logout Button** → Added to all level pages
5. **Project Details Display** → Enhanced with cards

### New Features Added
1. ✨ Comprehensive project details card in L1
2. ✨ Progress counter (X/23) in L1
3. ✨ Logout button with user info on all pages
4. ✨ Improved error messages in L2
5. ✨ Timeline display for locked projects

---

## 📊 Test Reports Generated

Check these files:
```
test_reports/test_excel_8.xlsx  → Excel report sample
test_reports/test_pdf_8.pdf     → PDF report sample
```

Both files generated successfully! ✅

---

## 🎨 UI Features to Notice

### Neon Theme
- Gradient animated backgrounds
- Glowing buttons on hover
- Neon text effects
- Glassmorphism cards
- Colored alert messages
- Smooth transitions

### User Experience
- Clear error messages
- Success confirmations
- Progress indicators
- Organized layouts
- Responsive design
- Helpful tooltips

---

## 🚨 Important Notes

### For Production
1. **Change default passwords** → Currently all use `password123`
2. **Configure email SMTP** → For workflow notifications
3. **Set up database backups** → Protect your data
4. **Enable SSL/TLS** → Secure connections
5. **Review file upload limits** → Prevent abuse

### Known Behaviors
- Evidence upload requires unique filenames per criterion
- Projects must have data before submission (L1 → L2)
- All calculations must be complete before review (L2 → L3)
- Locking is permanent and cannot be undone
- Email notifications fail gracefully if not configured

---

## 📝 Quick Commands

### View All Projects
```python
python3 -c "from core.db import get_db; from models import Project; db = next(get_db()); [print(f'{p.id}: {p.project_name} - {p.status}') for p in db.query(Project).all()]"
```

### Reset Test Data
```bash
python3 create_comprehensive_test_data.py
```

### Test Report Generation
```bash
python3 << 'EOF'
from core.db import get_db
from models import Project, Calculation
from core.reporting import report_generator
from pathlib import Path

db = next(get_db())
project = db.query(Project).filter(Project.id == 8).first()
calculations = db.query(Calculation).filter(Calculation.project_id == project.id).all()

calc_dicts = [{'scope': c.scope, 'category': c.category, 'activity_data': c.activity_data,
               'emission_factor': c.emission_factor, 'emissions_tco2e': c.emissions_tco2e}
              for c in calculations]

output_dir = Path("test_reports")
output_dir.mkdir(exist_ok=True)

print("Generating Excel...")
report_generator.generate_excel_report(project, calc_dicts, output_dir / "test.xlsx")
print("Generating PDF...")
report_generator.generate_pdf_report(project, calc_dicts, output_dir / "test.pdf")
print("Done!")
EOF
```

---

## 🎯 Testing Checklist

Before saying "it works":

- [ ] Logged in as all 4 user types
- [ ] Created a new project in L1
- [ ] Entered data for all 23 criteria
- [ ] Uploaded evidence file
- [ ] Submitted project to L2
- [ ] Searched Ecoinvent database
- [ ] Calculated emissions
- [ ] Submitted to L3
- [ ] Reviewed and approved project
- [ ] Locked project in L4
- [ ] Downloaded Excel report
- [ ] Downloaded PDF report
- [ ] Logged out successfully
- [ ] Checked all pages have logout button
- [ ] Verified project details display correctly
- [ ] Confirmed zero values can be saved

---

## 💡 Tips

1. **Start Fresh**: Test with the comprehensive test data already created
2. **Follow the Flow**: L1 → L2 → L3 → L4 in order
3. **Check Sidebar**: All pages and logout button should be visible
4. **Look for Neon**: Enjoy the modern UI with glowing effects
5. **Read Messages**: All errors and success messages are clear
6. **Take Your Time**: Explore each feature thoroughly

---

## 📞 Need Help?

Check these files:
- `test_all_fields.md` → Detailed test results
- `TESTING_SUMMARY.md` → Complete testing report
- `QUICK_TEST_GUIDE.md` → This file

---

**Ready to test?** 🚀

1. Open http://localhost:8501
2. Login as `user_l1` / `password123`
3. Click "📝 Level1 Data Entry" in sidebar
4. Start testing!

**Have fun exploring your GHG Sustainability App!** 🌍💚
