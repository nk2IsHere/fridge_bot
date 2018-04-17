# -*- coding: utf-8 -*-
import configparser
import telebot
from telebot import types
import serial
import threading
import time
import logging
from detect_contour import get_tomato
from detect_contour import cam_init
import numpy as np
import cv2 as cv
from telebot import apihelper
proxies = {
    'http': 'socks5://PROXY_5AD64B206FC28:72ab81839c99f96a@par4.google.v98nXNmRTPF8t0Oe1J4dcy4TLg636jiV.proxy.veesecurity.com:443',
    'https': 'socks5://PROXY_5AD64B206FC28:72ab81839c99f96a@par4.google.v98nXNmRTPF8t0Oe1J4dcy4TLg636jiV.proxy.veesecurity.com:443'
}

users_path = '/home/pi/Documents/fridge_bot/users.txt'  # path to users.txt
#users_path = 'C:/Users/Denis/Documents/drive/Google Drive/Projects/Холодильник/fridge_bot/users.txt'  # path to users.txt
cam_init()

conf_path = '/home/pi/Documents/fridge_bot/config.ini'  # path to config
#conf_path = 'C:/Users/Denis/Documents/drive/Google Drive/Projects/Холодильник/fridge_bot/config.ini'  # path to config
conf = configparser.ConfigParser()  # connect config
conf.read(conf_path)
setting = conf['Setting']

bot = telebot.TeleBot(setting['TOKEN'])  # telegram bot setup
ser = serial.Serial(setting['PORT'], setting['BAUD'], timeout=1)  # serial setup

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # main menu
hide = types.ReplyKeyboardRemove()
markup.row('🥛Молоко', '🥚Яйца')
markup.row('🌾Мука', '🍚Рис')
markup.row('🍅Помидоры', '⚙Настройки')


@bot.message_handler(commands=['start'])  # '/start' command handler
def subscribe_chat(message):
    users = open(users_path, 'r')
    if (str(message.chat.id) + '\n') in users:
        bot.send_message(message.chat.id, 'Бот уже запущен')
    else:
        users = open(users_path, 'a')
        users.write(str(message.chat.id) + '\n')
        bot.reply_to(message, 'Запуск бота...')
        time.delay(3)
        bot.reply_to(message, 'Бот успешно запущен')
    users.close()


@bot.message_handler(func=lambda message: message.text == '🥛Молоко')  # milk handler
def milk_send(message):
    milk = get_milk()
    if milk == "err":
        bot.register_next_step_handler(message, error)
    else:
        bot.send_message(message.chat.id, 'Осталось молока: ' + milk + ' мл')


@bot.message_handler(func=lambda message: message.text == '🥚Яйца')  # eggs handler
def eggs_send(message):
    eggs = get_eggs()
    if eggs == "err":
        bot.register_next_step_handler(message, error)
    else:
        bot.send_message(message.chat.id, 'Осталось яиц: ' + eggs + ' шт.')


@bot.message_handler(func=lambda message: message.text == '🌾Мука')  # flour handler
def tomato_send(message):
    flour = get_flour()
    if flour == "err":
        bot.register_next_step_handler(message, error)
    else:
        bot.send_message(message.chat.id, 'Осталось муки: ' + flour + ' гр')


@bot.message_handler(func=lambda message: message.text == '🍚Рис')  # rice handler
def tomato_send(message):
    rice = get_rice()
    if rice == "err":
        bot.register_next_step_handler(message, error)
    else:
        bot.send_message(message.chat.id, 'Осталось риса: ' + rice + ' гр')


@bot.message_handler(func=lambda message: message.text == '🍅Помидоры')  # tomato handler
def tomato_send(message):
    tomato = get_tomato()
    if tomato == "err":
        bot.register_next_step_handler(message, error)
    else:
        bot.send_message(message.chat.id, 'Осталось помидоров: ' + tomato + ' шт.')


@bot.message_handler(func=lambda message: message.text == '⚙Настройки')  # settings handler
def setting_send(message):
    delay = setting['DELAY']
    bot.send_message(message.chat.id, 'Задержка уведомлений: ' + delay + ' минут')
    bot.send_message(message.chat.id, 'Установите частоту уведомлений (в минутах)', reply_markup=hide)
    bot.register_next_step_handler(message, delay_set)


