from django.urls import path

from . import views

app_name = 'nodes'
urlpatterns = [
    #path('', views.IndexView.as_view(), name='index'),
    path('', views.RackListView.as_view(), name='rack_list'),
    path('rack/<int:rack_id>', views.rack, name='rack'),
    path('rack/<int:rack_id>/unit_detail/<int:unit_num>', views.unit_detail, name='unit_detail'),
    path('rack/<int:rack_id>/unit_creat/<int:unit_num>', views.unit_create, name='unit_create'),
]
