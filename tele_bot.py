import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()

from nodes.models import *
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import random


bot_name = sys.argv[1]
TOKEN = TelegramToken.objects.get(telegram_bot_name=bot_name).token
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

base_buttons = {
    'button_free': InlineKeyboardButton(text="Get Free Nodes", callback_data="get_free_nodes"),
    'button_my': InlineKeyboardButton(text="Get My Nodes", callback_data="get_my_nodes"),
    'button_inuse': InlineKeyboardButton(text="Get Booked Nodes", callback_data="get_booked_nodes"),
    'button_delim': InlineKeyboardButton(text="******************************", callback_data="fake")
}

button1 = InlineKeyboardButton(text="Get Free Nodes", callback_data="get_free_nodes")
button_my = InlineKeyboardButton(text="Get My Nodes", callback_data="get_my_nodes")
button_delim = InlineKeyboardButton(text="-----------------------------------------------------", callback_data="fake")
#keyboard_inline = InlineKeyboardMarkup().add(button1).add(button_my).add(button_delim)
keyboard_inline = InlineKeyboardMarkup().add(base_buttons['button_free']).add(base_buttons['button_my']).add(base_buttons['button_inuse']).add(base_buttons['button_delim'])

def auth_request(username):
    try:
        TelegramUser.objects.get(telegram_name=username)
        return True
    except ObjectDoesNotExist:
        return False

@dp.message_handler(commands=['help'])
async def send_welcome(msg: types.Message):
    await msg.answer(f'Я бот для бронирования узлов. Весь функционал реализован в меню. Операции интуитивно понятны. Нажмите start для начала.')
@dp.message_handler(commands=['start'])
async def send_welcome(msg: types.Message):
    username = msg.from_user.username
    if not auth_request(username):
        await msg.answer('В доступе отказано.')
        return
    await msg.answer("Select to get nodes list", reply_markup=keyboard_inline)
    print(f'BASE MSG ID ###    {msg.message_id}')
    #markup = types.InlineKeyboardMarkup(resize_keyboard=True)
    #item1 = types.KeyboardButton("Привет")
    #item2 = types.KeyboardButton("Загадай число")
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = KeyboardButton("/start")
    markup.add(item1)

    #markup.add(item1).add(item2)
    await msg.answer(text="Press '/start' to start over. ", reply_markup=markup)


@dp.callback_query_handler(text = "get_free_nodes")
async def get_free(call: types.CallbackQuery, base_buttons=base_buttons):
    username = call.from_user.username
    if not auth_request(username):
        await call.answer('В доступе отказано.')
        return
    if call.data == "get_free_nodes":
        free_node = LittleSecret.objects.filter(in_use=False)
        #int = random.randint(0, 20000)
        #button2 = InlineKeyboardButton(text=f"random {int}", callback_data="push_random")
        keyboard_inline = InlineKeyboardMarkup().add(base_buttons['button_free']).add(base_buttons['button_my']).add(base_buttons['button_inuse']).add(base_buttons['button_delim'])
        if not free_node:
            for k in call.message.reply_markup.values['inline_keyboard']:
                if 'no free nodes' in k[0]['text']:
                    await call.answer()
                    return True
            no_button = InlineKeyboardButton(text='There are no free nodes', callback_data='fake')
            keyboard_inline.add(no_button)
            #await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='Chosse a node to book', reply_markup=None)
            await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='There are no free nodes', reply_markup=keyboard_inline)
            return
        for node in free_node:
            button2 = InlineKeyboardButton(text=f"- {node} -", callback_data=f"set_inuse_{node}")
            keyboard_inline.add(button2)
        #call.message.clean()
        if call.message.reply_markup.values == keyboard_inline.values:
            await call.answer()
            return
            #await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='Chosse a node to book', reply_markup=None)
            #await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='Chosse a node to book', reply_markup=keyboard_inline)

           # await call.answer()
        else:
            await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='Chosse a node to book', reply_markup=keyboard_inline)
            return
        #await call.message.answer("Here is your random int", reply_markup=keyboard_inline)
    await call.answer()
    return

