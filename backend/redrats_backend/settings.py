# redrats_backend/settings.py
from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv
from datetime import timedelta
from corsheaders.defaults import default_headers

# Load .env
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "replace-this-with-production-key")
DEBUG = os.getenv("DEBUG", "True").lower() in ["true", "1"]

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# -------------------------
# CORS / allowed headers
# -------------------------
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
# allow the X-Wallet-Key header and usual defaults
CORS_ALLOW_HEADERS = list(default_headers) + ["x-wallet-key"]

# -------------------------
# Sessions & CSRF (dev)
# -------------------------
SESSION_COOKIE_SAMESITE = None   # allow cross-site cookies for local dev
SESSION_COOKIE_SECURE = False    # HTTP local dev
CSRF_COOKIE_SAMESITE = None
CSRF_COOKIE_SECURE = False
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 3600
SESSION_SAVE_EVERY_REQUEST = True

# -------------------------
# Google OAuth
# -------------------------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/drive/oauth2callback/"
)

# -------------------------
# Avalanche RPC
# -------------------------
AVALANCHE_RPC_URL = os.getenv(
    "AVALANCHE_RPC_URL", "https://api.avax-test.network/ext/bc/C/rpc"
)
AVALANCHE_CHAIN_ID = int(os.getenv("AVALANCHE_CHAIN_ID", 43113))

# -------------------------
# Database
# -------------------------
DATABASES = {"default": dj_database_url.config(default=os.getenv("DATABASE_URL"))}

# -------------------------
# Installed apps
# -------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Local apps
    "wallet",
    "users",
    "drive",

    # Third-party
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
]

# -------------------------
# Middleware
# -------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "redrats_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "redrats_backend.wsgi.application"

# -------------------------
# REST Framework & JWT
# -------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",   # enable session cookies
        "users.authentication.GoogleUserJWTAuthentication",       # keep JWT auth
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}



SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
