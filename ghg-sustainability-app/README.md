# GHG Sustainability Reporting System

A production-grade Streamlit application for GHG (Greenhouse Gas) emissions calculation and reporting, compliant with ISO 14064-1 and GHG Protocol standards.

## Features

- **Role-Based Workflow**: 4-level approval workflow (L1/L2/L3/L4)
- **23 GHG Categories**: Comprehensive coverage of Scope 1, 2, and 3 emissions
- **Ecoinvent Database**: Server-side search with 50+ emission factors
- **Formula Engine**: Precise calculations using Decimal arithmetic
- **Audit Trail**: Complete logging of all state transitions
- **Email Notifications**: Automated workflow notifications
- **Evidence Management**: File upload and tracking
- **Report Generation**: Excel and PDF export
- **Docker Deployment**: Production-ready containerization

## Architecture

### Technology Stack

- **Framework**: Streamlit 1.29+
- **Database**: PostgreSQL 14+ with SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: bcrypt password hashing
- **Testing**: pytest
- **Containerization**: Docker + docker-compose

### Project Structure

```
ghg-sustainability-app/
├── core/                   # Core business logic
│   ├── config.py          # Configuration management
│   ├── db.py              # Database setup
│   ├── auth.py            # Authentication & authorization
│   ├── workflow.py        # State machine
│   ├── formulas.py        # Calculation engine
│   ├── validation.py      # Data validation
│   ├── storage.py         # File storage
│   ├── emailer.py         # Email notifications
│   └── reporting.py       # Report generation
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── project.py
│   ├── criteria.py
│   ├── project_data.py
│   ├── calculation.py
│   ├── review.py
│   ├── approval.py
│   ├── ecoinvent.py
│   ├── reason_code.py
│   ├── formula.py
│   ├── audit_log.py
│   └── evidence.py
├── pages/                  # Streamlit pages
│   ├── 0_🔐_Login.py
│   ├── 1_📝_Level1_Data_Entry.py
│   ├── 2_🧮_Level2_Calculations.py
│   ├── 3_✅_Level3_Review.py
│   └── 4_📊_Level4_Dashboard.py
├── migrations/             # Alembic migrations
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── scripts/                # Seed scripts
│   ├── seed_users.py
│   ├── seed_criteria.py
│   ├── seed_reason_codes.py
│   ├── seed_formulas.py
│   ├── seed_ecoinvent.py
│   └── seed_all.py
├── tests/                  # Test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_formulas.py
│   └── test_workflow.py
├── templates/              # Email templates
│   └── emails/
├── app.py                  # Main application
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Docker (optional, for containerized deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ghg-sustainability-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

5. **Initialize database**
   ```bash
   # Run migrations
   alembic upgrade head

   # Seed reference data
   python scripts/seed_all.py
   ```

6. **Run application**
   ```bash
   streamlit run app.py
   ```

   Access at: http://localhost:8501

### Docker Deployment

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with production settings
   ```

2. **Build and run**
   ```bash
   docker-compose up -d
   ```

3. **Initialize database** (first time only)
   ```bash
   docker-compose exec app alembic upgrade head
   docker-compose exec app python scripts/seed_all.py
   ```

4. **Access application**
   - Application: http://localhost:8501
   - PostgreSQL: localhost:5432

## Usage

### Default Users

After seeding, the following test users are available:

| Username | Password | Role | Level | Permissions |
|----------|----------|------|-------|-------------|
| user_l1 | password123 | L1 | Data Entry | Create projects, enter activity data, upload evidence |
| user_l2 | password123 | L2 | Calculation | Search emission factors, perform calculations |
| user_l3 | password123 | L3 | Review | Review calculations, approve/reject with reason codes |
| user_l4 | password123 | L4 | Approval | View aggregates, lock projects, export reports |

**⚠️ Change these passwords in production!**

### Workflow States

```
DRAFT → SUBMITTED → UNDER_CALCULATION → PENDING_REVIEW
                                              ↓
                                          APPROVED → LOCKED
                                              ↓
                                          REJECTED → SUBMITTED (resubmit)
```

### Role Permissions

| Transition | From | To | Role |
|------------|------|-----|------|
| Submit | DRAFT | SUBMITTED | L1 |
| Start Calculation | SUBMITTED | UNDER_CALCULATION | L2 |
| Complete Calculation | UNDER_CALCULATION | PENDING_REVIEW | L2 |
| Approve | PENDING_REVIEW | APPROVED | L3 |
| Reject | PENDING_REVIEW | REJECTED | L3 |
| Resubmit | REJECTED | SUBMITTED | L1 |
| Lock | APPROVED | LOCKED | L4 |

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ghg_db

