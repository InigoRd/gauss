"""gauss URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^gprojects/', views.gprojects, name='gprojects'),
    # url(r'^create_project/', views.create_project, name='create_project'),
    url(r'^gprojects_ajax/', views.gprojects_ajax, name='gprojects_ajax'),
    url(r'^gantt/(?P<gproject_id>[0-9]+)/$', views.gantt),
    url(r'^gantt_ajax/', views.gantt_ajax, name='gantt_ajax')
]
