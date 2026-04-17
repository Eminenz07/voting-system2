"""Account URL routes."""
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('admin-register/<str:secret_key>/', views.admin_register, name='admin-register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('me/', views.me, name='me'),
    path('profile/', views.update_profile, name='update-profile'),
]
