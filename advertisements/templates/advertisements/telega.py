from telethon import TelegramClient, events, sync
import re

api_id = 11821981
api_hash = '4fa5dde61b5172461ec011169cb02420'

client = TelegramClient('test_session', api_id, api_hash)
client.start()

#print(client.get_me().stringify())

#client.send_message('and_galchenkov', 'Hello! Talking to you from Telethon')

for dialog in client.iter_dialogs():
    if re.search(r'РДП|RDP', dialog.title):
        print(dialog.title)
