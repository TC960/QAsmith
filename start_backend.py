#!/usr/bin/env python3
"""
QAsmith Backend Startup Script
Fixes import issues by setting up proper Python path
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"🚀 STARTUP: Project root: {project_root}")
print(f"🐍 STARTUP: Python path: {sys.path[:3]}...")

# Set environment variables
os.environ['PYTHONPATH'] = str(project_root)

try:
    print("📦 STARTUP: Testing imports...")
    from backend.shared.config import get_config
    from backend.api.main import app
    print("✅ STARTUP: All imports successful!")
    
    # Test config loading
    config = get_config()
    print(f"✅ STARTUP: Config loaded successfully")
    print(f"📊 STARTUP: Neo4j URI: {config.neo4j.uri}")
    
except Exception as e:
    print(f"❌ STARTUP: Import/config error: {e}")
    import traceback
    print(f"🔍 STARTUP: Traceback: {traceback.format_exc()}")
    sys.exit(1)

if __name__ == "__main__":
    import uvicorn
    print("🌐 STARTUP: Starting uvicorn server...")
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root / "backend")]
    )
