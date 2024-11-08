from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('perfil/editar/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
] 