from django.contrib import admin

from galahad.admin import ProcessAdmin
from . import models

admin.site.register(models.SimpleProcess, ProcessAdmin)
admin.site.register(models.SplitJoinProcess, ProcessAdmin)
admin.site.register(models.LoopProcess, ProcessAdmin)
