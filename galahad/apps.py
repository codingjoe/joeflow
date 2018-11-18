from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as t


class GalahadConfig(AppConfig):
    name = 'galahad'
    verbose_name = t('Galahad')

    def ready(self):
        from .contrib.reversion import register_processes
        register_processes()
