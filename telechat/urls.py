from django.urls import path
from django.urls import reverse_lazy, path
from django.contrib.auth.views import LoginView, PasswordChangeView, LogoutView
from . import views
from django.conf import settings
from django.contrib.auth.decorators import login_required

app_name = 'telechat'
urlpatterns = [
    path('chats/', login_required(views.ChatsListView.as_view()), name='chats'),
    path('chat/<int:chat_id>', views.chat_detail, name='chat_detail'),

]
