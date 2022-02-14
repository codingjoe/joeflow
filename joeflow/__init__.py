"""The lean workflow automation framework for machines with heart."""
import django

if django.VERSION < (3, 2):
    default_app_config = "joeflow.apps.JoeflowConfig"
