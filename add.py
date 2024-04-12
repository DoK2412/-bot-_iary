import telebot
import datetime
import re


from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar


from user_data import User
from servise.replacement import Authorization, UserResponse, Feedbacks, WorkingNotes, WorkingNotebook

from setting import bot_token


bot = telebot.TeleBot(bot_token)


@bot.message_handler(commands=['start'])
def startBotWorck(message):
    try:
        user = User.get_user(message.chat.id)
        user_check = Authorization().user_verification(message.from_user.id)
        if user_check:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttom_1 = types.KeyboardButton('Добавить заметку')
            buttom_2 = types.KeyboardButton('Заметки на день')
            buttom_3 = types.KeyboardButton('Заметки по датам')
            buttom_4 = types.KeyboardButton('Записать в блокнот')
            buttom_5 = types.KeyboardButton('Записи в блокноте')
            buttom_6 = types.KeyboardButton('Обратная связь')

            markup.add(buttom_1, buttom_2, buttom_3)
            markup.add(buttom_4, buttom_5)
            markup.add(buttom_6)

            bot.send_message(message.chat.id, "Велкам", reply_markup=markup)

        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttom_1 = types.KeyboardButton('Авторизация')

            markup.add(buttom_1)

            bot.send_message(message.chat.id, "Необходимо пройти авторизацию в боте", reply_markup=markup)
    except Exception as ecx:
        bot.send_message(message.chat.id, "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")


