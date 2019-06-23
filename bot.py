import telebot
from telebot import types
import requests
from datetime import date, timedelta
import os
import redis
import json

token = os.environ['BOT_TOKEN']

bot = telebot.TeleBot(token)
api_url_main = 'http://81.2.244.179/api/schedule'
api_url = 'http://81.2.244.179/api/groups'

group_res = requests.get(api_url)

GROUP_LIST = []
for i in group_res.json():
    GROUP_LIST.append(i['number'])

MAIN_STATE = 'main'
GROUP_STATE = 'group_handler'
SCHEDULE_STATE = 'schedule_handler'
SCHEDULE_DATE_STATE = 'schedule_date_handler'
LESSON_STATE = 'lesson_handler'
YEAR_ = date.today().year

redis_url = os.environ.get('REDIS_URL')
if redis_url is None:
    try:
        data = json.load(open('data.json', 'r', encoding='utf-8'))
    except FileNotFoundError:
        data = {
            'states': {},
            'last_call': {},

            MAIN_STATE: {

            },
            GROUP_STATE: {

            },
            SCHEDULE_STATE: {

            },
            SCHEDULE_DATE_STATE: {

            },
            LESSON_STATE: {

            },

        }
else:
    redis_db = redis.from_url(redis_url)
    raw_data = redis_db.get('data')
    if raw_data is None:
        data = {
            'states': {},
            'last_call': {},

            MAIN_STATE: {

            },
            GROUP_STATE: {

            },
            SCHEDULE_STATE: {

            },
            SCHEDULE_DATE_STATE: {

            },
            LESSON_STATE: {

            },

        }
    else:
        data = json.loads(raw_data)

def change_data(key, user_id, value):
    data[key][user_id] = value
    print(user_id, key, data[key][user_id])
    if redis_url is None:
        json.dump(
            data,
            open('data.json', 'w', encoding='utf-8'),
            indent=2,
            ensure_ascii=False,
        )
    else:
        redis_db = redis.from_url(redis_url)
        redis_db.set('data', json.dumps(data))

def change_additional_data(key1, user_id, key2, value):
    data[key1][user_id][key2] = value
    if redis_url is None:
        json.dump(
            data,
            open('data.json', 'w', encoding='utf-8'),
            indent=2,
            ensure_ascii=False,
        )
    else:
        pass # send to redis


def generate_keyboard(*texts, one_time=True):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=one_time)
    buttons = [types.KeyboardButton(text) for text in texts]
    keyboard.add(*buttons)
    return keyboard


STATE_ENTER_MESSAGES = {
  SCHEDULE_STATE: {
    "text": "Чтобы узнать расписание на интересующий тебя день, отправь боту команду 'Расписание' "
            "или отправь команду 'Последнее расписание', чтобы узнать последний найденный результат."
            "Если хочешь сменить номер группы, нажми 'Назад'",
    "text2": "Чтобы узнать расписание на интересующий тебя день, отправь боту команду 'Расписание'"
             "Если хочешь сменить номер группы, нажми 'Назад'",
    "text3": "Вернулся назад. Здесь можно посмотреть последнее расписание или посмотреть расписание на новую дату",
    "reply_markup": generate_keyboard('Расписание', 'Последнее расписание', 'Назад'),
    "reply_markup2": generate_keyboard('Расписание', 'Назад')
  },

  SCHEDULE_DATE_STATE: {
    "text": "Можешь выбрать день или написать конкретную дату"
            "(для этого введи дату (мес, день) в числовом формате)",
    "text2": "Вернулся в режим выбора даты",
    "reply_markup": generate_keyboard('Сегодня', 'Завтра', 'Послезавтра', 'Назад', one_time=False)
  },

  LESSON_STATE: {
      "text": "Выбери пару",
      "text2": "Интересно, какие предметы проходят другой парой? Жми кнопку!",
      "reply_markup": generate_keyboard('1', '2', '3', '4', '5', 'Назад')
  }

}


@bot.message_handler(func=lambda message: True)
def dispatcher(message):
    user_id = str(message.from_user.id)

    state = data['states'].get(user_id, MAIN_STATE)
    print('current state', user_id, state)

    if state == MAIN_STATE:
        main_handler(message)

    elif state == GROUP_STATE:
        group_handler(message)

    elif state == SCHEDULE_STATE:
        schedule(message)

    elif state == SCHEDULE_DATE_STATE:
        schedule_date(message)

    elif state == LESSON_STATE:
        lesson_handler(message)


def main_handler(message):

    user_id = str(message.from_user.id)

    if 'привет' in message.text.lower():
        bot.reply_to(message, 'Ну привет, ' + message.from_user.first_name + '! ' +
                     'Чтобы начать работать с ботом, отправь ему команду "/start"')
    elif message.text == '/start':
        bot.reply_to(message, 'Это бот с расписанием занятий: он умеет подсказывать расписание на сегодня и на завтра. '
                              'Напиши номер своей группы')
        change_data('states', user_id, GROUP_STATE)
    else:
        bot.reply_to(message, 'Я тебя не понял. Чтобы начать работу с ботом, отправь ему команду "/start"')


def group_handler(message):
    user_id = str(message.from_user.id)

    group_number = message.text.lower()
    if group_number in GROUP_LIST:
        change_data(GROUP_STATE, user_id, group_number)
        bot.reply_to(message, STATE_ENTER_MESSAGES[SCHEDULE_STATE]['text'],
                     reply_markup=STATE_ENTER_MESSAGES[SCHEDULE_STATE]['reply_markup'])
        change_data('states', user_id, SCHEDULE_STATE)
    else:
        bot.reply_to(message, 'Такой группы у нас нет :( Выбери другой номер.')


