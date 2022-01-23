from django.shortcuts import render, reverse
from django.views import generic
from .models import *
import csv
from django.contrib import messages
from django.http import JsonResponse
from webpush import send_group_notification
from functions.decorators import *
from django.utils.decorators import method_decorator
from django.db.models import Q
import json
import html
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize
from . import views

class IndexView(generic.ListView):
    model = Racks

    def __init__(self):
        self.signer = URLSafeTimedSerializer(
            b'xxx', salt='cookie-session',
            serializer=session_json_serializer,
            signer_kwargs={'key_derivation': 'hmac', 'digest_method': sha1}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.session_data = self.signer.loads(self.request.COOKIES['session'])
        context['cookies'] = self.request.COOKIES
        context['user_data'] = self.session_data
        return context

    template_name = 'root/index.html'

class RackListView(generic.ListView):
    decorators = [
        flask_session_required,
        flask_permission_required,
    ]

    def __init__(self):
       self.signer = flask_signer()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.session_data = self.signer.loads(self.request.COOKIES['session'])
        context['role'] = self.session_data['role']
        return context


    @method_decorator(decorators)
    def dispatch(self, request, *args, **kwargs):

        args = args + (kwargs,)

        return super(RackListView, self).dispatch(request, *args, **kwargs)

    model = Racks
    template_name = 'rack_list/index.html'
    context_object_name = 'r_list'


def index(request):
    return HttpResponse("THIS IS NODES APP!")


#@login_required
@flask_session_required
def rack_list(request):
    r_list = Racks.objects.all().order_by('location')
    context = {
        'r_list': r_list
    }
    return render(request, 'rack_list/index.html', context)

#@login_required
@set_role_context
@flask_session_required
@flask_permission_required
def rack(request, rack_id, **kwargs):
    units_used = Units.objects.values_list('unit_num', flat=True).filter(in_use=True, rack_id=rack_id)
    u_list = []
    rack = Racks.objects.get(id=rack_id)
    location = rack.__str__().replace('_', ' ')
    u_list = Units.objects.filter(rack=rack)
    u_list = reversed(u_list)
    webpush = {"group": 'all' }
    context = {
        'u_list': u_list,
        'rack': rack,
        'location': location,
        'rack_id': rack_id,
        'units_used': units_used,
        'webpush': webpush,
        'role': kwargs['role'],
        'user': kwargs['user'],
    }
    return render(request, 'rack/index.html', context)

#@permission_required('nodes.can_view_unit')
#@login_required
@set_role_context
@flask_session_required
@flask_permission_required
def unit_detail(request, rack_id, unit_num, **kwargs):
    #custom_messages = kwargs.get('messages', None)
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
        if request.POST['comment']:
            if not unit.comment or unit.comment.text != request.POST['comment']:
                c1 = Comments(text=request.POST['comment'], author=kwargs['user'], units=unit)
                c1.save()
                unit_form = UnitForm(user=kwargs['user'], role=kwargs['role'], request=request, instance=unit, data=request.POST, initial={'modified_by': unit.modified_by, 'comment': unit.comment})
            else:
                unit_form = UnitForm(user=kwargs['user'], role=kwargs['role'], request=request, instance=unit, data=request.POST, initial={'comment': unit.comment.text})
        else:
            # c1 = Comments(text=None, author=None, units=unit, pub_date=None)
            # c1.save()
            unit_form = UnitForm(user=kwargs['user'], role=kwargs['role'], request=request, instance=unit, data=request.POST, initial={'comment': None})
        if unit_form.is_valid():
            if unit_form.has_changed():
                unit_form.save()
                messages.success(request, 'Готово')
                return HttpResponseRedirect(reverse('nodes:unit_detail', args=[rack_id, unit_num]))
            else:
                unit_form = UnitForm(user=kwargs['user'], role=kwargs['role'], request=request, instance=unit, initial=unit_form.cleaned_data)
    rebase_form = UnitRebaseForm(instance=unit)
    context = {
        'unit': unit,
        'rack_id': rack_id,
        'rack': rack,
        'unit_num': unit_num,
        'rebase_form': rebase_form,
        'form': unit_form,
        'role': kwargs['role'],
        'user': kwargs['user'],
    }

    return render(request, 'unit_detail/index.html', context)


#@login_required
@set_role_context
@flask_session_required
@flask_permission_required
def search(request, **kwargs):
    qs = {}
    form = SearchForm(instance=Units)
    if request.method != 'POST':
        form_without_csv = SearchForm(instance=Units, initial={'sn': '', 'comment': '', 'hostname': '', 'mng_ip': '', 'ipmi_bmc': ''})
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
            if key == 'has_10G':
                if request.POST['has_10G'] == '2':
                    qs = qs.filter(~Q(g10=0))
                    continue
                elif request.POST['has_10G'] == '3':
                    qs = qs.filter(g10=0)
                    continue
                else:
                    continue
            if key == 'has_40G':
                if request.POST['has_40G'] == '2':
                    qs = qs.filter(~Q(g40=0))
                    continue
                elif request.POST['has_10G'] == '3':
                    qs = qs.filter(g40=0)
                    continue
                else:
                    continue
            if key == 'has_100G':
                if request.POST['has_100G'] == '2':
                    qs = qs.filter(~Q(g100=0))
                    continue
                elif request.POST['has_10G'] == '3':
                    qs = qs.filter(g100=0)
                    continue
                else:
                    continue
            if key == 'has_ipmi':
                if request.POST['has_ipmi'] == '2':
                    qs = qs.filter(has_ipmi=True)
                    continue
                elif request.POST['has_ipmi'] == '3':
                    qs = qs.filter(has_ipmi=False)
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
            if key == 'ipmi_is_avaliable':
                if request.POST['ipmi_is_avaliable'] == '2':
                    qs = qs.filter(ipmi_is_avaliable=True).filter(model__isnull=False).filter(ipmi_bmc__isnull=False)
                    continue
                elif request.POST['ipmi_is_avaliable'] == '3':
                    qs = qs.filter(ipmi_is_avaliable=False).filter(model__isnull=False).filter(ipmi_bmc__isnull=False)
                    continue
                else:
                    continue
            if val:
                qs = qs.filter(**{ key:val })
        sn = request.POST['sn'] if request.POST['sn'] else ''
        mng_ip = request.POST['mng_ip'] if request.POST['mng_ip'] else ''
        hostname = request.POST['hostname'] if request.POST['hostname'] else ''
        ipmi_bmc = request.POST['ipmi_bmc'] if request.POST['ipmi_bmc'] else ''

        form_without_csv = SearchForm(instance=Units, initial={
            'owner': request.POST['owner'],
            'rack': request.POST['rack'],
            'model': request.POST['model'],
            'vendor': request.POST['vendor'],
            'power': request.POST['power'],
            'vendor_model': request.POST['vendor_model'],
            'appliance': request.POST['appliance'],
            'sn': sn,
            'mng_ip': mng_ip,
            'ipmi_bmc': ipmi_bmc,
            'hostname': hostname,
            'has_model': request.POST['has_model'],
            'comment': request.POST['comment'],
            'is_avaliable': request.POST['is_avaliable'],
            'has_10G': request.POST['has_10G'],
            'has_40G': request.POST['has_40G'],
            'has_100G': request.POST['has_100G'],
            'has_ipmi': request.POST['has_ipmi'],
            'ipmi_is_avaliable': request.POST['ipmi_is_avaliable'],
        })

        form_csv = SearchForm(instance=Units, initial={
            'owner': request.POST['owner'],
            'rack': request.POST['rack'],
            'model': request.POST['model'],
            'vendor': request.POST['vendor'],
            'power': request.POST['power'],
            'vendor_model': request.POST['vendor_model'],
            'appliance': request.POST['appliance'],
            'sn': sn,
            'mng_ip': mng_ip,
            'ipmi_bmc': ipmi_bmc,
            'hostname': hostname,
            'has_model': request.POST['has_model'],
            'comment': request.POST['comment'],
            'is_avaliable': request.POST['is_avaliable'],
            'has_10G': request.POST['has_10G'],
            'has_40G': request.POST['has_40G'],
            'has_100G': request.POST['has_100G'],
            'has_ipmi': request.POST['has_ipmi'],
            'ipmi_is_avaliable': request.POST['ipmi_is_avaliable'],
        #    'csv': True,
        })
    context = {
        'form_without_csv': form_without_csv,
        'form_csv': form_csv,
        'qs': qs,
        'request': request,
        'role': kwargs['role'],
        'user': kwargs['user'],
    }
    return render(request, 'search/index.html', context)

#@login_required
@set_role_context
@flask_session_required
@flask_permission_required
def unit_create(request, rack_id, unit_num, **kwargs):
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
        'unit_num': unit_num,
        'role': kwargs['role'],
        'user': kwargs['user'],
    }
    return render(request, 'unit_create/index.html', context)

