from django.urls import path
from .views import (
    home,
    f_f,
    t_a,
    t_g,
    t_f,
    da,
    profile,
    toggle_favorite,
    formula_quiz,
    quiz_result,
    RegisterView,
    CustomLoginView,
    NoteListView,
    NoteCreateView,
    NoteUpdateView,
    NoteDeleteView
)
from django.contrib.auth import views as auth_views

app_name = "app"

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', home, name='home'),
    path('notes/', NoteListView.as_view(), name='note_list'),
    path('notes/create/', NoteCreateView.as_view(), name='note_create'),
    path('notes/update/<int:pk>/', NoteUpdateView.as_view(), name='note_update'),
    path('notes/delete/<int:pk>/', NoteDeleteView.as_view(), name='note_delete'),
    path('f_f/', f_f, name='f_f'),
    path('t_a/', t_a, name='t_a'),
    path('t_g/', t_g, name='t_g'),
    path('t_f/', t_f, name='t_f'),
    path('da/', da, name='da'),
    path('', home, name='home'),
    path('profile/', profile, name='profile'),
    path('toggle-favorite/', toggle_favorite, name='toggle_favorite'),
    path('quiz/', formula_quiz, name='formula_quiz'),
    path('quiz/result/', quiz_result, name='quiz_result'),
]