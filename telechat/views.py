from django.shortcuts import render
from .models import *
from django.views import generic
from telethon import TelegramClient, events, sync
import asyncio
import re
from django.db import close_old_connections
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.images import get_image_dimensions
from PIL import Image
import random


class ChatsListView(generic.ListView):
    model = Chat
    template_name = 'chats/index.html'
    context_object_name = 'c_list'

def chat_detail(request, chat_id):
    api_id = 11821981
    api_hash = '4fa5dde61b5172461ec011169cb02420'
    chat = Chat.objects.get(id=chat_id)
    chat = chat.name

    limit = 50
    users = {}
    msg = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient('test_session', api_id, api_hash, loop=loop)

    client.start()
    client.get_dialogs()
    for partic in client.iter_participants(chat):
        lastname = partic.last_name if partic.last_name else ""
        firstname = partic.first_name if partic.first_name else ""
        r = lambda: random.randint(0,150)
        g = lambda: random.randint(0,150)
        b = lambda: random.randint(0,150)
        color = '#%02X%02X%02X' % (r(),g(),b())
        users[partic.id] = {'name': firstname + " " + lastname, 'color': color}
    for message in client.iter_messages(chat, limit=limit):
        id = message.from_id.user_id
        try:
            if message.media:
                media_link = f'/telechat/{chat}/{message.id}'
                if not default_storage.exists(str(settings.MEDIA_ROOT) + media_link + '.jpg'):
                    med = client.download_media(message.media, str(settings.MEDIA_ROOT) + media_link)
                w, h = get_image_dimensions(str(settings.MEDIA_ROOT) + media_link + '.jpg')
                if h > 240:
                    msg.append(f'<span style="color:gray; display:block">{message.date.replace(microsecond=0, tzinfo=None)}</span> <b style="color: {users[id]["color"]}">{users[id]["name"]} :: </b><img src="{media_link}.jpg" width="320" height="240">')
                else:
                    msg.append(f'<span style="color:gray; display:block">{message.date.replace(microsecond=0, tzinfo=None)}</span> <b style="color: {users[id]["color"]}">{users[id]["name"]} :: </b><img src="{media_link}.jpg">')
            else:
                msg.append(f'<span style="color:gray; display:block">{message.date.replace(microsecond=0, tzinfo=None)}</span> <b style="color: {users[id]["color"]}">{users[id]["name"]} :: </b> {message.text}')
        except:
            client.disconnect()
    context = {
        'msg': reversed(msg),
        'chat': chat,
        'limit': limit
    }
    client.disconnect()
    return render(request, 'chat_detail/index.html', context)
