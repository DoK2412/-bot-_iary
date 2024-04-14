from database.sql_requests import *
from database.connection_db import engin
from sqlmodel import Session, select

from telebot import types

import datetime

from database.sql_requests import Users, Feedback, Notebook

from telegram_bot_calendar import DetailedTelegramCalendar
from user_data import User


class Authorization(object):
    @classmethod
    def user_verification(cls, user_teleg_id):
        with Session(engin) as session:
            user_id = session.exec(select(Users).where(Users.user_id == user_teleg_id)).first()
        if user_id:
            return user_id

    @classmethod
    def adding_user(cls, user_teleg_id, user_name_teleg):
            check_user = Authorization().user_verification(user_teleg_id)

            if check_user:
                return "Пользователь уже авторизован"
            data = datetime.datetime.now()
            with Session(engin) as session:
                add_useer = Users(user_id=user_teleg_id,
                                  registration_date=str(data),
                                  active=True,
                                  telegramm_teg=user_name_teleg)
                session.add(add_useer)
                session.commit()
            return add_useer

    @classmethod
    def user_id(cls, user_teleg_id):
        with Session(engin) as session:
            user_id = session.exec(select(Users).where(Users.user_id == user_teleg_id)).first()
            if user_id is None:
                return None
            else:
                return user_id.id


class UserResponse(object):

    def __init__(self, message, bot, user=None):
        self.message = message
        self.bot = bot
        self.user = user

    def request(self):

        def daily_deletion():
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            user_id = Authorization.user_id(self.message.from_user.id)
            if user_id:
                with Session(engin) as session:
                    user_view = session.exec(select(Notes).where(Notes.user_id == user_id)).all()
                    for view in user_view:
                        if view.date < date:
                            session.delete(view)
                            session.commit()
                        else:
                            continue

        daily_deletion()
        if self.message.text == 'Авторизация':
            add_user = Authorization.adding_user(self.message.from_user.id, self.message.from_user.username)
            self.bot.send_message(self.message.chat.id, "Авторизация пройдена успешно.")
            if add_user == "Пользователь уже авторизован":
                return "существует"
            else:
                return 'создан'

        elif self.message.text == 'Обратная связь':
            markup = types.InlineKeyboardMarkup()
            markup.row_width = 1

            switch_button_1 = types.InlineKeyboardButton(text='Перейти в чат',
                                                         url='https://t.me/DoK2412')
            switch_button_2 = types.InlineKeyboardButton(text='Написать письмо',
                                                         callback_data='письмо')
            markup.add(switch_button_1, switch_button_2)

            self.bot.send_message(self.message.chat.id, 'Для улучшения работы бота Вы можете написать лично разработчику, либо оставить обратную связь на почту.', reply_markup=markup)
            self.bot.set_state(self.message.from_user.id, self.message.chat.id)

        elif self.message.text == 'Добавить заметку':
            calendar, step = DetailedTelegramCalendar(calendar_id=1,
                                                      locale='ru', min_date=datetime.date.today()).build()
            self.bot.send_message(self.message.chat.id,
                             'Укажите год.',
                             reply_markup=calendar)

        elif self.message.text == 'Заметки на день':
            user = User.get_user(self.message.chat.id)
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            user.date_note = date
            note = WorkingNotes().get_notes(self.message, date)
            if len(note) == 0:
                self.bot.send_message(self.message.chat.id, "На сегодня заметки отсутствуют.")
            else:
                WorkingNotes().sending_notes(self.message, user, self.bot, note)
        elif self.message.text == 'Заметки по датам':
            WorkingNotes().view_notes(self.message.from_user.id, self.bot, self.message)
        elif self.message.text == 'Записать в блокнот':
            return 'блокнот'
        elif self.message.text == 'Записи в блокноте':
            user_id = Authorization.user_id(self.message.from_user.id)
            user = User.get_user(self.message.chat.id)
            with Session(engin) as session:
                user_notebook = session.exec(select(Notebook).where(Notebook.user_id == user_id)).all()
            if len(user_notebook) == 0:
                self.bot.send_message(self.message.chat.id, "Отсутствуют записи в блокноте.")
            else:
                WorkingNotebook().get_notebook(self.message, user, self.bot, user_notebook)


class Feedbacks(object):

    def __init__(self, message, bot):
        self.message = message
        self.bot = bot

    def sending_message(self, user_teleg_id):
        message = self.message.text
        data = datetime.datetime.now()
        print(user_teleg_id)
        user_id = Authorization.user_id(user_teleg_id)
        with Session(engin) as session:
            massege = Feedback(user_id=user_id,
                               description=message,
                               creation_date=str(data))
            session.add(massege)
            session.commit()

        self.bot.send_message(self.message.chat.id,
                              'Сообщение сохранено.',
                              )
        self.bot.set_state(self.message.from_user.id, self.message.chat.id)


