import datetime
import time


from sqlmodel import Session, select
from database.connection_db import engin
from database.sql_requests import Users, Feedback, Notes, Notebook

from aiogram_calendar import SimpleCalendar, get_user_locale

from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from servise.state import Form



class UserPanel(object):
    def __init__(self, callback=None, message=None, user=None):
        self.callback = callback
        self.message = message
        self.user = user

    async def authorization(self):
        date = datetime.datetime.now()
        with Session(engin) as session:
            add_useer = Users(telegram_id=self.callback.from_user.id,
                              registration_date=date,
                              active=True,
                              telegram_teg=self.callback.from_user.username)
            session.add(add_useer)
            session.commit()
        return True

    async def user_verification(self):
        with Session(engin) as session:
            user_view = session.exec(
                select(Users).where(Users.telegram_id == self.user.telegram_id)).all()
            if len(user_view) == 0:
                return None
            else:
                print(user_view[0].id)
                self.user.user_id = user_view[0].id


async def get_calendar(callback, min_date, max_date):
    calendar = SimpleCalendar(locale='ru_RU.utf8', show_alerts=True)
    calendar.set_dates_range(datetime.datetime.strptime(str(min_date), '%Y-%m-%d'),
                             datetime.datetime.strptime(str(max_date), '%Y-%m-%d'))
    return calendar

