import sys
import os

# Add backend directory to path so imports work
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
backend_dir = os.path.abspath(backend_dir)
sys.path.insert(0, backend_dir)

# Change cwd so config.py finds .env (if present) and relative paths resolve
os.chdir(backend_dir)

from main import app  # noqa: E402 — must be after path setup
