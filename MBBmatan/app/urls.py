from django.urls import path
from .views import RegisterView, CustomLoginView, ProfileView, home, f_f, t_a, t_f, t_g
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from . import views

app_name = "app"

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('', ProfileView.as_view(), name='profile'),
    path('home/', home, name='home'),
    path("notes/", views.NoteListView.as_view(), name="note_list"),
    path("notes/create/", views.NoteCreateView.as_view(), name="note_create"),
    path("notes/update/<int:pk>/", views.NoteUpdateView.as_view(), name="note_update"),
    path("notes/delete/<int:pk>/", views.NoteDeleteView.as_view(), name="note_delete"),
    path('f_f/', f_f, name='f_f'),
    path('t_a/', t_a, name='t_a'),
    path('t_g/', t_g, name='t_g'),
    path('t_f/', t_f, name='t_f'),
]
