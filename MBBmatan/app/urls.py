from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home, profile, toggle_favorite, formula_quiz, quiz_result,
    RegisterView, NoteListView, NoteCreateView, NoteUpdateView, NoteDeleteView,
    chat_home, chat_room, subject_chat, send_message,
    f_f, t_f, t_a, t_g,
    manage_friends, send_friend_request, handle_friend_request,
    remove_friend, start_private_chat, user_profile_view, create_group_chat, notification_list, get_hint,
    mark_notification_read, NoteDetailView,
)

app_name = "app"

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', home, name='home'),
    path('', home, name='home'),
    path('profile/', profile, name='profile'),
    path('toggle-favorite/', toggle_favorite, name='toggle_favorite'),
    path('quiz/', formula_quiz, name='formula_quiz'),
    path('quiz/result/', quiz_result, name='quiz_result'),
    path('notes/', NoteListView.as_view(), name='note_list'),
    path('notes/create/', NoteCreateView.as_view(), name='note_create'),
    path('notes/update/<int:pk>/', NoteUpdateView.as_view(), name='note_update'),
    path('notes/delete/<int:pk>/', NoteDeleteView.as_view(), name='note_delete'),
    path('chat/', chat_home, name='chat_home'),
    path('chat/<int:room_id>/', chat_room, name='chat_room'),
    path('chat/<str:subject>/', subject_chat, name='subject_chat'),
    path('chat/<int:room_id>/send/', send_message, name='send_message'),
    path('formulas/physics/', f_f, name='f_f'),
    path('theory/physics/', t_f, name='t_f'),
    path('theory/algebra/', t_a, name='t_a'),
    path('theory/geometry/', t_g, name='t_g'),
    path('friends/', manage_friends, name='manage_friends'),
    path('friends/send/', send_friend_request, name='send_friend_request'),
    path('friends/<int:request_id>/<str:action>/', handle_friend_request, name='handle_friend_request'),
    path('friends/remove/', remove_friend, name='remove_friend'),
    path('chat/private/<int:user_id>/', start_private_chat, name='start_private_chat'),
    path('profile/<int:user_id>/', user_profile_view, name='user_profile'),
    path('chat/group/create/', create_group_chat, name='create_group_chat'),
    path('notifications/', notification_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('quiz/hint/', get_hint, name='get_hint'),
    path('notes/<int:pk>/', NoteDetailView.as_view(), name='note_detail'),
]