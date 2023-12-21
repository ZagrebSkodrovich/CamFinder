import telebot
from telebot import types
from telebot.types import InputMediaPhoto
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
from sqlite3 import Error
from PIL import Image
import os

API_TOKEN = '6826795099:AAFzxyEiF0Wi3igyNmkDWUlXgeDJeQnP_Io'
BASE = 'http://localhost:5000'

bot = telebot.TeleBot(API_TOKEN)

                                                                #начало ТГхуйни

@bot.message_handler(content_types=['/help'])
def start(message):
    bot.send_message(message.from_user.id, '''Напиши /startsearch для ввода запроса
- /choosecam выбрать камеру.
- /show чтобы посомтреть найденные лоты.
- /showfav чтобы посмотреть избранные лоты.
- чтобы добавить лот в избранное, пререшлите лот с \U0001f90d.
- чтобы узнать более подробно о лоте, перешлите сообщение с лотом.
- /showstatistic чтобы узнать статистику''')

@bot.message_handler(func=lambda message: True)
def startsearch(message):
    if message.text == '/startsearch':
        bot.send_message(message.from_user.id, "Что бы вы хотели найти?")
        bot.register_next_step_handler(message, request_core)
    elif message.text == '/show':
        show_table(message)
        fav = ''
        bot.register_next_step_handler(message, show_lots, fav)
    elif message.text == '/showfav':
        fav = 'F'
        show_lots(message, fav)
    elif message.text == '/showstatistic':
        show_table(message)
        bot.register_next_step_handler(message, showstatistic)
    else:
        try:
            if message.reply_to_message.caption != None or message.reply_to_message.text != None:
                name = message.reply_to_message.caption
                if name[0] == '\U0001f90d' and message.text == '\U0001f90d':
                    bot.send_message(message.from_user.id, 'Лот уже в избранном')
                else:
                    if '\U0000274c' not in name:
                        newname = name.split('.  Цена: ', 1)[0]
                    else:
                        newname = name.split('. ❌Цена: ', 1)[0]
                    print(newname)
                    if message.text == '\U0001f90d':
                        print('cock3')
                        addfav = requests.put(BASE + '/addlottofav/'+newname).json()['message']
                        bot.send_message(message.from_user.id, addfav)
                    else:
                        showextralot(message, newname)
        except:
            start(message)

def showextralot(message, newname):
    cameras = requests.get(BASE + '/showextralot/'+newname).json()['camerainformation']
    if cameras[0][6] == 'F':
        fav = '\U0001f90d'
    else:
        fav = ' '
    if cameras[0][7] == 'N':
        act = '\U0000274c'
    else:
        act = ' '
    if cameras[0][5] != 'noimage':
        number = (cameras[0][5].split('.png')[0]).split('/')[8]
        images_url = cameras[0][3].split(',')
        if len(images_url) == 1:
            bot.send_photo(message.from_user.id, photo = images_url[0], caption = fav + cameras[0][0] + cameras[0][1] + act + 'Цена: ' + str(int(cameras[0][2]))+ '/n/n' + 'https://meshok.net/item/' + cameras[0][4])
        else:
            if len(images_url) < 9:
                j = len(images_url)
            else:
                j = 9
            path = '/Users/georgy/Desktop/penis/nigger_killer/images/'+(cameras[0][5].split('.png')[0]).split('/')[7]
            for i in range(1, j):
                img = Image.open(requests.get(images_url[i], stream = True).raw)
                img.save(path+'/'+number+'_'+str(i)+'.png')
            media_group = [types.InputMediaPhoto(open(path+'/'+str(number)+'.png', 'rb'))]
            for s in range(1, j):
                filenamepath = path+'/'+number+'_'+str(s)+'.png'
                media_group.append(types.InputMediaPhoto(open(filenamepath, 'rb')))
            bot.send_media_group(message.from_user.id, media_group)
    bot.send_message(message.from_user.id, fav + cameras[0][0] + cameras[0][1] + act + 'Цена: ' + str(int(cameras[0][2]))+ '\n\n' + 'https://meshok.net/item/' + cameras[0][4])

def show_table(message):
    searchrequest = requests.get(BASE + '/show/ ').json()['listofcams']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for num in range(0, len(searchrequest)):
        search = searchrequest[num][0]
        if ', ' in searchrequest[num][0]:
            search = search.split(', ', 1)[0]
        numpad = types.KeyboardButton(search)
        markup.add(numpad)
    bot.send_message(message.from_user.id, 'Выберите что показать: ', reply_markup=markup)

def showstatistic(message):
    a = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.from_user.id, 'Хорошо', reply_markup=a)
    print(message.text)
    price = requests.get(BASE + '/showstatistics/'+message.text).json()
    print(price)
    bot.send_message(message.from_user.id, 'Средняя цена: '+ price['actualprice'] +'\n'+'Цена продажи: '+price['sellprice'])

def request_core(message):
    response = requests.post(BASE + '/startsearch/'+message.text).json()['message']
    bot.send_message(message.from_user.id, response)

def show_lots(message, fav):
    if fav == '':
        a = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.from_user.id, 'Хорошо', reply_markup=a)
        name = message.text
    else:
        name = fav
        bot.send_message(message.from_user.id, 'Хорошо.')
    cameras = requests.post(BASE+'/show/'+name).json()['listofcams']
    if len(cameras) == 0 and fav == 'F':
        bot.send_message(message.from_user.id, 'Нету избранных лотов.')
    else:
        for i in range(0, len(cameras)):
            if cameras[i][4] == 'F':
                fav = '\U0001f90d'
            else:
                fav = ' '
            if cameras[i][5] == 'N':
                act = '\U0000274c'
            else:
                act = ' '
            caption = fav + cameras[i][0] + '. ' + act + 'Цена: ' + str(int(cameras[i][1]))
            if cameras[i][3] != 'noimage':
                bot.send_photo(message.from_user.id, open(str(cameras[i][3]), 'rb'), caption)
            else:
                bot.send_message(message.from_user.id, caption)

def statuscheck(message, response):
    if response.status_code != 200:
        bot.send_message(message.from_user.id, 'Что-то пошло не так. Автор идиот.')

bot.infinity_polling()