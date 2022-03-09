import mysite.settings as site_setting
from flask.sessions import session_json_serializer
from hashlib import sha1
from itsdangerous import URLSafeTimedSerializer
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import reverse
import time
from django.core.exceptions import PermissionDenied
import functools
from nodes.models import *
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError

def flask_signer():
    signer = URLSafeTimedSerializer(
            site_setting.SECRET_KEY, salt='cookie-session',
            serializer=session_json_serializer,
            signer_kwargs={'key_derivation': 'hmac', 'digest_method': sha1}
        )
    return signer

def flask_session_required(func):
    def wrapper(request, *args, **kwargs):
        signer = flask_signer()
        try:
            session_data = signer.loads(request.COOKIES['session'])
            try:
                u = User.objects.get(username=session_data['username'])
            except ObjectDoesNotExist:
                first_name = session_data['username'].split(' ')[0]
                last_name = session_data['username'].split(' ')[1]
                is_staff = True if session_data['role'] <= 2 else False
                User(username=session_data['username'], first_name=first_name, last_name=last_name, is_staff=is_staff).save()
                u = User.objects.get(username=session_data['username'])
        except KeyError:
            return HttpResponseRedirect('/login')
        if (int(time.time()) - session_data['login_time']) > 86400:
            return HttpResponseRedirect('/login')
        kwargs.update({'user': u})
        return func(request, **kwargs)
    return wrapper

def flask_permission_required(role=3):
    def actual_decorator(func):
        def wrapper(request, **kwargs):
            signer = flask_signer()
            try:
                session_data = signer.loads(request.COOKIES['session'])
                if session_data['role'] > role:
                    #return HttpResponseForbidden()
                    raise PermissionDenied()
            except KeyError:
                return HttpResponseRedirect('/login')
            return func(request, **kwargs)
        return wrapper
    return actual_decorator

def set_role_context(func):
    def wrapper(request, *args, **kwargs):
        signer = flask_signer()
        try:
            session_data = signer.loads(request.COOKIES['session'])
            kwargs.update({'role': session_data['role']})
            return func(request, *args, **kwargs)
        except KeyError:
            return func(request, **kwargs)
    return wrapper

