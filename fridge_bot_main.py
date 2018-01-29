# -*- coding: utf-8 -*-
import configparser
import telebot
from telebot import types
import serial
import threading
import time
import logging

conf_path = '/home/pi/Documents/fridge_bot/config.ini'  # path to config
conf = configparser.ConfigParser()  # connect config
conf.read(conf_path)
setting = conf['Setting']

bot = telebot.TeleBot(setting['TOKEN'])  # telegram bot setup
ser = serial.Serial(setting['PORT'], setting['BAUD'])  # serial setup

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # main menu
hide = types.ReplyKeyboardRemove()
markup.row('🥛Молоко', '🥚Яйца')
markup.row('⚙Настройки')


@bot.message_handler(commands=['start'])  # '/start' command handler
def subscribe_chat(message):
    users = open('users.txt', 'r')
    if (str(message.chat.id) + '\n') in users:
        bot.send_message(message.chat.id, 'Бот уже запущен')
    else:
        users = open('users.txt', 'a')
        users.write(str(message.chat.id) + '\n')
        bot.reply_to(message, 'Запуск бота...')
        time.delay(3)
        bot.reply_to(message, 'Бот успешно запущен')
    users.close()


@bot.message_handler(func=lambda message: message.text == '🥚Яйца')  # eggs handler
def eggs_send(message):
    eggs = get_eggs()
    if eggs == "err":
        bot.register_next_step_handler(message, error)
    else:
        bot.send_message(message.chat.id, 'Осталось яиц: ' + eggs + ' шт.')
    # curtime = datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')
    # bot.send_message(message.chat.id, 'Temperature: ' + temp + ' °C\n' + 'Time: ' + curtime)


@bot.message_handler(func=lambda message: message.text == '🥛Молоко')  # milk handler
def milk_send(message):
    milk = get_milk()
    if milk == "err":
        bot.register_next_step_handler(message, error)
    else:
        bot.send_message(message.chat.id, 'Осталось молока: ' + milk + ' мл')


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
        with open('config.ini', 'w') as config:
            conf.write(config)
        message = bot.reply_to(message, 'Задержка установлена!', reply_markup=markup)
    except Exception as e_delay:
        logging.exception(e_delay)
        bot.reply_to(message, 'Ой, словили баг')


def get_eggs():   # get 'eggs' from serial
    i = 7
    while i == 7:
        try:
            tmp = ser.read(8)  # read 8 bytes
            tmp = tmp.decode(errors='ignore')
            i = 0
            while (tmp[i] != 'e') & (i < 7):
                i += 1
            if i != 7:
                return tmp[i + 1]  # e3m400e6
        except Exception as e_eggs:
            logging.exception(e_eggs)
            return "err"


def get_milk():   # get 'milk' from serial
    i = 5
    while i == 5:
        try:
            tmp = ser.read(8)  # read 8 bytes
            tmp = tmp.decode(errors='ignore')
            i = 0
            while (tmp[i] != 'm') & (i < 5):
                i += 1
            if i != 5:
                return tmp[i + 1:i + 4]  # e3m400e6
        except Exception as e_milk:
            logging.exception(e_milk)
            return "err"


def notification():   # notifications sender
    delay = int(setting['DELAY'])
    time.sleep(delay*60)
    users = open('users.txt', 'r')
    print('SEND')
    eggs = get_eggs()
    milk = get_milk()
    print(milk + ' ' + eggs)
    for user in users:
        user_id = int(user[:-1])
        if int(eggs) < 3:
            bot.send_message(user_id, 'Яйца заканчиваются\nОсталось: ' + eggs + ' шт.', reply_markup=markup)
        if int(milk) < 300:
            bot.send_message(user_id, 'Молоко заканчивается\nОсталось: ' + milk + ' мл', reply_markup=markup)
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
