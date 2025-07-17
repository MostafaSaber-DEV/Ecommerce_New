# create_superuser.py

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecomprj.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# عدل البيانات حسب رغبتك
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@gmail.com", "admin123")
    print("Superuser created ✅")
else:
    print("Superuser already exists.")
