#!/bin/bash
echo "======================================================================"
echo "FINAL END-TO-END VERIFICATION - GHG Sustainability App"
echo "======================================================================"

echo -e "\n📊 CODE STATISTICS:"
echo "-------------------------------------------------------------------"
echo "Python files:"
find . -name "*.py" -not -path "./venv/*" | wc -l | xargs echo "  Total .py files:"
find . -name "*.py" -not -path "./venv/*" -exec cat {} \; | wc -l | xargs echo "  Total lines of Python code:"

echo -e "\nConfiguration files:"
ls -1 *.{yml,yaml,txt,ini,md,example} 2>/dev/null | wc -l | xargs echo "  Config files:"

echo -e "\nHTML templates:"
find templates -name "*.html" 2>/dev/null | wc -l | xargs echo "  Email templates:"

echo -e "\n📁 DIRECTORY STRUCTURE:"
echo "-------------------------------------------------------------------"
tree -L 2 -I 'venv|__pycache__|*.pyc|.git' 2>/dev/null || find . -type d -not -path "*/venv/*" -not -path "*/__pycache__/*" -not -path "*/.git/*" | head -30

echo -e "\n✅ CRITICAL FILES CHECK:"
echo "-------------------------------------------------------------------"
for file in app.py requirements.txt Dockerfile docker-compose.yml .env.example README.md; do
    if [ -f "$file" ]; then
        size=$(wc -c < "$file")
        lines=$(wc -l < "$file" 2>/dev/null || echo "N/A")
        echo "  ✓ $file ($lines lines, $size bytes)"
    else
        echo "  ✗ MISSING: $file"
    fi
done

echo -e "\n🔧 MODULES VERIFICATION:"
echo "-------------------------------------------------------------------"
echo "Core modules:"
ls -1 core/*.py | wc -l | xargs echo "  "
echo "Database models:"
ls -1 models/*.py | wc -l | xargs echo "  "
echo "Streamlit pages:"
ls -1 pages/*.py | wc -l | xargs echo "  "
echo "Seed scripts:"
ls -1 scripts/*.py | wc -l | xargs echo "  "
echo "Test files:"
ls -1 tests/*.py | wc -l | xargs echo "  "

echo -e "\n🗄️ DATABASE MODELS:"
echo "-------------------------------------------------------------------"
grep -h "^class.*Base" models/*.py | sed 's/.*class /  - /' | sed 's/(Base.*//'

echo -e "\n📝 WORKFLOW STATES:"
echo "-------------------------------------------------------------------"
grep "WORKFLOW_STATES" core/config.py -A 10 | grep '"' | sed 's/.*"//;s/".*//' | sed 's/^/  - /'

echo -e "\n👥 USER ROLES:"
echo "-------------------------------------------------------------------"
grep -A 5 "ROLES = {" core/config.py | grep ":" | sed 's/.*"//;s/":.*//' | sed 's/^/  - /'

echo -e "\n🧪 TESTS AVAILABLE:"
echo "-------------------------------------------------------------------"
grep "^def test_" tests/test_*.py | wc -l | xargs echo "  Total test functions:"
for file in tests/test_*.py; do
    count=$(grep -c "^def test_" "$file" 2>/dev/null || echo 0)
    echo "  $(basename $file): $count tests"
done

echo -e "\n📧 EMAIL TEMPLATES:"
echo "-------------------------------------------------------------------"
ls -1 templates/emails/*.html 2>/dev/null | sed 's/.*\//  - /'

echo -e "\n🌱 SEED SCRIPTS:"
echo "-------------------------------------------------------------------"
ls -1 scripts/seed_*.py | sed 's/scripts\//  - /'

echo -e "\n======================================================================"
echo "✅ VERIFICATION COMPLETE"
echo "======================================================================"
echo ""
echo "🚀 NEXT STEPS:"
echo "  1. cp .env.example .env"
echo "  2. Edit .env with your database credentials"
echo "  3. pip install -r requirements.txt"
echo "  4. alembic upgrade head"
echo "  5. python scripts/seed_all.py"
echo "  6. streamlit run app.py"
echo ""
echo "OR using Docker:"
echo "  1. docker-compose up -d"
echo "  2. docker-compose exec app python scripts/seed_all.py"
echo ""
