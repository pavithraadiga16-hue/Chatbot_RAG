"""
PhinsIQ Seed Script Runner
==========================
Delegates to seed.py in the workspace root.
"""
import sys
import os

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from seed import main

if __name__ == "__main__":
    main()
