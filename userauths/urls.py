from django.urls import path
from userauths.views import login_view, register_view , logout_view

app_name = 'userauths'

urlpatterns = [
    path('signup/', register_view, name='register_view'),
    path('signin/', login_view, name='login_view'),
    path('logout/<pk>/', logout_view, name='logout_view'),
]
