from django.contrib import admin
from django.urls import include, path

from . import models, workflows

urlpatterns = [
    path("admin/", admin.site.urls),
    path("shipment/", include(workflows.ShippingWorkflow.urls())),
    path("simple/", include(workflows.SimpleWorkflow.urls())),
    path("assignee/", include(workflows.AssigneeWorkflow.urls())),
    path("gateway/", include(workflows.GatewayWorkflow.urls())),
    path("splitjoin/", include(workflows.SplitJoinWorkflow.urls())),
    path("loop/", include(workflows.LoopWorkflow.urls())),
    path("welcome/", include(models.WelcomeWorkflow.urls())),
]
