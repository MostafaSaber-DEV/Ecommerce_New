import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecomprj1.settings")  # غيّر الاسم لو settings.py في مسار مختلف

import django
django.setup()

from django.core.management import call_command
call_command("migrate")
