#!/usr/bin/env python3
"""
MayDay Platform Quick Setup Script
Run this from D:\mayday\patient-platform\backend to finish deployment setup.
"""

import os
import sys
from dotenv import load_dotenv

def check_env_file():
    """Check if .env.local exists and has required keys."""
    if not os.path.exists(".env.local"):
        print("❌ .env.local not found in current directory")
        return False
    
    load_dotenv(".env.local")
    
    required_keys = ["APP_API_KEY", "MONGO_DB_NAME"]
    missing = []
    
    mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
    if not mongo_uri:
        missing.append("MONGODB_URI or MONGO_URI")

    for key in required_keys:
        val = os.getenv(key)
        if not val or "YOUR_" in val or val == "replace_with_very_long_random_key_1234567890":
            missing.append(key)
    
    if missing:
        print(f"⚠️  These env vars are still placeholders or missing: {', '.join(missing)}")
        print(f"\n📝 Edit .env.local and replace placeholder values with real ones.")
        return False
    
    print("✅ .env.local has all required keys with real values")
    return True

def test_mongo_connection():
    """Test MongoDB connection."""
    try:
        from pymongo import MongoClient
        load_dotenv(".env.local")
        uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
        
        if not uri:
            print("❌ MONGODB_URI/MONGO_URI not set")
            return False
        
        print("🔄 Testing MongoDB connection (timeout: 5s)...")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        result = client.admin.command('ping')
        print(f"✅ MongoDB connection successful: {result}")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\n💡 Fix: Check MongoDB Atlas URI and Network Access settings")
        return False

def test_fastapi_import():
    """Test if FastAPI app imports correctly."""
    try:
        sys.path.insert(0, os.getcwd())
        from app.main import app
        print(f"✅ FastAPI app imported successfully ({len(app.routes)} routes)")
        return True
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        return False

def print_next_steps():
    """Print next steps."""
    print("\n" + "="*60)
    print("🚀 NEXT STEPS")
    print("="*60)
    print("""
1. Run backend locally:
   cd D:\mayday\patient-platform\backend
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

2. Verify in browser:
   http://127.0.0.1:8000/docs

3. Make public (ngrok):
   ngrok http 8000

4. Copy ngrok URL and update doctor app .env.local

5. Run doctor app:
   cd "D:\doctor side app\MediScribe-AI-main"
   npm install
   npm run dev

6. Test from doctor app at http://localhost:3000
""")

def main():
    print("="*60)
    print("📦 MayDay Platform Setup Verification")
    print("="*60 + "\n")
    
    all_ok = True
    
    # Check env file
    if not check_env_file():
        all_ok = False
    print()
    
    # Test Mongo connection
    if not test_mongo_connection():
        all_ok = False
    print()
    
    # Test FastAPI import
    if not test_fastapi_import():
        all_ok = False
    print()
    
    if all_ok:
        print("✅ ALL CHECKS PASSED - Ready for deployment!")
        print_next_steps()
        return 0
    else:
        print("⚠️  Some checks failed - see above for fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())
