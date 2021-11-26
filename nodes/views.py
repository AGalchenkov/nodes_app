from django.shortcuts import render, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views import generic
from django.forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import *
from djqscsv import render_to_csv_response
import csv

class IndexView(generic.ListView):
    model = Racks
    template_name = 'nodes/index.html'

class RackListView(generic.ListView):
    model = Racks
    template_name = 'rack_list/index.html'
    context_object_name = 'r_list'

def index(request):
    return HttpResponse("THIS IS NODES APP!")

def base(request):
    return render(request, 'nodes/base.html')

@login_required
def rack_list(request):
    r_list = Racks.objects.all()
    context = {
        'r_list': r_list
    }
    return render(request, 'rack_list/index.html', context)

@login_required
def rack(request, rack_id):
    units_used = Units.objects.values_list('unit_num', flat=True).filter(in_use=True, rack_id=rack_id)
    u_list = []
    rack = Racks.objects.get(id=rack_id)
    location = rack.__str__().replace('_', ' ')
    u_list = Units.objects.filter(rack=rack)
    u_list = reversed(u_list)
    context = {
        'u_list': u_list,
        'rack': rack,
        'location': location,
        'rack_id': rack_id,
        'units_used': units_used,
    }
    return render(request, 'rack/index.html', context)

@login_required
def unit_detail(request, rack_id, unit_num):
    if Units.objects.get(rack_id=rack_id, unit_num=unit_num).used_by_unit:
        return HttpResponseRedirect(reverse('nodes:rack', args=[rack_id]))
    rack = Racks.objects.get(id=rack_id)
    try:
        unit = Units.objects.get(rack_id=rack_id, unit_num=unit_num)
    except ObjectDoesNotExist:
        unit = Units(rack_id=rack_id, unit_num=unit_num, owner=None)
        unit.save()
    if request.method != 'POST':
        unit_form = UnitForm(instance=unit, initial={'modified_by': unit.modified_by, 'comment': unit.comment})
    else:
        print(f"###########1 Comment:   {request.POST['comment']}")
        if request.POST['comment']:
            if not unit.comment or unit.comment.text != request.POST['comment']:
                c1 = Comments(text=request.POST['comment'], author=request.user, units=unit)
                c1.save()
                unit_form = UnitForm(request=request, instance=unit, data=request.POST, initial={'comment': unit.comment})
            else:
                unit_form = UnitForm(request=request, instance=unit, data=request.POST)
        else:
            #if not unit.comment:
             c1 = Comments(text=None, author=None, units=unit, pub_date=None)
             c1.save()
             unit_form = UnitForm(request=request, instance=unit, data=request.POST, initial={'comment': unit.comment})
            #else:
            #    unit_form = UnitForm(request=request, instance=unit, data=request.POST)
        if unit_form.is_valid():
            unit_form.save()
            return HttpResponseRedirect(reverse('nodes:rack', args=[rack_id]))
    context = {
        'unit': unit,
        'rack_id': rack_id,
        'rack': rack,
        'unit_num': unit_num,
        'form': unit_form,
    }
    return render(request, 'unit_detail/index.html', context)

@login_required
def search(request):
    qs = {}

    form = SearchForm(instance=Units)

    if request.method != 'POST':
        form_without_csv = SearchForm(instance=Units, initial={'sn': '', 'comment': '', 'hostname': '', 'mng_ip': ''})
        form_csv = None
    else:
        qs = Units.objects.all()
        for key, val in request.POST.items():
            if key == 'csrfmiddlewaretoken':
                continue
            if key == 'comment' and val != '':
                qs = qs.filter(comment__text__icontains=val)
                continue
            if key == 'hostname' and val != '':
                qs = qs.filter(hostname__icontains=val)
                continue
            if key == 'has_model':
                if request.POST['has_model'] == '2':
                    qs = qs.filter(model__isnull=False)
                    continue
                elif request.POST['has_model'] == '3':
                    qs = qs.filter(model__isnull=True)
                    continue
                else:
                    continue
            if key == 'is_avaliable':
                if request.POST['is_avaliable'] == '2':
                    qs = qs.filter(is_avaliable=True).filter(model__isnull=False).filter(mng_ip__isnull=False)
                    continue
                elif request.POST['is_avaliable'] == '3':
                    qs = qs.filter(is_avaliable=False).filter(model__isnull=False).filter(mng_ip__isnull=False)
                    continue
                else:
                    continue
            if val:
                qs = qs.filter(**{ key:val })
        print(request.POST)
        sn = request.POST['sn'] if request.POST['sn'] else ''
        mng_ip = request.POST['mng_ip'] if request.POST['mng_ip'] else ''
        hostname = request.POST['hostname'] if request.POST['hostname'] else ''

        print(f"##################### HAS_MODEL:      {request.POST['has_model']}")
        form_without_csv = SearchForm(instance=Units, initial={
            'owner': request.POST['owner'],
            'rack': request.POST['rack'],
            'model': request.POST['model'],
            'vendor': request.POST['vendor'],
            'power': request.POST['power'],
            'vendor_model': request.POST['vendor_model'],
            'sn': sn,
            'mng_ip': mng_ip,
            'hostname': hostname,
            'has_model': request.POST['has_model'],
            'comment': request.POST['comment'],
            'is_avaliable': request.POST['is_avaliable'],
        })

        form_csv = CSVForm(instance=Units, initial={
            'owner': request.POST['owner'],
            'rack': request.POST['rack'],
            'model': request.POST['model'],
            'vendor': request.POST['vendor'],
            'power': request.POST['power'],
            'vendor_model': request.POST['vendor_model'],
            'sn': sn,
            'mng_ip': mng_ip,
            'hostname': hostname,
            'has_model': request.POST['has_model'],
            'comment': request.POST['comment'],
            'is_avaliable': request.POST['is_avaliable'],
            'csv': True,
        })
    context = {
        'form_without_csv': form_without_csv,
        'form_csv': form_csv,
        'qs': qs,
        'request': request,
    }
    return render(request, 'search/index.html', context)

@login_required
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

def csv_view(request):
    print('######## POST:')
    print(request.method)

    qs = Units.objects.all()
    for key, val in request.POST.items():
        if key == 'csrfmiddlewaretoken':
            continue
        if key == 'comment' and val != '':
            qs = qs.filter(comment__text__icontains=val)
            continue
        if key == 'hostname' and val != '':
            qs = qs.filter(hostname__icontains=val)
            continue
        if key == 'has_model':
            if request.POST['has_model'] == '2':
                qs = qs.filter(model__isnull=False)
                continue
            elif request.POST['has_model'] == '3':
                qs = qs.filter(model__isnull=True)
                continue
            else:
                continue
        if key == 'is_avaliable':
            if request.POST['is_avaliable'] == '2':
                qs = qs.filter(is_avaliable=True).filter(model__isnull=False).filter(mng_ip__isnull=False)
                continue
            elif request.POST['is_avaliable'] == '3':
                qs = qs.filter(is_avaliable=False).filter(model__isnull=False).filter(mng_ip__isnull=False)
                continue
            else:
                continue
        if val:
            qs = qs.filter(**{key: val})
    opts = qs.model._meta
    model = qs.model
    #response = HttpResponse(mimetype='text/csv')
    #response['Content-Disposition'] = 'attachment;filename=export.csv'
    #writer = csv.writer(response)
    #field_names = [field.name for field in opts.fields]
    #writer.writerow(field_names)
    #for obj in qs:
    #    writer.writerow([getattr(obj, field) for field in field_names])
    #return response
    return render_to_csv_response(qs)