def create_rack(request):

    if request.method != 'POST':
        form = RackCreateForm(instance=Racks)
    else:
        form = RackCreateForm(instance=None, data=request.POST)
        if form.is_valid():
            rack = form.save(commit=False)
            rack.save()
            units_num = request.POST.get('units_num')
            for i in range(1, int(units_num)+1):
                Units(rack=rack, unit_num=i).save()
            messages.success(request, 'Готово')
            return HttpResponseRedirect(reverse('nodes:rack_list'))

    context = {
        'form': form,
    }

    return render(request, 'create_rack/index.html', context)

def csv_view(request, *args, **kwargs):
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
        if key == 'has_10G':
            if request.POST['has_10G'] == '2':
                qs = qs.filter(~Q(g10=0))
                continue
            elif request.POST['has_10G'] == '3':
                qs = qs.filter(g10=0)
                continue
            else:
                continue
        if key == 'has_40G':
            if request.POST['has_40G'] == '2':
                qs = qs.filter(~Q(g40=0))
                continue
            elif request.POST['has_10G'] == '3':
                qs = qs.filter(g40=0)
                continue
            else:
                continue
        if key == 'has_100G':
            if request.POST['has_100G'] == '2':
                qs = qs.filter(~Q(g100=0))
                continue
            elif request.POST['has_10G'] == '3':
                qs = qs.filter(g100=0)
                continue
            else:
                continue
        if key == 'has_ipmi':
            if request.POST['has_ipmi'] == '2':
                qs = qs.filter(has_ipmi=True)
                continue
            elif request.POST['has_ipmi'] == '3':
                qs = qs.filter(has_ipmi=False)
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
        if key == 'ipmi_is_avaliable':
            if request.POST['ipmi_is_avaliable'] == '2':
                qs = qs.filter(ipmi_is_avaliable=True).filter(model__isnull=False).filter(ipmi_bmc__isnull=False)
                continue
            elif request.POST['ipmi_is_avaliable'] == '3':
                qs = qs.filter(ipmi_is_avaliable=False).filter(model__isnull=False).filter(ipmi_bmc__isnull=False)
                continue
            else:
                continue
        if val:
            qs = qs.filter(**{ key:val })
    opts = qs.model._meta
    model = qs.model
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=export.csv'
    writer = csv.writer(response)
    field_names = [field.name for field in opts.fields]
    writer.writerow(field_names)
    for obj in qs:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response
    #return render_to_csv_response(qs)

