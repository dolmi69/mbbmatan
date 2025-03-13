from django.urls import path
from .views import RegisterView, CustomLoginView, ProfileView, home
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('', ProfileView.as_view(), name='profile'),
    path('home/', home, name='home'),
]