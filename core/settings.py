"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 3.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os
import environ
# Build paths inside the project like this: BASE_DIR / 'subdir'.
environ.Env.read_env('django.env') # reading .env file
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("MYSITE_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'django_celery_results',
    'app',
    'celerytasks',
    'emailadmin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Los_Angeles'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_TIMEZONE = "US/Pacific"

environment = os.environ.get("DB")
print("environment "+ environment)
from celery.schedules import crontab


if environment == "prodcluster":
    CELERY_BEAT_SCHEDULE = {
        "process_emails":{
            "task": "process_ticket_emails",
            "schedule": crontab(minute="*/2")
        },
        "send_emails": {
            "task": "send_emails",
            "schedule": crontab(minute="*/2")
        },
        "pagerduty":{
            "task":"pagerduty",
            "schedule": crontab(minute="*/2")
        },
        "request_emails":{
            "task": "request_emails",
            "schedule": crontab(minute="*/2")
        },
        "daily_ticket_report":{
            "task": "daily_tickets_report",
            "schedule": crontab(hour=1, minute=0)
        },
        "nri_email": {
            "task": "nri_email",
            "schedule": crontab(hour=11, minute=1)
        },
        "ninja_one_dump":{
            "task": "ninja_one_dump",
            "schedule": crontab(hour=22, minute=0)
        },
        "idassets":{
            "task": "id_dump",
            "schedule": crontab(hour=22, minute=0)
        },
        "auvik_dump":{
            "task": "auvik_dump",
            "schedule": crontab(hour=22, minute=0)
        },
        "asset_dump": {
            "task": "asset_dump",
            "schedule": crontab(hour=2, minute=0)
        },
        # "access_ticket_provisions": {
        #     "task": "access_ticket_provisions",
        #     "schedule": crontab(minute="*/1")
        # },
        "splunk_cloud_assets": {
            "task": "splunk_cloud_assets",
            "schedule": crontab(hour=8, minute=0)
        },
        "cisa_repot": {
            "task": "cisa_report",
            "schedule": crontab(hour=8, minute=1)
        },
        "clear_temp_s3": {
            "task": "clear_temp_s3",
            "schedule": crontab(hour=11, minute=1)
        },
        "pull_patches": {
            "task": "pull_patches",
            "schedule": crontab(hour=23, minute=0)
        },
        # "sync_okta_groups": {
        #     "task": "sync_okta_groups",
        #     "schedule": crontab(hour=1, minute=0)
        # }
    }
else:
    CELERY_BEAT_SCHEDULE = {
        "pull_patches": {
            "task": "pull_patches",
            "schedule": crontab(hour=1, minute=0)
        },
        "ninja_one_dump":{
            "task": "ninja_one_dump",
            "schedule": crontab(hour=22, minute=0)
        },
        "idassets":{
            "task": "id_dump",
            "schedule": crontab(hour=22, minute=0)
        },
        "auvik_dump":{
            "task": "auvik_dump",
            "schedule": crontab(hour=22, minute=0)
        },
        "asset_dump": {
            "task": "asset_dump",
            "schedule": crontab(hour=2, minute=0)
        },
        "sync_db": {
            "task": "sync_db",
            "schedule": crontab(hour=10, minute=35)
        },
        "sync_okta_groups": {
            "task": "sync_okta_groups",
            "schedule": crontab(hour=1, minute=0)
        }
    }
