import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    from app.core.config import settings
    print(f"GOOGLE_CLIENT_ID: '{settings.GOOGLE_CLIENT_ID}'")
    print(f"GOOGLE_CLIENT_SECRET length: {len(settings.GOOGLE_CLIENT_SECRET) if settings.GOOGLE_CLIENT_SECRET else 0}")
    print(f"GOOGLE_REDIRECT_URI: '{settings.GOOGLE_REDIRECT_URI}'")
except Exception as e:
    print(f"Error loading settings: {e}")