def BsUnitDetail(request, rack_id, unit_num):
    unit = Units.objects.get(rack_id=rack_id, unit_num=unit_num)
    ram = unit.appliance.ram if unit.appliance else None
    unit_form = BsUnitForm(instance=unit, initial={
        'comment': unit.comment,
        'model': unit.model,
        'vendor': unit.vendor,
        'power': unit.power,
        'vendor_model': unit.vendor_model,
        'appliance': unit.appliance,
        'ram': ram,
    })
    context = {
        'unit_form': unit_form,
        'unit_num': unit_num,
        'rack_id': rack_id,
    }
    return render(request, 'nodes/bs_unit_detail.html', context)

def delet_rack(request, rack_id):
    Racks.objects.get(id=rack_id).delete()
    messages.success(request, 'Готово')
    return HttpResponseRedirect(reverse('nodes:rack_list'))

def clear_unit(request, rack_id, unit_num):
    rack = Racks.objects.get(id=rack_id)
    unit = Units.objects.get(rack_id=rack_id, unit_num=unit_num)
    if unit.model.units_takes > 1:
        unit_form = UnitForm(instance=unit)
        unit_form.remove_fatboy(unit_num, unit.model, rack)
    unit.owner = None
    unit.in_use = False
    unit.model = None
    unit.ram = None
    unit.vendor = None
    unit.power = None
    unit.vendor_model = None
    unit.appliance = None
    unit.sn = ''
    unit.hostname = ''
    unit.has_ipmi = False
    unit.ipmi_bmc = ''
    unit.mng_ip = ''
    unit.console = None
    unit.g10 = 0
    unit.g40 = 0
    unit.g100 = 0
    unit.comment = None
    unit.save()
    messages.success(request, 'Готово')
    return HttpResponseRedirect(reverse('nodes:unit_detail', args=[rack_id, unit_num]))

