"""
WSGI config for gauss project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os
import sys

path = '/home/juanjo/django/gauss_project'
if path not in sys.path:
    sys.path.append(path)

path = '/home/juanjo/django'
if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gauss.settings")
os.environ["DJANGO_SETTINGS_MODULE"] = "gauss_project.gauss.settings"

application = get_wsgi_application()