"""
Vercel Python Serverless Function Entrypoint for Annapurna Telugu Food Scanner.
Exposes the FastAPI `app` instance from `../app.py`.
"""

import pathlib
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import app  # noqa: E402, F401
