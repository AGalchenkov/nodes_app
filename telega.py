import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()

from telethon import TelegramClient, events, sync
import re
from telechat.models import *
from django.conf import settings
from webpush import send_group_notification
import asyncio



django.setup()
print(settings.MEDIA_ROOT)

api_id = 11821981
api_hash = '4fa5dde61b5172461ec011169cb02420'
#loop = asyncio.new_event_loop()
#asyncio.set_event_loop(loop)

client = TelegramClient('test_session', api_id, api_hash)
@client.on(events.NewMessage())
async def normal_handler(event):
    print(event)
    await event.get_chat()
    try:
        event.chat.title
        chat_title = event.chat.title
    except AttributeError:
        lastname = event.chat.last_name if event.chat.last_name else ""
        firstname = event.chat.first_name if event.chat.first_name else ""
        chat_title = firstname + " " + lastname
    payload = {"head": "new message", "body": f"chat : {chat_title}"}
    send_group_notification(group_name='all', payload=payload, ttl=1000)

client.start()

#print(client.get_me().stringify())

#client.send_message('and_galchenkov', 'Hello! Talking to you from Telethon')

users = {}

chats = Chat.objects.get(id=1)
client.get_dialogs()
#list_result = [entry.name for entry in chats]
#list_result = [chats.name]
for dialog in client.iter_dialogs():
    print(dialog.title)
#for dialog in client.iter_dialogs():
#    if re.search(r'РДП|RDP', dialog.title):
#       if not dialog.title in list_result:
#            Chat(name=dialog.title).save()
#        #participants = client.get_participants(dialog.title)
#        for partic in client.iter_participants(dialog.title):
#           lastname = partic.last_name if partic.last_name else ""
#            firstname = partic.first_name if partic.first_name else ""
#            users[partic.id] = firstname + " " + lastname
#        print("#"*(len(dialog.title) + 2))
#       print(f'#{dialog.title}#')
#        print("#"*(len(dialog.title) + 2))
#        print(f'Messages in {dialog.title}')
       # for message in client.iter_messages(dialog.title, limit=2):
#for message in client.iter_messages(chats.name, limit=2):
#    id = message.from_id.user_id
#         #   print(f'{users[id]} :: {message.text}')
#    if message.action:
#        if 'AddUser' in str(message.action):
#            print('!!!')
##        print(message.action)
#        print(type(message.action))
#    if message.media:
#        med = client.download_media(message.media, str(settings.MEDIA_ROOT) + f'/telechat/{chats.name}/{id}')
#                #pass
#        print("{:25} :: {} \r\n".format(users[id], message.text))

client.run_until_disconnected()
