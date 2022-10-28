"""The lean workflow automation framework for machines with heart."""
import django

from . import _version

__version__ = _version.version
VERSION = _version.version_tuple

if django.VERSION < (3, 2):
    default_app_config = "joeflow.apps.JoeflowConfig"