@bot.callback_query_handler(func=lambda c: True)  # callback button for reconnect
def reconnect(c):
    if c.data == 'Reconnect':
        try:
            ser.open()
            bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text='Подключено')
        except Exception as e_ser:
            logging.exception(e_ser)
            try:
                recon_button = types.InlineKeyboardMarkup()
                callback_button = types.InlineKeyboardButton(text='Reconnect', callback_data='Reconnect')
                recon_button.add(callback_button)
                bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                                      text='Повторите попытку', reply_markup=recon_button)
            except Exception as e_recon:
                logging.exception(e_recon)
                print("")


@bot.message_handler(func=lambda message: True, content_types=['text'])  # default handler
def echo_msg(message):
    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)




def error(message):   # connection error
    ser.close()
    recon_button = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text='Reconnect', callback_data='Reconnect')
    recon_button.add(callback_button)
    bot.send_message(message.chat.id, 'Ошибка чтения данных\nПерепроверьте подключение Arduino',
                     reply_markup=recon_button)


def delay_set(message):   # set delay for notifications
    try:
        delay = message.text
        if not delay.isdigit():
            msg = bot.reply_to(message, 'Задержка должна быть целым числом. Попробуйте снова')
            bot.register_next_step_handler(msg, delay_set)
            return
        conf.set('Setting', 'delay', delay)
        with open(conf_path, 'w') as config:
            conf.write(config)
        message = bot.reply_to(message, 'Задержка установлена!', reply_markup=markup)
    except Exception as e_delay:
        logging.exception(e_delay)
        bot.reply_to(message, 'Ой, словили баг')


def get_eggs():   # get 'eggs' from serial
    try:
        ser.write(b'e')
        time.sleep(0.5)
        tmp = ser.read(1)  # read 1 byte
        tmp = tmp.decode(errors='ignore')
        return tmp
    except Exception as e_eggs:
        logging.exception(e_eggs)
        return "err"


def get_milk():   # get 'milk' from serial
    try:
        ser.wite(b'm')
        time.sleep(0.5)
        tmp = ser.read(3)  # read 3 bytes
        tmp = tmp.decode(errors='ignore')
        return tmp
    except Exception as e_milk:
        logging.exception(e_milk)
        return "err"


def get_flour():   # get 'flour' from serial
    try:
        ser.write(b'f')
        time.sleep(0.5)
        tmp = ser.read(3)  # read 3 byte
        tmp = tmp.decode(errors='ignore')
        return tmp
    except Exception as e_flour:
        logging.exception(e_flour)
        return "err"


def get_rice():   # get 'rice' from serial
    try:
        ser.write(b'r')
        time.sleep(0.5)
        tmp = ser.read(3)  # read 3 byte
        tmp = tmp.decode(errors='ignore')
        return tmp
    except Exception as e_rice:
        logging.exception(e_rice)
        return "err"


def get_tomato():    # get 'tomato' from camera
    tomato = get_tomato()
    return tomato


def notification():   # notifications sender
    delay = int(setting['DELAY'])
    time.sleep(delay*60)
    users = open(users_path, 'r')
    print('SEND')
    eggs = get_eggs()
    milk = get_milk()
    tomato = get_tomato()
    rice = get_rice()
    flour = get_flour()
    print(milk + ' ' + eggs + ' ' + tomato + ' ' + rice + ' ' + flour)
    for user in users:
        user_id = int(user[:-1])
        if int(eggs) < 3:
            bot.send_message(user_id, 'Яйца заканчиваются\nОсталось: ' + eggs + ' шт.', reply_markup=markup)
        if int(milk) < 300:
            bot.send_message(user_id, 'Молоко заканчивается\nОсталось: ' + milk + ' мл', reply_markup=markup)
        if int(rice) < 300:
            bot.send_message(user_id, 'Рис заканчивается\nОсталось: ' + rice + ' гр', reply_markup=markup)
        if int(flour) < 300:
            bot.send_message(user_id, 'Мука заканчивается\nОсталось: ' + flour + ' гр', reply_markup=markup)
        if int(tomato) < 2:
            bot.send_message(user_id, 'Помидоры заканчиваются\nОсталось: ' + tomato + ' шт. ', reply_markup=markup)
    users.close()


if __name__ == '__main__':
    print('Bot started\n')
    while True:
        try:
            threading.Thread(target=bot.polling).start()
            while True:
                notification()
        except Exception as e_launch:
            logging.exception(e_launch)
            print('Bot relaunched\n')
            continue