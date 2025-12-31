#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║         🚀 GHG App - Local PostgreSQL Setup                         ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check PostgreSQL is running
echo "📋 Step 1/6: Checking PostgreSQL service..."
if pg_isready -q; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL not running. Starting it..."
    brew services start postgresql@14
    sleep 3
    if pg_isready -q; then
        echo "✅ PostgreSQL started successfully"
    else
        echo "❌ Failed to start PostgreSQL"
        echo "Try: brew services restart postgresql@14"
        exit 1
    fi
fi
echo ""

# Step 2: Create database and user
echo "📋 Step 2/6: Creating database..."
psql postgres << 'SQL'
-- Drop if exists (for clean setup)
DROP DATABASE IF EXISTS ghg_db;
DROP USER IF EXISTS ghg_user;

-- Create user and database
CREATE USER ghg_user WITH PASSWORD 'ghg_password';
CREATE DATABASE ghg_db OWNER ghg_user;
GRANT ALL PRIVILEGES ON DATABASE ghg_db TO ghg_user;

\c ghg_db

-- Enable pg_trgm extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

\q
SQL

echo "✅ Database 'ghg_db' created"
echo "✅ User 'ghg_user' created"
echo "✅ pg_trgm extension enabled"
echo ""

# Step 3: Install Python dependencies
echo "📋 Step 3/6: Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt -q
    echo "✅ Python dependencies installed"
else
    echo "⚠️  pip3 not found. Install manually: pip install -r requirements.txt"
fi
echo ""

# Step 4: Run database migrations
echo "📋 Step 4/6: Running database migrations..."
alembic upgrade head
echo "✅ Database schema created"
echo ""

# Step 5: Seed database
echo "📋 Step 5/6: Seeding database with initial data..."
python3 scripts/seed_all.py
echo ""

# Step 6: Done
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║                    ✅ SETUP COMPLETE! ✅                             ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 START THE APP:"
echo "   streamlit run app.py"
echo ""
echo "🌐 THEN OPEN:"
echo "   http://localhost:8501"
echo ""
echo "🔑 LOGIN WITH:"
echo "   Username: user_l1"
echo "   Password: password123"
echo ""
echo "👥 OTHER USERS:"
echo "   L2: user_l2 / password123"
echo "   L3: user_l3 / password123"
echo "   L4: user_l4 / password123"
echo ""