@bot.message_handler(content_types=['text'])
def bot_messag(message):
    try:
        user = User.get_user(message.chat.id)
        result = UserResponse(message, bot, user).request()
        if result in ['существует', 'создан']:
            startBotWorck(message)
        elif result == "блокнот":
            bot.send_message(message.from_user.id, 'Введите название для текста.')
            bot.register_next_step_handler(message, receiving_name)

    except Exception as ecx:
        bot.send_message(message.chat.id, "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal(call):
    try:
        user = User.get_user(call.message.chat.id)
        WorkingDates().getting_date(call)
    except Exception as ecx:
        bot.send_message(call.from_user.id, "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")



class WorkingDates(object):

    def getting_date(self, call):
        """
            получение месяца и числа
        """
        try:
            user = User.get_user(call.message.chat.id)

            result, key, step = DetailedTelegramCalendar(calendar_id=1, locale='ru', min_date=datetime.date.today()).process(call.data)
            if not result and key:
                bot.edit_message_text('Укажите месяц и число.',
                                           call.message.chat.id,
                                           call.message.message_id,
                                           reply_markup=key)
            elif result:
                bot.edit_message_text(f"Выбрана дата: {result}",
                                      call.message.chat.id,
                                      call.message.message_id)
                user.data = result
                WorkingDates().receive_user_notes(call)
        except Exception as ecx:
            bot.send_message(call.from_user.id,
                             "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")

    def receive_user_notes(self, call):
        """
            получение текста заметки от пользователя
        """
        try:
            bot.send_message(call.message.chat.id, 'Введите текст сообщения.')
            bot.register_next_step_handler(call.message, WorkingDates().note_user_processing)
        except Exception as ecx:
            bot.send_message(call.from_user.id,
                             "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")

    @bot.message_handler(content_types=['text'])
    def note_user_processing(self, call):
        """
            обработка заметки
        """
        try:
            user = User.get_user(call.from_user.id)

            # print(call)
            # if call.get('sticker'):
            #     result = WorkingNotes().save_note(data_us.data, call.text, call.from_user.id, call.sticker.file_id)
            # else:
            result = WorkingNotes().save_note(user.data, call.text, call.from_user.id)

            if result:
                bot.send_message(call.from_user.id, "Заметка сохранена.")
            else:
                bot.send_message(call.from_user.id, "Не удалось сохранить заметку.")
        except Exception as ecx:
            bot.send_message(call.from_user.id,
                             "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")


@bot.callback_query_handler(func=lambda call: True)
def entry_database(call):
    """
    получение замеки от пользователя
    """
    try:
        user = User.get_user(call.from_user.id)

        user.message_id = call.message.message_id
        if re.search('\d{4}-\d{2}-\d{2}', call.data):
            user.message_nate_id = call.message.message_id
            user.message_id = call.message.message_id
            bot.send_message(call.from_user.id, f'Выбрана дата: {call.data}.')
            bot.delete_message(call.from_user.id, user.message_id)
            user.date_note = call.data


            note = WorkingNotes().get_notes(call)
            WorkingNotes().sending_notes(call, user, bot, note)
                # if nat.sticker:
                #     bot.send_sticker(call.from_user.id, nat.sticker)
                # else:
                #     bot.send_message(call.from_user.id, nat.nate)
            # WorkingNotes().editing_note(bot, call)


        elif call.data.startswith("Заметка"):
            user.user_nate = call.data[8:]
            WorkingNotes().editing_note(bot, call, user)

        elif call.data.startswith("Блокнот "):
            user.big_user_note_book = call.data[8:]
            WorkingNotebook().editing_notebook(bot, call)

        elif call.data == "Кнопка удалить":
            for i in range(len(user.big_user_nate)):
                if user.big_user_nate[i].startswith(user.user_nate[:-3]):
                    WorkingNotes().note_detete(call, user.big_user_nate[i], user.date_note)
                    break
            else:
                WorkingNotes().note_detete(call, user.user_nate, user.date_note)
            bot.delete_message(call.from_user.id, user.message_id)
            bot.send_message(call.from_user.id, 'Заметка удалена.')

        elif call.data == "Кнопка изменить":
            bot.delete_message(call.from_user.id, user.message_id)
            bot.send_message(call.from_user.id, 'Введите текст изменения.')
            bot.register_next_step_handler(call.message, nat_appdata)
        elif call.data == "Кнопка просмотреть":
            bot.delete_message(call.from_user.id, user.message_id)
            for i in range(len(user.big_user_nate)):
                if user.big_user_nate[i].startswith(user.user_nate[:-3]):
                    bot.send_message(call.from_user.id, user.big_user_nate[i])
                    break
        elif call.data == "Кнопка посмотреть текст":
            bot.delete_message(call.from_user.id, user.message_id)
            WorkingNotebook().get_text_notebook(bot, call, user)
        elif call.data == "Удалить текст":
            bot.delete_message(call.from_user.id, user.message_id)
            WorkingNotebook().delete_text_notebook(bot, call, user)
        elif call.data == "Изменить текст":
            bot.delete_message(call.from_user.id, user.message_id)
            bot.send_message(call.from_user.id, 'Введите текст изменения.')
            bot.register_next_step_handler(call.message, update_notebook)

        else:
            bot.send_message(call.from_user.id, 'Введите текст сообщения.')
            bot.register_next_step_handler(call.message, preservation)
    except Exception as ecx:
        bot.send_message(call.from_user.id, "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")



@bot.message_handler(content_types=['text'])
def preservation(call):
    """
    сохранение замеки
    """
    try:
        Feedbacks(call, bot).sending_message(call.from_user.id)
    except Exception as ecx:
        bot.send_message(call.from_user.id, "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")



@bot.message_handler(content_types=['text'])
def nat_appdata(call):
    """
    обновление заметки
    """
    try:
        user = User.get_user(call.from_user.id)
        for i in range(len(user.big_user_nate)):
            if user.big_user_nate[i].startswith(user.user_nate[:-3]):
                WorkingNotes().nate_appdata(call, user.big_user_nate[i], user.date_note)
                break
        else:
            WorkingNotes().nate_appdata(call, user.user_nate, user.date_note)
        user.big_user_nate = list()
        bot.send_message(call.from_user.id, 'Заметка изменена.')
    except Exception as ecx:
        bot.send_message(call.from_user.id, "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")


@bot.message_handler(content_types=['text'])
def receiving_name(message):
    user = User.get_user(message.from_user.id)
    user.name_notebook = message.text
    bot.send_message(message.from_user.id, 'Введите текст.')
    bot.register_next_step_handler(message, save_notebook)

@bot.message_handler(content_types=['text'])
def save_notebook(message):
    try:
        user = User.get_user(message.from_user.id)
        text_notebook = message.text
        WorkingNotebook().save_notebook(message, bot, user.name_notebook, text_notebook)
    except Exception as ecx:
        bot.send_message(message.from_user.id, "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")


@bot.message_handler(content_types=['text'])
def update_notebook(message):
    try:
        user = User.get_user(message.from_user.id)
        text_notebook = message.text
        WorkingNotebook().update_text_notebook(message, bot, user, text_notebook)
    except Exception as ecx:
        bot.send_message(message.from_user.id, "При выполнении запроса произошла ошибка, повторите запрос либо напишите обратную связь c описанием действий вызвавших ошибку.")


if __name__ == '__main__':
    bot.polling()