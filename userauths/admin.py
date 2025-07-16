from django.contrib import admin
from userauths.models import User
# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'bio', 'is_staff')
    search_fields = ('username', 'email')
admin.site.register(User, UserAdmin)   
