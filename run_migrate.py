# run_migrate.py

import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecomprj.settings')
django.setup()
call_command('migrate')