# Application
APP_NAME=GHG Sustainability Reporting System
SECRET_KEY=your-secret-key-here
DEBUG=False

# SMTP (for email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourcompany.com
SMTP_USE_TLS=True

# File Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10

# Email Templates
EMAIL_TEMPLATES_DIR=./templates/emails
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=models

# Run specific test file
pytest tests/test_formulas.py

# Verbose output
pytest -v
```

## API Documentation

### Formula Engine

The core calculation engine supports multiple emission calculation methods:

#### Standard Emissions Calculation
```python
from core.formulas import FormulaEngine

result = FormulaEngine.calculate_emissions(
    activity_data=100.0,      # Quantity of activity
    emission_factor=2.68,      # kgCO2e per unit
    gwp=1.0,                   # Global Warming Potential
    unit_conversion=1.0        # Unit conversion factor
)
# Returns: {'emissions_tco2e': 0.268, 'emissions_kg': 268.0, ...}
```

#### Scope-Specific Calculations
```python
# Scope 1: Stationary Combustion
result = FormulaEngine.calculate_scope1_stationary_combustion(
    fuel_quantity=1000.0,
    fuel_type="Diesel",
    emission_factor=2.68,
    ncv=36.0
)

# Scope 2: Electricity
result = FormulaEngine.calculate_scope2_electricity(
    electricity_kwh=10000.0,
    grid_emission_factor=0.5,
    location="USA"
)

# Scope 3: Transportation
result = FormulaEngine.calculate_scope3_transport(
    distance_km=500.0,
    transport_mode="Truck",
    emission_factor=0.062,
    weight_tonnes=10.0
)
```

### Workflow Manager

Manage project lifecycle:

```python
from core.workflow import WorkflowManager

# Check if transition is allowed
can_transition, message = WorkflowManager.can_transition(
    from_status="DRAFT",
    to_status="SUBMITTED",
    user_role="L1"
)

# Perform transition
if can_transition:
    WorkflowManager.transition(
        db=db_session,
        project=project,
        new_status="SUBMITTED",
        user_id=user.id,
        user_role=user.role,
        comments="Optional comments"
    )
```

## Database Schema

### Key Tables

- **users**: User accounts with roles (L1-L4)
- **projects**: Main project/submission entity
- **criteria**: 23 GHG category master data
- **project_data**: L1 activity data entries
- **calculations**: L2 calculation results with breakdown
- **ecoinvent**: Emission factors database (with pg_trgm search)
- **reviews**: L3 review records with reason codes
- **approvals**: L4 approval records with snapshots
- **audit_logs**: Complete audit trail
- **evidence**: File metadata

### Indexes

Optimized for performance with indexes on:
- User lookup: username, email, role
- Project search: organization, year, status
- Ecoinvent search: GIN index with pg_trgm for full-text search
- Audit queries: project_id, action, created_at

## Maintenance

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

### Backup

PostgreSQL backup:
```bash
docker-compose exec postgres pg_dump -U ghg_user ghg_db > backup_$(date +%Y%m%d).sql
```

Restore:
```bash
docker-compose exec -T postgres psql -U ghg_user ghg_db < backup_YYYYMMDD.sql
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env
   - Ensure database exists

2. **Email notifications not sending**
   - Verify SMTP credentials
   - Check SMTP_USE_TLS setting
   - Gmail: Use app-specific password

3. **File upload errors**
   - Check UPLOAD_DIR permissions
   - Verify MAX_UPLOAD_SIZE_MB setting
   - Ensure disk space available

4. **Search not working**
   - Verify pg_trgm extension is installed
   - Check GIN index on ecoinvent.search_text
   - Run: `CREATE EXTENSION IF NOT EXISTS pg_trgm;`

## Security Considerations

- ✅ Passwords hashed with bcrypt
- ✅ Role-based access control enforced
- ✅ SQL injection protected (SQLAlchemy ORM)
- ✅ File upload validation (type, size)
- ✅ Audit trail for compliance
- ⚠️ Change default passwords in production
- ⚠️ Use HTTPS in production
- ⚠️ Configure firewall rules
- ⚠️ Regular security updates

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Email: support@yourcompany.com

## Credits

Built with:
- [Streamlit](https://streamlit.io/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [pytest](https://pytest.org/)

Emission factors based on:
- Ecoinvent v3.9
- GHG Protocol
- IPCC AR6 GWP values