def rebase_unit(request, **kwargs):
    print(request.POST)
    json_resp = []
    new_rack_id = request.POST['rack']
    rack = Racks.objects.get(id=new_rack_id)
    new_unit_num = request.POST['unit_num']
    old_rack = Racks.objects.get(rack_id=request.POST['old_rack'])
    old_unit_num = request.POST['old_unit_num']
    unit = Units.objects.get(rack_id=new_rack_id, unit_num=new_unit_num)
    if request.method == 'POST':
        rebase_form = UnitRebaseForm(instance=unit, data=request.POST)
    if rebase_form.is_valid():
        if Units.objects.get(rack_id=new_rack_id, unit_num=new_unit_num).model:
            messages.warning(request, 'Юнит назначения ЗАНЯТ')
            return HttpResponseRedirect(reverse('nodes:unit_detail', args=[old_rack.id, old_unit_num]))
        old_unit = Units.objects.get(rack=old_rack, unit_num=old_unit_num)
        new_unit = Units.objects.get(rack=rack, unit_num=new_unit_num)
        new_unit.owner = old_unit.owner
        new_unit.in_use = old_unit.in_use
        new_unit.model = old_unit.model
        new_unit.ram = old_unit.ram
        new_unit.vendor = old_unit.vendor
        new_unit.power = old_unit.power
        new_unit.vendor_model = old_unit.vendor_model
        new_unit.appliance = old_unit.appliance
        new_unit.sn = old_unit.sn
        new_unit.hostname = old_unit.hostname
        new_unit.has_ipmi = old_unit.has_ipmi
        new_unit.ipmi_bmc = old_unit.ipmi_bmc
        new_unit.mng_ip = old_unit.mng_ip
        new_unit.console = old_unit.console
        new_unit.g10 = old_unit.g10
        new_unit.g40 = old_unit.g40
        new_unit.g100 = old_unit.g100
        new_unit.comment = old_unit.comment
        old_unit.owner = None
        old_unit.in_use = False
        old_unit.model = None
        old_unit.ram = None
        old_unit.vendor = None
        old_unit.power = None
        old_unit.vendor_model = None
        old_unit.appliance = None
        old_unit.sn = ''
        old_unit.hostname = ''
        old_unit.has_ipmi = False
        old_unit.ipmi_bmc = ''
        old_unit.mng_ip = ''
        old_unit.console = None
        old_unit.g10 = 0
        old_unit.g40 = 0
        old_unit.g100 = 0
        old_unit.comment = None
        old_unit.save()
        new_unit.save()
        json_resp.append(
            {
                'messages': {'success': f'Перемещено на {rack.location}#{rack.id} ==> U{new_unit_num}'},
                'result': True,
                'location': reverse('nodes:unit_detail', args=[rack.id, new_unit_num]),
            }
        )
        json_resp = json.dumps(json_resp)
        return HttpResponse(json_resp, content_type='application/json')
    else:
        json_resp.append(
            {
                'messages': {'error': rebase_form.errors.get_json_data(escape_html=False)},
                'result': False,
            }
        )
        json_resp = json.dumps(json_resp)
        return HttpResponse(json_resp, content_type='application/json')

