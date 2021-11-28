from django.conf.urls import url
from django.urls import reverse_lazy, path
from django.contrib.auth.views import LoginView, PasswordChangeView, LogoutView
from . import views
from django.conf import settings

app_name = 'advertisements'
urlpatterns = [
    path('', views.advs, name='advs'),
    path('create_adv/', views.create_adv, name='create_adv'),
    path('adv_detail/<int:adv_id>', views.adv_detail, name='adv_detail')
]
