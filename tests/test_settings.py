import os

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "77777777777777777777777777777777777777777777777777"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'postgres'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "user",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "ajax_datatable",
]

AUTH_USER_MODEL = "user.TestUser"

SITE_ID = 1

MIDDLEWARE = ()


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
    },
]