def send_notifi(request):
    payload = {"head": "Welcome to wunderfull peace of WebPush!", "body": "There is a body of webpush message!!!!"}

    send_group_notification(group_name='all', payload=payload, ttl=1000)
    return JsonResponse(status=200, data={"message": "Web push successful"})

@set_role_context
@flask_session_required
@flask_permission_required
def rack_to_json(request, rack_id, **kwargs):
    u = Units.objects.filter(rack_id=rack_id)
    json_resp = []
    green = '<div class="green status"></div>'
    red = '<div class="red status"></div>'
    blue = '<div class="blue status"></div>'
    for e in reversed(u):
        unit_takes = ''
        int = ''
        used_by = 'used_by' if e.used_by_unit else ''
        unit_num = '<span class="in_used">' + str(e.unit_num) + '</span>' if e.in_use else f'<span class="free {used_by}">' + str(e.unit_num) + '</span>'
        hostname = ' (<span class="bold">' + e.hostname + '</span>)' if e.hostname else ''
        if e.model:
            if e.model.units_takes > 1:
                unit_takes = f' (U{e.model.units_takes})'
            model = '<span class="bold">' + e.model.model_name + hostname + unit_takes + '</span>'
        elif e.used_by_unit:
            model = '<span class="used_by">used by U' + e.used_by_unit + '</span>'
        else:
            model = ''
        is_avaliable = e.is_avaliable
        if e.mng_ip:
            if is_avaliable:
                mng_ip = green + e.mng_ip
            else:
                mng_ip = red + e.mng_ip
        else:
            mng_ip = ''
        if e.ipmi_bmc:
            if e.ipmi_is_avaliable:
                ipmi = green + e.ipmi_bmc
            else:
                ipmi = red + e.ipmi_bmc
        elif e.has_ipmi:
                ipmi = blue + '<span class="transp">no ip</span>'
        else:
            ipmi = ''
        owner = e.owner.username if e.owner else ''
        console = '<a class="hover_bold my_lnk" href="ssh://tac@10.212.130.117">' + e.console.console + '</a>' if e.console else ''
        appliance = e.appliance.appliance if e.appliance else ''
        vendor = e.vendor.vendor_name if e.vendor else ''
        vendor_model = e.vendor_model.vendor_model if e.vendor_model else ''
        pwr = e.power.power if e.power else ''
        sn = e.sn if e.sn else ''
        ram = e.appliance.ram if appliance else ''
        if e.comment:
            comment = e.comment.text if e.comment.text else ''
        else:
            comment = ''
        c = f'''
            <ul class="collapsible">
            <li>
            <div class="hover_bold collapsible-header">{comment}</div>
            <div class="collapsible-body collapsible_comment">{comment}</div>
            </li>
            </ul>
        '''
        int += f'{e.g10}<span class="clr_gray">x10G</span>' if e.g10 else ''
        int += f' {e.g40}<span class="clr_gray">x40G</span>' if e.g40 else ''
        int += f' {e.g100}<span class="clr_gray">x100G</span>' if e.g100 else ''
        json_resp.append({
            'unit_num': unit_num, 'model': model, 'is_avaliable': is_avaliable, 'mng_ip': mng_ip,
            'ipmi': ipmi, 'owner': owner, 'appliance': appliance, 'sn': sn, 'ram': ram, 'vendor': vendor,
            'console': console, 'vendor_model': vendor_model, 'pwr': pwr, 'int': int, 'comment': c
            })
    json_resp = json.dumps(json_resp)

    #return JsonResponse(status=200, data=html.unescape(json_resp), safe=False)
    return HttpResponse(json_resp, content_type='application/json')
