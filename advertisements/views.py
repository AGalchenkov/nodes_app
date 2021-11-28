from django.shortcuts import render, reverse
from .models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import ImageField

import os


# Create your views here.

def create_adv(request):
    adv = Advertisments.objects.all()
    if request.method != 'POST':
        create_adv_form = CreateAdvertisment(instance=None, initial={'text': '', 'expired_date': None})
    else:
        file = request.FILES['image']
        location = str(settings.MEDIA_ROOT) + '/adv_images'
        url = str(settings.MEDIA_URL) + 'adv_images/'
        print(f'URL ::: {url}    ;  LOCATION  :::  {location}')
        fs = FileSystemStorage(location=location, base_url=url)
        filename = fs.save(file.name, file, base_url=url)
        print(f'URL     ::::::;    {fs.url(filename)}')
        create_adv_form = CreateAdvertisment(request=request, instance=None, data=request.POST, initial={'author_id': request.user.id, 'image': filename})
        #create_adv_form = CreateAdvertisment(request.POST, request.FILES)
        if create_adv_form.is_valid():
            create_adv_form.save()
            return HttpResponseRedirect(reverse('adv:advs'))

    context = {
        'form': create_adv_form
    }

    return render(request, 'create_adv/index.html', context)

def advs(request):
    advs = Advertisments.objects.all()
    advs = reversed(advs)

    context = {
        'advs': advs
    }

    return render(request, 'advertisements/index.html', context)

def adv_detail(request, adv_id):
    adv = Advertisments.objects.get(id=adv_id)
    context = {
        'adv': adv
    }

    return render(request, 'adv_detail/index.html', context)
