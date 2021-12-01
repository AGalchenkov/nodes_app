from django.shortcuts import render, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views import generic
from django.forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from nodes.models import *

#@login_required
def password_change_done(request):
    return render(request, 'users/password_change_done.html')

def profile(request):
    unit_link_list = []
    user_units = Units.objects.filter(owner=request.user)
    for u in user_units:
        unit_link_list.append({
            'rack_id': u.rack.rack_id,
            'unit_num': u.unit_num,
            'url_text': u,
        })
    context = {
        'user': request.user,
        'user_units': user_units,
        'unit_link_list': unit_link_list,
        'permissions': Permission.objects.filter(group__user=request.user)
    }
    return render(request, 'users/profile.html', context)