#@dp.callback_query_handler(text = "set_inuse_")
@dp.callback_query_handler()
async def action(call: types.CallbackQuery, base_buttons=base_buttons):
    username = call.from_user.username
    if not auth_request(username):
        await call.answer('В доступе отказано.')
        return
    call.clean()
    username = call.from_user.username
    keyboard_inline_local = InlineKeyboardMarkup()
    if 'fake' in call.data:
        await call.answer()
        return
    ls_name = f'- {call.data.split("_")[2]} -'
    if call.data.startswith('set_inuse'):
        ls_id = call.data.split('#')[1]
        user = TelegramUser.objects.get(telegram_name=username)
        LittleSecret(id=ls_id, in_use=True, owner=user).save()
        for k in call.message.reply_markup.values['inline_keyboard']:
            if not k[0]['text'] == ls_name:
                keyboard_inline_local.add(k[0])

        print(f'GET FREE MSG ID  ####  {call.message.message_id}')
        #await call.answer()
        await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=f"booked Node #{ls_id}", reply_markup=keyboard_inline_local)
        return
  #  await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id, reply_markup=keyboard_inline)
    if call.data == 'get_my_nodes':
        my_nodes = LittleSecret.objects.filter(owner__telegram_name=username)
        keyboard_inline = InlineKeyboardMarkup().add(base_buttons['button_free']).add(base_buttons['button_my']).add(base_buttons['button_inuse']).add(base_buttons['button_delim'])
        if not my_nodes:
            no_button = InlineKeyboardButton(text='You have no booked nodes', callback_data='fake')
            keyboard_inline.add(no_button)
            try:
                await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='You have no booked nodes', reply_markup=keyboard_inline)
            except:
                await call.answer()
                return
        for node in my_nodes:
            node_button = InlineKeyboardButton(text=f"- {node} -", callback_data=f"unset_inuse_{node}")
            keyboard_inline.add(node_button)
        try:
            await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=f"Your nodes.\r\nSelect to release.", reply_markup=keyboard_inline)
            return
        except:
            await call.answer()
            return
    if call.data.startswith('unset_inuse'):
        ls_id = call.data.split('#')[1]
        node = call.data.split('_')[2]
        keyboard_inline_local = InlineKeyboardMarkup()
        LittleSecret(id=ls_id, in_use=False, owner=None).save()
        for k in call.message.reply_markup.values['inline_keyboard']:
            if not k[0]['text'] == ls_name:
                keyboard_inline_local.add(k[0])
        #await bot.send_message(call.from_user.id, f'Release {node}')
        await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=f'Release node #{ls_id}', reply_markup=keyboard_inline_local)
        return
    if call.data == "get_booked_nodes":
        booked_node = LittleSecret.objects.filter(in_use=True)
        #int = random.randint(0, 20000)
        #button2 = InlineKeyboardButton(text=f"random {int}", callback_data="push_random")
        keyboard_inline = InlineKeyboardMarkup().add(base_buttons['button_free']).add(base_buttons['button_my']).add(base_buttons['button_inuse']).add(base_buttons['button_delim'])
        if not booked_node:
            for k in call.message.reply_markup.values['inline_keyboard']:
                if 'There are no booked nodes' in k[0]['text']:
                    await call.answer()
                    return
            no_button = InlineKeyboardButton(text='There are no booked nodes', callback_data='fake')
            keyboard_inline.add(no_button)
            #await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='Chosse a node to book', reply_markup=None)
            await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='There are no booked nodes', reply_markup=keyboard_inline)
            return
        for node in booked_node:
            id = str(node).split('#')[1]
            button2 = InlineKeyboardButton(text=f"- {node.owner.real_name} :: node#{id} -", callback_data="fake")
            keyboard_inline.add(button2)
        #call.message.clean()
        if call.message.reply_markup.values == keyboard_inline.values:
            await call.answer()
            return
            #await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='Chosse a node to book', reply_markup=None)
            #await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='Chosse a node to book', reply_markup=keyboard_inline)

           # await call.answer()
        else:
            await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text='Booked nodes list', reply_markup=keyboard_inline)
            return
        #await call.message.answer("Here is your random int", reply_markup=keyboard_inline)
    await call.answer()
    return


@dp.message_handler(content_types=['text'])
async def get_text_messages(msg: types.Message):
    if msg.text.lower() == 'привет':
        await msg.answer(f'Привет, {msg.from_user.first_name}!')
    elif msg.text.lower() == 'загадай число':
        int = random.randint(0, 20000)
        await  msg.answer(int)
    else:
        await msg.answer('Не понимаю, что это значит. Я пока плохо понимаю человеческий.')



if __name__ == '__main__':
   executor.start_polling(dp)