def schedule(message):
    user_id = str(message.from_user.id)

    print(message)
    if message.text.lower() == 'последнее расписание':
        last_schedule = data['last_call'].get(user_id, 'Пока пусто!')
        bot.send_message(user_id, last_schedule)
        bot.reply_to(message, STATE_ENTER_MESSAGES[SCHEDULE_STATE]['text2'],
                     reply_markup=STATE_ENTER_MESSAGES[SCHEDULE_STATE]['reply_markup2'])
        change_data('states', user_id, SCHEDULE_STATE)

    elif message.text.lower() == 'расписание':
        bot.reply_to(message, STATE_ENTER_MESSAGES[SCHEDULE_DATE_STATE]['text'],
                     reply_markup=STATE_ENTER_MESSAGES[SCHEDULE_DATE_STATE]['reply_markup'])
        change_data('states', user_id, SCHEDULE_DATE_STATE)

    elif message.text.lower() == 'назад':
        bot.send_message(user_id, 'Вернулся назад. Напиши боту свой номер группы')
        change_data('states', user_id, GROUP_STATE)

    else:
        bot.reply_to(message, 'Я тебя не понял, напиши "расписание", если хочешь узнать расписание')


def certain_date(message):
    month, day = message.text.lower().split(' ')
    year, week_number, day_number = date(YEAR_, int(month), int(day)).isocalendar()
    return year, week_number, day_number


def schedule_date(message):
    user_id = str(message.from_user.id)

    if message.text.lower() == 'назад':
        bot.send_message(user_id, STATE_ENTER_MESSAGES[SCHEDULE_STATE]['text3'],
                         reply_markup=STATE_ENTER_MESSAGES[SCHEDULE_STATE]['reply_markup'])
        change_data('states', user_id, SCHEDULE_STATE)
    else:
        try:

            if message.text.lower() == 'сегодня':
                year, week_number, day_number = date.today().isocalendar()

            elif message.text.lower() == 'завтра':
                tomorrow = date.today() + timedelta(days=1)
                year, week_number, day_number = tomorrow.isocalendar()

            elif message.text.lower() == 'послезавтра':
                day_after_tomorrow = date.today() + timedelta(days=2)
                year, week_number, day_number = day_after_tomorrow.isocalendar()
            else:
                month, day = message.text.lower().split(',')
                year, week_number, day_number = date(YEAR_, int(month.strip()), int(day.strip())).isocalendar()

            if int(week_number) % 2 == 0:
                week_parity = 2
            else:
                week_parity = 1

            if day_number == 6 or day_number == 7:
                bot.reply_to(message, 'Это выходной день!')
            else:
                change_data(SCHEDULE_DATE_STATE, user_id, {})
                change_additional_data(SCHEDULE_DATE_STATE, user_id, 'dow', str(day_number))
                change_additional_data(SCHEDULE_DATE_STATE, user_id, 'parity', str(week_parity))
                print(data[SCHEDULE_DATE_STATE].get(user_id))

                bot.reply_to(message, STATE_ENTER_MESSAGES[LESSON_STATE]['text'],
                             reply_markup=STATE_ENTER_MESSAGES[LESSON_STATE]['reply_markup'])
                change_data('states', user_id, LESSON_STATE)
        except ValueError:
            bot.reply_to(message, 'Я тебя не понял, нажми на кнопку или напиши дату')


def lesson_handler(message):

    user_id = str(message.from_user.id)

    if message.text.lower() == "назад":
        bot.send_message(user_id, STATE_ENTER_MESSAGES[SCHEDULE_DATE_STATE]['text2'],
                         reply_markup=STATE_ENTER_MESSAGES[SCHEDULE_DATE_STATE]['reply_markup'])
        change_data('states', user_id, SCHEDULE_DATE_STATE)
    else:
        lesson_number = message.text
        change_additional_data(SCHEDULE_DATE_STATE, user_id, 'pair', str(lesson_number))

        main_res = requests.get(api_url_main, params={'group': data[GROUP_STATE][user_id]}).json()
        print(data[SCHEDULE_DATE_STATE].get(user_id))

        schedule_message = "Извините, в этот день нет такой пары!"
        for elem in main_res['exercises']:
            if elem['day'] == data[SCHEDULE_DATE_STATE][user_id]['dow'] \
                    and elem['parity'] == data[SCHEDULE_DATE_STATE][user_id]['parity'] \
                    and elem['pair'] == data[SCHEDULE_DATE_STATE][user_id]['pair']:
                schedule_message = '"{}" в кабинете №{}'.format(elem['name'].capitalize(), elem['room_id'])
                break
            elif elem['day'] == data[SCHEDULE_DATE_STATE][user_id]['dow'] \
                    and elem['parity'] is None \
                    and elem['pair'] == data[SCHEDULE_DATE_STATE][user_id]['pair']:
                schedule_message = '"{}" в кабинете №{}'.format(elem['name'].capitalize(), elem['room_id'])
                break

        bot.send_message(user_id, schedule_message)
        change_data('last_call', user_id, schedule_message)

        bot.send_message(user_id, STATE_ENTER_MESSAGES[LESSON_STATE]['text2'],
                         reply_markup=STATE_ENTER_MESSAGES[LESSON_STATE]['reply_markup'])

        change_data('states', user_id, LESSON_STATE)



bot.polling()