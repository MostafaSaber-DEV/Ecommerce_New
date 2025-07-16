import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecomprj.settings")  # تأكد من اسم مشروعك هنا
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'admin' AND name = '0001_initial'")
    print("✅ Deleted admin.0001_initial migration from history.")
