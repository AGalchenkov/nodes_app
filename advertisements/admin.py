from django.contrib import admin

# Register your models here.
from .models import Advertisments, Tags

admin.site.register(Advertisments)
admin.site.register(Tags)
