import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecomprj.settings")  # عدل الاسم لو مختلف
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'admin'")
    print("✅ Deleted all admin migrations from django_migrations.")
