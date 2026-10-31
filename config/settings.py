import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in {"1", "true", "yes", "on"}
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-change-me"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured when DEBUG is disabled.")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    "http://10.90.0.3:8000",
    "https://ngundu.kelvonix.net",
]

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "academics",
    "grades",
    "fees",
    "library",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "config.context_processors.school_profile",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "student_portal_db"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Harare"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "school_site" / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "accounts:login"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

PAYNOW_INTEGRATION_ID = os.getenv("PAYNOW_INTEGRATION_ID", "")
PAYNOW_INTEGRATION_KEY = os.getenv("PAYNOW_INTEGRATION_KEY", "")
PAYNOW_AUTH_EMAIL = os.getenv("PAYNOW_AUTH_EMAIL", "samuelfifitini0@gmail.com")
PAYNOW_RETURN_URL = os.getenv("PAYNOW_RETURN_URL", "")
PAYNOW_RESULT_URL = os.getenv("PAYNOW_RESULT_URL", "")
ECOCASH_RECEIVER_NAME = os.getenv("ECOCASH_RECEIVER_NAME", "Samuel Owen Fifitini")
ECOCASH_RECEIVER_PHONE = os.getenv("ECOCASH_RECEIVER_PHONE", "+263782649111")
PAYMENTS_DEMO_MODE = os.getenv(
    "PAYMENTS_DEMO_MODE", "true" if DEBUG else "false"
).lower() in {"1", "true", "yes", "on"}

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

JAZZMIN_SETTINGS = {
    "site_logo": "school_site/images/school-crest.webp",
    "login_logo": "school_site/images/school-crest.webp",
    "login_logo_dark": "school_site/images/school-crest.webp",
    "site_logo_classes": "img-circle",
    "site_icon": "school_site/images/school-crest.webp",
    "topmenu_links": [
        {"name": "Back to School Website", "url": "/", "new_window": False, "icon": "fas fa-home"},
        {"name": "Student Portal Login", "url": "/login/", "new_window": False, "icon": "fas fa-sign-in-alt"},
    ],
    "usermenu_links": [
        {"name": "Back to School Website", "url": "/", "new_window": False, "icon": "fas fa-globe"},
    ],
    "custom_links": {"fees": [{"name": "Fees Overview", "url": "fees:overview", "icon": "fas fa-chart-line", "permissions": ["fees.view_termfee"]}]},
    "site_title": "Ngundu Halt School Admin",
    "site_header": "Ngundu Halt Government High School",
    "site_brand": "NGUNDU HALT",
    "welcome_sign": "Welcome, Ngundu Halt Staff",
    "copyright": "Student Academic Portal",
    "show_ui_builder": False,
    "show_version": False,
    "custom_css": "school_site/css/jazzmin_custom_v2.css",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-warning",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-warning",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
}

# Redirect Django admin logout directly to the admin login page.
LOGOUT_REDIRECT_URL = "/admin/login/"
