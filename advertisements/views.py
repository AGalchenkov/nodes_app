from django.shortcuts import render, reverse
from .models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import ImageField
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib import messages

import os


# Create your views here.

@permission_required('advertisements.can_create_adv', raise_exception=True)
@login_required
def create_adv(request):
    adv = Advertisments.objects.all()
    if request.method != 'POST':
        create_adv_form = CreateAdvertisment(instance=None, initial={'text': '', 'expired_date': None})
    else:
        if request.FILES:
            file = request.FILES['image']
            fs = FileSystemStorage()
            filename = fs.save('adv_app###'+file.name, file)
            create_adv_form = CreateAdvertisment(
                request=request, instance=None, data=request.POST,
                initial={'author_id': request.user.id, 'image': filename}
            )
        else:
            create_adv_form = CreateAdvertisment(
                request=request, instance=None, data=request.POST,
                initial={'author_id': request.user.id}
            )
        if create_adv_form.is_valid():
            create_adv_form.save()
            return HttpResponseRedirect(reverse('adv:advs'))

    context = {
        'form': create_adv_form
    }

    return render(request, 'create_adv/index.html', context)

@login_required
def advs(request):
    advs = Advertisments.objects.all()
    advs = reversed(advs)

    context = {
        'advs': advs
    }

    return render(request, 'advertisements/index.html', context)

@login_required
def adv_detail(request, adv_id):
    adv = Advertisments.objects.get(id=adv_id)
    context = {
        'adv': adv
    }

    return render(request, 'adv_detail/index.html', context)

@login_required
def adv_edit(request, adv_id):
    adv = Advertisments.objects.get(id=adv_id)
    if request.method != 'POST':
        edit_adv_form = CreateAdvertisment(instance=adv, initial={'text': adv.text})
    else:
        if request.FILES:
            file = request.FILES['image']
            fs = FileSystemStorage()
            filename = fs.save('adv_app###'+file.name, file)
            edit_adv_form = CreateAdvertisment(
                request=request, instance=adv, data=request.POST,
                initial={'author_id': request.user.id, 'image': filename}
            )
        else:
            edit_adv_form = CreateAdvertisment(
                request=request, instance=adv, data=request.POST, initial={'author_id': request.user.id}
            )
        if edit_adv_form.is_valid():
            edit_adv_form.save()
            messages.success(request, 'DONE!')
            return HttpResponseRedirect(reverse('adv:adv_detail', args=[adv_id]))
    context = {
        'form': edit_adv_form,
        'adv': adv,
    }
    return render(request, 'adv_edit/index.html', context)

@login_required
def adv_del(request, adv_id):
    adv = Advertisments.objects.get(id=adv_id)
    adv.delete()
    return HttpResponseRedirect(reverse('adv:advs'))
