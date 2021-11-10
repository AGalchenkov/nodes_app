from django.shortcuts import render, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views import generic
from django.forms import *

from .models import *

class IndexView(generic.ListView):
    model = Racks
    template_name = 'nodes/index.html'

class RackListView(generic.ListView):
    model = Racks
    template_name = 'rack_list/index.html'
    context_object_name = 'r_list'

def index(request):
    return HttpResponse("THIS IS NODES APP!")

def rack_list(request):
    r_list = Racks.objects.all()
    context = {
        'r_list': r_list
    }
    return render(request, 'rack_list/index.html', context)

def rack(request, rack_id):
    units_used = Units.objects.values_list('unit_num', flat=True).filter(in_use=True,rack_id=rack_id)
    u_list = []
    rack = Racks.objects.filter(id=rack_id)
    location = rack[0].__str__().replace('_', ' ')
    units = [i for i in range(1,rack[0].units_num+1)]
    for item in units:
        try:
            u_item = Units.objects.get(rack_id=rack_id, unit_num=item)
            hostname = f'@{u_item.hostname}' if u_item.hostname else ''
            if u_item.model:
                u_list.append({
                    'created': True,
                    'unit_num': item,
                    'model': u_item.model,
                    'owner': u_item.owner,
                    'units_takes': u_item.model.units_takes,
                    'comment': u_item.comments,
                    'hostname': hostname,
                })
            else:
                u_list.append({
                    'created': True,
                    'unit_num': item,
                    'model': u_item.model,
                    'owner': u_item.owner,
                    'comment': u_item.comments,
                    'hostname': hostname,
                })
        except ObjectDoesNotExist:
            hostname = ''
            u_list.append({
                'created': False,
                'unit_num': item,
                'model': 'empty',
                'owner': '',
                'comment': '',
                'hostname': hostname,
            })
    context = {
        'u_list': u_list,
        'rack': rack,
        'location': location,
        'rack_id': rack_id,
        'units_used': units_used,
    }
    return render(request, 'rack/index.html', context)

def unit_detail(request, rack_id, unit_num):
    rack = Racks.objects.get(id=rack_id)
    try:
        unit = Units.objects.get(rack_id=rack_id, unit_num=unit_num)
    except ObjectDoesNotExist:
        unit = Units(rack_id=rack_id, unit_num=unit_num, owner=None)
        unit.save()
    try:
        comments = Comments.objects.get(unit=unit)
    except ObjectDoesNotExist:
        comments = Comments(unit=unit, text='')
        comments.save()
    if request.method != 'POST':
        unit_form = UnitForm(instance=unit)
    else:
        comments.text = request.POST['comment']
        unit_form = UnitForm(instance=unit, data=request.POST)
        comment_form = CommentForm(instance=comments, data=comments.__dict__)
        if unit_form.is_valid() and comment_form.is_valid():
            unit_form.save()
            comment_form.save()
            return HttpResponseRedirect(reverse('nodes:rack', args=[rack_id]))
    context = {
        'unit': unit,
        'rack_id': rack_id,
        'rack': rack,
        'unit_num': unit_num,
        'form': unit_form,
    }
    return render(request, 'unit_detail/index.html', context)

def unit_create(request, rack_id, unit_num):
    rack = Racks.objects.get(id=rack_id)
    form = UnitCreateForm(instance=Units, initial={
        'unit_num': unit_num,
        'rack': rack,
        'hostname': '',
        'sn': '',
        'mng_ip': '',
        'in_use': False,
    })
    context = {
        'form': form,
        'rack_id': rack_id,
        'unit_num': unit_num
    }
    return render(request, 'unit_create/index.html', context)
