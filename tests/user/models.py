#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-task
------------

Tests for `django-task` models module.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class TestUser(AbstractUser):
    pass


class Profile(models.Model):
    """
    A real FK to a *different* model than the view's own, purely so
    list_autofilter_choices() has a legitimate reason to call
    get_foreign_queryset() (only exercised when the autofiltered field
    belongs to a model other than the view's own).
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profiles')
    bio = models.CharField(max_length=100, blank=True)
