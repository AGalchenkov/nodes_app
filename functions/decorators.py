import mysite.settings as site_setting
from flask.sessions import session_json_serializer
from hashlib import sha1
from itsdangerous import URLSafeTimedSerializer
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import reverse
import time
from django.core.exceptions import PermissionDenied
import functools

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
        except KeyError:
            return HttpResponseRedirect('http://127.0.0.1:5000/login')
        if (int(time.time()) - session_data['login_time']) > 86400:
            return HttpResponseRedirect('http://127.0.0.1:5000/login')
        return func(request, **kwargs)
    return wrapper

def flask_permission_required(func):
    def wrapper(request, **kwargs):
        signer = flask_signer()
        session_data = signer.loads(request.COOKIES['session'])
        if session_data['role'] > 3:
            #return HttpResponseForbidden()
            raise PermissionDenied()
        return func(request, **kwargs)
    return wrapper

def set_role_context(func):
    def wrapper(request, *args, **kwargs):
        signer = flask_signer()
        try:
            print(f'PARAMSSSS::::   {args}; {kwargs}')
            session_data = signer.loads(request.COOKIES['session'])
            kwargs.update({'role': session_data['role']})
            return func(request, *args, **kwargs)
        except KeyError:
            return func(request, **kwargs)
    return wrapper
