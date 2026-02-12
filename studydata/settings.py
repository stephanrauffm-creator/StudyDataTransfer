"""Django settings for studydata project."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
CONFIG_PATH = INSTANCE_DIR / "config.json"

load_dotenv(INSTANCE_DIR / ".env")


def _as_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_list(value: object, default: list[str] | None = None) -> list[str]:
    if value is None:
        return default or []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [item.strip() for item in str(value).split(",") if item.strip()]


config_data: dict[str, object] = {}
if CONFIG_PATH.exists():
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)


def get_config(key: str, default: object = None) -> object:
    if key in config_data:
        return config_data[key]
    return os.environ.get(key, default)


SECRET_KEY = str(get_config("SECRET_KEY", "dev-only-change-me"))
DEBUG = _as_bool(get_config("DEBUG", True), True)
ALLOWED_HOSTS = _as_list(get_config("ALLOWED_HOSTS", ["127.0.0.1", "localhost"]))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "study",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "studydata.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "studydata.wsgi.application"

DATABASE_URL = str(get_config("DATABASE_URL", "")).strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

if DATABASE_URL:
    from urllib.parse import urlparse

    parsed = urlparse(DATABASE_URL)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("Only PostgreSQL DATABASE_URL is supported when set.")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": parsed.username or "",
            "PASSWORD": parsed.password or "",
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
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

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_ROOT = Path(str(get_config("MEDIA_ROOT", BASE_DIR / "media")))
MEDIA_URL = "/media/"

LOG_DIR = Path(str(get_config("LOG_DIR", BASE_DIR / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

DATA_XLSX_PATH = str(get_config("DATA_XLSX_PATH", BASE_DIR / "instance" / "study_export.xlsx"))

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "entry-list"
LOGOUT_REDIRECT_URL = "login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "audit_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "audit.log",
        },
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "study.audit": {
            "handlers": ["audit_file", "console"],
            "level": "INFO",
            "propagate": False,
        }
    },
}
