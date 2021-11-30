from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'nodes'
urlpatterns = [
    path('', views.IndexView.as_view(), name='root'),
    path('rack_list/', login_required(views.RackListView.as_view()), name='rack_list'),
    path('rack/<int:rack_id>', views.rack, name='rack'),
    path('rack/<int:rack_id>/unit_detail/<int:unit_num>', views.unit_detail, name='unit_detail'),
    path('rack/<int:rack_id>/unit_creat/<int:unit_num>', views.unit_create, name='unit_create'),
    path('search/', views.search, name='search'),
    path('csv_view/', views.csv_view, name='csv_view'),
    path('rack/<int:rack_id>/bs_unit_detail/<int:unit_num>', views.BsUnitDetail, name='bs_unit_detail'),
]
