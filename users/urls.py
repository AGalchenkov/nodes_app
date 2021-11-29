from django.conf.urls import url
from django.urls import reverse_lazy, path
from django.contrib.auth.views import LoginView, PasswordChangeView, LogoutView
from . import views
from django.conf import settings

app_name='users'
urlpatterns = [
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path(r'^password_change/$', PasswordChangeView.as_view(success_url=reverse_lazy('users:profile'),template_name='users/password_change.html'), name='password_change'),
    path('password_change_done/', views.password_change_done, name='password_change_done'),
    path('profile/', views.profile, name='profile'),
    path('logout/', LogoutView.as_view(), {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
]
