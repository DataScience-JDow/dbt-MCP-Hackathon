"""
Import fix utility for frontend components
"""
import sys
from pathlib import Path

# Add necessary paths for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
parent_root = project_root.parent

# Add paths to sys.path if not already there
paths_to_add = [str(parent_root), str(project_root)]
for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# Now we can import everything we need
def safe_import(module_path, fallback_path=None):
    """Safely import a module with fallback"""
    try:
        parts = module_path.split('.')
        module = __import__(module_path, fromlist=[parts[-1]])
        return module
    except ImportError:
        if fallback_path:
            try:
                parts = fallback_path.split('.')
                module = __import__(fallback_path, fromlist=[parts[-1]])
                return module
            except ImportError:
                pass
        raise ImportError(f"Could not import {module_path}")

# Export commonly used imports
try:
    from dbt_mcp_hackathon_project.frontend.utils.session_state import *
    from dbt_mcp_hackathon_project.frontend.services.mcp_client import *
except ImportError:
    # Fallback imports
    from utils.session_state import *
    from services.mcp_client import *