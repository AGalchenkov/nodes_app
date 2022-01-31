from django.urls import path
from django.contrib.auth.decorators import login_required
from functions.decorators import *

from . import views

app_name = 'nodes'
urlpatterns = [
    path('', views.RackListView.as_view(), name='rack_list'),
    path('nodes/rack_list/', views.RackListView.as_view(), name='rack_list'),
    path('nodes/rack/<int:rack_id>', views.rack, name='rack'),
    path('nodes/rack_to_json/<int:rack_id>', views.rack_to_json, name='rack_to_json'),
    path('nodes/rack/<int:rack_id>/unit_detail/<int:unit_num>', views.unit_detail, name='unit_detail'),
    path('nodes/rack/<int:rack_id>/unit_creat/<int:unit_num>', views.unit_create, name='unit_create'),
    path('nodes/search/', views.search, name='search'),
    path('nodes/csv_view/', views.csv_view, name='csv_view'),
    path('nodes/rack/<int:rack_id>/bs_unit_detail/<int:unit_num>', views.BsUnitDetail, name='bs_unit_detail'),
    path('nodes/rack/create_rack', views.create_rack, name='create_rack'),
    path('nodes/rack/delete_rack/<int:rack_id>', views.delet_rack, name='delete_rack'),
    path('nodes/rack/<int:rack_id>/unit_detail/<int:unit_num>/clear_unit', views.clear_unit, name='clear_unit'),
    path('nodes/rebase_unit/', views.rebase_unit, name='rebase_unit'),
    path('nodes/send_notifi/', views.send_notifi, name='send_notifi'),
]