class WorkingNotes(object):

    def save_note(self, user_data, nate, user_teleg_id, sticker=None):
        """
        сохранение заметки
        """

        data = datetime.datetime.now()
        user_id = Authorization.user_id(user_teleg_id)
        with Session(engin) as session:
            massege = Notes(user_id=user_id,
                            date=str(user_data),
                            nate=nate,
                            creation_date=str(data),
                            sticker=sticker)
            session.add(massege)
            session.commit()
        return True

    def view_notes(self, user_teleg_id, bot, message):
        user_id = Authorization.user_id(user_teleg_id)
        with Session(engin) as session:
            user_view = session.exec(select(Notes).where(Notes.user_id == user_id)).all()

        if len(user_view) == 0:
            bot.send_message(message.chat.id, "У вас еще нет заметок.")
        else:
            markup = types.InlineKeyboardMarkup()
            list_bottom = list()
            markup.row_width = 1
            for view in user_view:
                if view.date not in list_bottom:
                    list_bottom.append(str(view.date))
                    markup.add(types.InlineKeyboardButton(text=str(view.date),
                                                          callback_data=str(view.date)))
            bot.send_message(message.chat.id, "Выберите дату в которой у вас есть заметки", reply_markup=markup)

    def get_notes(self, message, date_notes=None):
        """
        получение заметок пользователя по дате
        """
        if date_notes is None:
            date_notes = message.data
        user_id = Authorization.user_id(message.from_user.id)
        with Session(engin) as session:
            user_view = session.exec(select(Notes).where(Notes.user_id == user_id, Notes.date == date_notes)).all()
        return user_view

    def editing_note(self, bot, message, user):

        markup = types.InlineKeyboardMarkup()
        for i in range(len(user.big_user_nate)):
            if user.big_user_nate[i].startswith(user.user_nate[:-3]):
                markup.add(types.InlineKeyboardButton(text="Удалить заметку",
                                                      callback_data="Кнопка удалить"))
                markup.add(types.InlineKeyboardButton(text="Изменить заметку",
                                                      callback_data="Кнопка изменить"))
                markup.add(types.InlineKeyboardButton(text="Просмотреть полностью",
                                                      callback_data="Кнопка просмотреть"))
                break
        else:
            markup.add(types.InlineKeyboardButton(text="Удалить заметку",
                                                  callback_data="Кнопка удалить"))
            markup.add(types.InlineKeyboardButton(text="Изменить заметку",
                                                  callback_data="Кнопка изменить"))
        bot.send_message(message.from_user.id, "Редактирование заметок", reply_markup=markup)

    def note_detete(self, message, text_nate, date_note):
        user_id = Authorization.user_id(message.from_user.id)
        with Session(engin) as session:
            user_view = session.exec(select(Notes).where(Notes.user_id == user_id, Notes.date == date_note, Notes.nate == text_nate)).one()
            session.delete(user_view)
            session.commit()

    def nate_appdata(self, message, text_nate, date_note):
        user_id = Authorization.user_id(message.from_user.id)
        with Session(engin) as session:
            user_view = session.exec(
                select(Notes).where(Notes.user_id == user_id, Notes.date == date_note, Notes.nate == text_nate)).one()
            user_view.nate = text_nate + ' ' + message.text
            session.add(user_view)
            session.commit()
            session.refresh(user_view)

    def sending_notes(self, message, user, bot, note):
        markup = types.InlineKeyboardMarkup()
        for nat in note:
            if len(nat.nate) >= 21:
                user.big_user_nate.append(nat.nate)
                text = nat.nate[:16] + '...'
                markup.add(types.InlineKeyboardButton(resize_keyboard=True, text=str(text),
                                                      callback_data='Заметка ' + str(text)))
            else:
                markup.add(types.InlineKeyboardButton(resize_keyboard=True, text=str(nat.nate),
                                                      callback_data='Заметка ' + str(nat.nate)))
        bot.send_message(message.from_user.id,
                         f"При необходимости просмотреть полностью, удалить или изменить заметку нажмите на нее.",
                         reply_markup=markup)


class WorkingNotebook(object):

    def save_notebook(self, message, bot, name, text):
        user_id = Authorization.user_id(message.from_user.id)
        data = datetime.datetime.now()
        if len(name) >= 21:
            name = name[:16] + '...'
        with Session(engin) as session:
            massege = Notebook(user_id=user_id,
                               creation_date=str(data),
                               name=name,
                               text=text)
            session.add(massege)
            session.commit()
        bot.send_message(message.chat.id, "Текст успешно сохранен")

    def get_notebook(self, message, user, bot, note_book):
        markup = types.InlineKeyboardMarkup()
        for book in note_book:
                markup.add(types.InlineKeyboardButton(resize_keyboard=True, text=str(book.name),
                                                      callback_data='Блокнот ' + str(book.name)))
        bot.send_message(message.from_user.id,
                         f"При необходимости просмотреть полностью, удалить или изменить заметку нажмите на нее.",
                         reply_markup=markup)

    def editing_notebook(self, bot, message):

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Удалить текст",
                                              callback_data="Удалить текст"))
        markup.add(types.InlineKeyboardButton(text="Изменить текст",
                                              callback_data="Изменить текст"))
        markup.add(types.InlineKeyboardButton(text="Просмотреть текст",
                                              callback_data="Кнопка посмотреть текст"))

        bot.send_message(message.from_user.id, "Редактирование заметок", reply_markup=markup)

    def get_text_notebook(self, bot, message, user):
        user_id = Authorization.user_id(message.from_user.id)
        with Session(engin) as session:
            user_notebook = session.exec(select(Notebook).where(Notebook.user_id == user_id, Notebook.name == user.big_user_note_book)).one()
            bot.send_message(message.from_user.id, user_notebook.text)

    def delete_text_notebook(self, bot, message, user):
        user_id = Authorization.user_id(message.from_user.id)
        with Session(engin) as session:
            user_view = session.exec(
                select(Notebook).where(Notebook.user_id == user_id, Notebook.name == user.big_user_note_book)).one()
            session.delete(user_view)
            session.commit()
        bot.send_message(message.from_user.id, "Запись удалена.")

    def update_text_notebook(self, message, bot, user, text_notebook):
        user_id = Authorization.user_id(message.from_user.id)
        with Session(engin) as session:
            user_notebook = session.exec(
                select(Notebook).where(Notebook.user_id == user_id, Notebook.name == user.big_user_note_book)).one()
            user_notebook.text = text_notebook + ' ' + message.text
            session.add(user_notebook)
            session.commit()
            session.refresh(user_notebook)
        bot.send_message(message.from_user.id, "Запись изменена.")


