from django.urls import path
from .views import RegisterView, CustomLoginView, ProfileView, home
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('', ProfileView.as_view(), name='profile'),
    path('home/', home, name='home'),
]