import secrets
import types


def get_processes() -> types.GeneratorType:
    """Return all registered processes."""
    from django.apps import apps
    from .models import Process

    apps.check_models_ready()
    for model in apps.get_models():
        if issubclass(model, Process) and model is not Process:
            yield model


def jitter():
    """Return a random number between 0 and 1."""
    return secrets.randbelow(5)


def backoff(retries):
    """Return an exponentially growing number limited to 600 plus a random jitter."""
    return min(600, 2 ** retries) + jitter()
