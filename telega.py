import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django
django.setup()

from telethon import TelegramClient, events, sync
import re
from telechat.models import *
from django.conf import settings



django.setup()
print(settings.MEDIA_ROOT)

api_id = 11821981
api_hash = '4fa5dde61b5172461ec011169cb02420'

client = TelegramClient('test_session', api_id, api_hash)
client.start()

#print(client.get_me().stringify())

#client.send_message('and_galchenkov', 'Hello! Talking to you from Telethon')

users = {}

chats = Chat.objects.all()
list_result = [entry.name for entry in chats]

for dialog in client.iter_dialogs():
    if re.search(r'РДП|RDP', dialog.title):
        if not dialog.title in list_result:
            Chat(name=dialog.title).save()
        #participants = client.get_participants(dialog.title)
        for partic in client.iter_participants(dialog.title):
            lastname = partic.last_name if partic.last_name else ""
            firstname = partic.first_name if partic.first_name else ""
            users[partic.id] = firstname + " " + lastname
        print("#"*(len(dialog.title) + 2))
        print(f'#{dialog.title}#')
        print("#"*(len(dialog.title) + 2))
        print(f'Messages in {dialog.title}')
        for message in client.iter_messages(dialog.title, limit=20):
            id = message.from_id.user_id
         #   print(f'{users[id]} :: {message.text}')
            if message.media:
                med = client.download_media(message.media, str(settings.MEDIA_ROOT) + f'/telechat/{dialog.title}/{id}')
                #pass
            print("{:25} :: {} \r\n".format(users[id], message.text))
