from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile, name='profile'),           # ← добавь
    path('leaderboard/', views.leaderboard, name='leaderboard'), # ← добавь
    path('vpn/download/', views.download_vpn_config, name='download_vpn_config'),
    ]
