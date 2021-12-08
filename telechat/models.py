from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Chat(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


