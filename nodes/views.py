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
        account_visitor,
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
@account_visitor
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
@account_visitor
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
@account_visitor
def unit_detail(request, rack_id, unit_num, **kwargs):
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
                unit_form = UnitForm(user=kwargs['user'], request=request, instance=unit, data=request.POST, initial={'comment': unit.comment})
            else:
                unit_form = UnitForm(user=kwargs['user'], request=request, instance=unit, data=request.POST, initial={'comment': unit.comment.text})
        else:
            c1 = Comments(text=None, author=None, units=unit, pub_date=None)
            c1.save()
            unit_form = UnitForm(user=kwargs['user'], request=request, instance=unit, data=request.POST, initial={'comment': unit.comment.text})
        if unit_form.is_valid():
            if unit_form.has_changed():
                unit_form.save()
                messages.success(request, 'Готово')
                return HttpResponseRedirect(reverse('nodes:unit_detail', args=[rack_id, unit_num]))
    context = {
        'unit': unit,
        'rack_id': rack_id,
        'rack': rack,
        'unit_num': unit_num,
        'form': unit_form,
        'role': kwargs['role'],
        'user': kwargs['user'],
    }
    return render(request, 'unit_detail/index.html', context)

#@login_required
@set_role_context
@flask_session_required
@flask_permission_required
@account_visitor
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
        })

        form_csv = SearchForm(instance=Units, initial={
            'owner': request.POST['owner'],
            'rack': request.POST['rack'],
            'model': request.POST['model'],
            'vendor': request.POST['vendor'],
            'power': request.POST['power'],
            'vendor_model': request.POST['vendor_model'],
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
@account_visitor
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
            messages.success(request, 'DONE!')
            return HttpResponseRedirect(reverse('nodes:rack_list'))

    context = {
        'form': form,
    }

    return render(request, 'create_rack/index.html', context)

def csv_view(request, *args, **kwargs):
    qs = Units.objects.all()
    print(f'REQUWSR ITEMS ######### {request.POST}')
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
    messages.success(request, 'DONE!')
    return HttpResponseRedirect(reverse('nodes:rack_list'))

def send_notifi(request):
    payload = {"head": "Welcome to wunderfull peace of WebPush!", "body": "There is a body of webpush message!!!!"}

    send_group_notification(group_name='all', payload=payload, ttl=1000)
    return JsonResponse(status=200, data={"message": "Web push successful"})
