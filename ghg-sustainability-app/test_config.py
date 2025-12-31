"""
Quick configuration test
"""
import sys
from pathlib import Path

print("Testing configuration...")
print("=" * 60)

# Test 1: Check .env file exists
env_file = Path(".env")
if env_file.exists():
    print("✅ .env file exists")
    with open(env_file, 'r') as f:
        content = f.read()
        if 'change-this-to-a-random-secret-key' in content:
            print("⚠️  WARNING: SECRET_KEY not updated!")
        else:
            print("✅ SECRET_KEY is configured")
        
        if 'your-email@gmail.com' in content:
            print("ℹ️  Email not configured (optional)")
        else:
            print("✅ Email configured")
else:
    print("❌ .env file not found!")

# Test 2: Check required directories
dirs = ['core', 'models', 'pages', 'scripts', 'tests', 'migrations', 'templates']
for d in dirs:
    if Path(d).exists():
        print(f"✅ {d}/ directory exists")
    else:
        print(f"❌ {d}/ directory missing!")

# Test 3: Check key files
files = ['app.py', 'requirements.txt', 'Dockerfile', 'docker-compose.yml', 'alembic.ini']
for f in files:
    if Path(f).exists():
        print(f"✅ {f} exists")
    else:
        print(f"❌ {f} missing!")

print("=" * 60)
print("\n✅ Configuration test complete!")
print("\nNext step: Choose Docker or Local PostgreSQL (see guide above)")
