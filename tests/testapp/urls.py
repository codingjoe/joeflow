"""testapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

import tests.testapp.models


urlpatterns = [
    path('admin/', admin.site.urls),
    path('simple/', include(tests.testapp.models.SimpleProcess.urls())),
    path('gateway/', include(tests.testapp.models.GatewayProcess.urls())),
    path('splitjoin/', include(tests.testapp.models.SplitJoinProcess.urls())),
    path('loop/', include(tests.testapp.models.LoopProcess.urls())),
    path('welcome/', include(tests.testapp.models.WelcomeProcess.urls()))
]
