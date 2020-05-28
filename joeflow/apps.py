from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as t


class JoeflowConfig(AppConfig):
    name = "joeflow"
    verbose_name = t("Joeflow")

    def ready(self):
        from .contrib.reversion import register_processes

        register_processes()
