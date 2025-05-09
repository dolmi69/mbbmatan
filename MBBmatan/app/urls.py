from django.urls import path
from .views import RegisterView, CustomLoginView, home, f_f, t_a, t_f, t_g, da
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from . import views
from .views import toggle_favorite, profile
from .views import formula_quiz


app_name = "app"

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', home, name='home'),
    path("notes/", views.NoteListView.as_view(), name="note_list"),
    path("notes/create/", views.NoteCreateView.as_view(), name="note_create"),
    path("notes/update/<int:pk>/", views.NoteUpdateView.as_view(), name="note_update"),
    path("notes/delete/<int:pk>/", views.NoteDeleteView.as_view(), name="note_delete"),
    path('f_f/', f_f, name='f_f'),
    path('t_a/', t_a, name='t_a'),
    path('t_g/', t_g, name='t_g'),
    path('t_f/', t_f, name='t_f'),
    path('da/', da, name='da'),
    path('', home, name='home'),
    path('profile/', profile, name='profile'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('physics/', views.physics_formulas, name='physics_formulas'),
    path('quiz/', views.formula_quiz, name='formula_quiz'),

]
