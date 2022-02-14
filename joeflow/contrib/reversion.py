from contextlib import contextmanager

from joeflow import utils

__all__ = (
    "register_workflows",
    "RevisionMixin",
    "with_reversion",
    "VersionAdmin",
)


def register_workflows():
    try:
        from reversion import revisions
    except ImportError:
        pass
    else:
        for workflow in utils.get_workflows():
            if not revisions.is_registered(workflow):
                revisions.register(workflow)


@contextmanager
def with_reversion(task):
    try:
        import reversion
    except ImportError:
        yield
    else:
        with reversion.create_revision():
            yield
            reversion.set_comment(task.name)


try:
    import reversion
    from reversion.views import RevisionMixin as _RevisionMixin

    class RevisionMixin(_RevisionMixin):
        def dispatch(self, request, *args, **kwargs):
            if self.revision_request_creates_revision(request):
                reversion.set_comment(self.name)
            return super().dispatch(request, *args, **kwargs)

except ImportError:

    class RevisionMixin:
        pass


try:
    from reversion.admin import VersionAdmin
except ImportError:
    from django.contrib.admin import ModelAdmin as VersionAdmin