class Note(object):
    def __init__(self, callback=None, message=None, user=None):
        self.callback = callback
        self.message = message
        self.user = user

    async def adding_note(self):
        min_date = datetime.date.today()
        max_date = "{:%Y-%m-%d}".format(datetime.datetime.strptime('31.12.2030', '%d.%m.%Y'))
        await self.callback.message.answer('Укажите дату: ',
                                           reply_markup=await (
                                               await get_calendar(self.callback, min_date, max_date)).start_calendar())

    async def get_day_and_month(self, callback_data, state):
        min_date = datetime.date.today()
        max_date = "{:%Y-%m-%d}".format(datetime.datetime.strptime('31.12.2030', '%d.%m.%Y'))
        calendar = await get_calendar(self.callback, min_date, max_date)
        selected, date = await calendar.process_selection(self.callback, callback_data)
        if selected and date:
            await self.callback.message.delete()
            date_list = [date.strftime('%d'), date.strftime('%m'), date.strftime('%Y')]
            self.user.data = datetime.datetime.strptime(f'{date_list[0]}.{date_list[1]}.{date_list[2]}', '%d.%m.%Y').date()

            await state.set_state(Form.note)
            await self.callback.message.answer(
                "Введите вашу заметку",
                reply_markup=ReplyKeyboardRemove(),
            )

    async def recording_note_in_db(self, state):
        await state.update_data(name=self.message.text)
        date = datetime.datetime.now()
        with Session(engin) as session:
            massege = Notes(user_id=self.user.user_id,
                            date=self.user.data,
                            note=self.message.text,
                            creation_date=date,
                            sticker=None)
            session.add(massege)
            session.commit()
        await state.clear()
        await self.message.answer("Заметка сохранена")

    async def notes_for_day(self):
        date = datetime.datetime.now().date()
        with Session(engin) as session:
            user_note = session.exec(select(Notes).where(Notes.user_id == self.user.user_id, Notes.date == str(date))).all()
            if len(user_note) == 0:
                await self.callback.message.answer("На сегодня у Вас нет заметок.")
            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                for note in user_note:
                    keyboard.inline_keyboard.append(
                        [
                            InlineKeyboardButton(text=note.note,
                                                 callback_data='Заметка '+ str(note.id))
                        ]
                    )
                await self.callback.message.answer(f'Заметка на {date.strftime("%d.%m.%Y")}\n\nПри необходимости изменить заметку нажмите на нее.', reply_markup=keyboard)

    async def note_processing(self, notes_id):
        with Session(engin) as session:
            note = session.exec(
                select(Notes).where(Notes.id == notes_id)).one()
            self.user.note_id = notes_id
            await Note(callback=self.callback, user=self.user).actions_with_notes(len(note.note))

    async def deleting(self):
        with Session(engin) as session:
            user_view = session.exec(
                select(Notes).where(Notes.user_id == self.user.user_id, Notes.id == self.user.note_id)).one()
            session.delete(user_view)
            session.commit()
        self.user.note_id = None
        await self.callback.message.answer("Заметка удалена")

    async def view_note(self):
        with Session(engin) as session:
            user_view = session.exec(
                select(Notes).where(Notes.id == self.user.note_id)).one()
            await self.callback.message.answer(user_view.note)

    async def notes_date(self):
        with Session(engin) as session:
            user_note = session.exec(
                select(Notes).where(Notes.user_id == self.user.user_id)).all()
            day_list = list()
            if len(user_note) == 0:
                await self.callback.message.answer("У Вас нет заметок.")
            else:
                for note in user_note:
                    if note.date in day_list:
                        continue
                    else:
                        day_list.append(note.date)
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                for day in day_list:
                    keyboard.inline_keyboard.append(
                        [
                            InlineKeyboardButton(text=day,
                                                 callback_data='Выбранный день ' + day)
                        ]
                    )
                await self.callback.message.answer(
                    f'Выберите необходимый день.',
                    reply_markup=keyboard)

    async def specific_day(self, day):
        with Session(engin) as session:

            user_note = session.exec(
                select(Notes).where(Notes.user_id == self.user.user_id, Notes.date == day)).all()
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            for note in user_note:
                keyboard.inline_keyboard.append(
                    [
                        InlineKeyboardButton(text=note.note,
                                             callback_data='Заметка ' + str(note.id))
                    ]
                )
            day = day.split('-')
            day = day[2]+'.'+day[1]+'.'+day[0]
            await self.callback.message.answer(
                f'Заметка на {day}\n\nПри необходимости изменить заметку нажмите на нее.',
                reply_markup=keyboard)

    async def feed_back(self):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='Написать письмо',
                                     callback_data='Написать письмо')
            ],
            [
                InlineKeyboardButton(text='Перейти в чвт',
                                     url='https://t.me/DoK2412')
            ]
            ])
        await self.callback.message.answer(
            f'При возникновении ошибки вы можете написать мне лично, либо воспользоваться формой обратной связи.',
            reply_markup=keyboard)

    async def letter(self, state):
        await state.update_data(name=self.message.text)
        date = datetime.datetime.now()

        with Session(engin) as session:
            massege = Feedback(user_id=self.user.user_id,
                               description=self.message.text,
                               creation_date=date)
            session.add(massege)
            session.commit()
        await state.clear()
        await self.message.answer("Письмо отправлено")

    async def writing_name_notepad(self, state):
        self.user.name_notebook = self.message.text
        await state.clear()
        await state.set_state(Form.notepad)
        await self.message.answer(
            "Введите необходимой текст",
            reply_markup=ReplyKeyboardRemove(),
        )

    async def writing_notepad_db(self, state):
        date = datetime.datetime.now()
        with Session(engin) as session:
            massege = Notebook(user_id=self.user.user_id,
                               creation_date=date,
                               name=self.user.name_notebook,
                               text=self.message.text)
            session.add(massege)
            session.commit()
        await state.clear()
        await self.message.answer("Запись сохранена в блокноте.")

    async def get_records(self):
        with Session(engin) as session:
            user_notebook = session.exec(
                select(Notebook).where(Notebook.user_id == self.user.user_id)).all()
            if len(user_notebook) == 0:
                await self.callback.message.answer("У Вас нет записей в блокноте.")

            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                for notebook in user_notebook:
                    keyboard.inline_keyboard.append(
                        [
                            InlineKeyboardButton(text=notebook.name,
                                                 callback_data='Блокнот ' + str(notebook.id))
                        ]
                    )
                await self.callback.message.answer(
                    f'Выберите необходимую запись.',
                    reply_markup=keyboard)

    async def return_notepad(self):
        self.user.notebook_id = self.callback.data.split(' ')[1]
        with Session(engin) as session:
            user_notebook = session.exec(
                select(Notebook).where(Notebook.user_id == self.user.user_id, Notebook.id == self.user.notebook_id)).one()
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text='Удалить',
                                         callback_data='Удалить запись')
                ]
            ])
            await self.callback.message.answer(
                user_notebook.text,
                reply_markup=keyboard)

    async def delete_entry(self):
        with Session(engin) as session:
            user_view = session.exec(
                select(Notebook).where(Notebook.user_id == self.user.user_id, Notebook.id == self.user.notebook_id)).one()
            session.delete(user_view)
            session.commit()
        self.user.notebook_id = None
        await self.callback.message.answer("Запись удалена.")







    async def actions_with_notes(self, notes_len):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            if notes_len > 46:
                keyboard.inline_keyboard.append(
                    [
                        InlineKeyboardButton(text='Просмотр заметки',
                                             callback_data='Просмотр заметки')
                    ])
                keyboard.inline_keyboard.append(
                    [
                        InlineKeyboardButton(text='Удалить заметку',
                                             callback_data='Удалить заметку')
                    ])
            else:
                keyboard.inline_keyboard.append(
                    [
                        InlineKeyboardButton(text='Удалить заметку',
                                             callback_data='Удалить заметку')
                    ])

            await self.callback.message.answer(
                f'Выберите необходимое действие с заметкой.',
                reply_markup=keyboard)

    # async def delete_message(self):
    #     await self.callback.message.delete()







