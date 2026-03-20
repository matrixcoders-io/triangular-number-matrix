"""
api/routes/files.py

File browser blueprint — file listing, size/digit-count, preview, download.
Implemented in Phase 2.
"""

from flask import Blueprint

files_bp = Blueprint("files", __name__)
