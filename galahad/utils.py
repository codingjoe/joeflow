import types


def get_processes() -> types.GeneratorType:
    """Return all registered processes."""
    from django.apps import apps
    from .models import Process

    apps.check_models_ready()
    for model in apps.get_models():
        if issubclass(model, Process) and model is not Process:
            yield model
