import asyncio
import logging
import datetime


from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, Message

from aiogram_calendar import get_user_locale, SimpleCalendarCallback

from servise.state import Form



from user_data import User
from servise.replacement import UserPanel, Note, get_calendar

from setting import bot_token, bot_token_test

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # try:
    # await message.delete()
    user = User.get_user(message.chat.id)
    await UserPanel(message=message, user=user).user_verification()
    if user.user_id:
        keyboard = InlineKeyboardMarkup(inline_keyboard= [
            [
                InlineKeyboardButton(text='Добавить заметку',
                                              callback_data='Добавить заметку')
            ],
            [
                InlineKeyboardButton(text='Заметки на день',
                                        callback_data='Заметки на день'),
                InlineKeyboardButton(text='Заметки по датам',
                                        callback_data='Заметки по датам')
            ],
            [
                InlineKeyboardButton(text='Запись в блокнот',
                                        callback_data='Запись в блокнот'),
                InlineKeyboardButton(text='Посмотреть записи',
                                        callback_data='Записи в блокноте')
            ],
            [
                InlineKeyboardButton(text='Обратная связь',
                                        callback_data='Обратная связь')
                ]
        ])
        await message.answer('Добро пожаловать в главное меню.', reply_markup=keyboard)

    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='Авторизация',
                                     callback_data='Авторизация')
            ]
        ])
        await message.answer('Для использования бота вам необходимо авторизоваться', reply_markup=keyboard)


@dp.callback_query(F.data == "Авторизация")
async def send_random_value(callback: types.CallbackQuery):
    await callback.message.delete()
    authorization = await UserPanel(callback=callback).authorization()
    if authorization:
        await command_start_handler(callback.message)
    else:
        await callback.message.answer("Во время авторизации возникла ошибка.\nПовторите авторизацию.")
        await command_start_handler(callback.message)


@dp.callback_query(F.data == "Добавить заметку")
async def send_random_value(callback: types.CallbackQuery):
    # await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).adding_note()


@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback, callback_data, state: FSMContext):
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).get_day_and_month(callback_data, state)


@dp.message(Form.note)
async def cmd_numbers(message: Message, state: FSMContext):
    user = User.get_user(message.chat.id)
    await Note(message=message, user=user).recording_note_in_db(state)


@dp.callback_query(F.data == "Заметки на день")
async def day_notes(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).notes_for_day()


@dp.callback_query(F.data[:7] == "Заметка")
async def receiving_note(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).note_processing(callback.data.split(' ')[1])


@dp.callback_query(F.data == "Удалить заметку")
async def deleting_note(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).deleting()


@dp.callback_query(F.data == "Просмотр заметки")
async def view_one_note(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).view_note()


@dp.callback_query(F.data == "Заметки по датам")
async def notes_by_date(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).notes_date()


@dp.callback_query(F.data[:14] == "Выбранный день")
async def receiving_note(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).specific_day(callback.data.split(' ')[2])


@dp.callback_query(F.data == "Обратная связь")
async def feedback(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).feed_back()


@dp.callback_query(F.data == "Написать письмо")
async def naw_letter(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(Form.letter)
    await callback.message.answer(
        "Введите ваше сообщение",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(Form.letter)
async def write_letter(message: Message, state: FSMContext):
    await message.delete()
    user = User.get_user(message.chat.id)
    await Note(message=message, user=user).letter(state)


@dp.callback_query(F.data == "Запись в блокнот")
async def writing_in_notepad(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(Form.name_notepad)
    await callback.message.answer(
        "Введите наименование записи",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(Form.name_notepad)
async def write_letter(message: Message, state: FSMContext):
    await message.delete()
    user = User.get_user(message.chat.id)
    await Note(message=message, user=user).writing_name_notepad(state)


@dp.message(Form.notepad)
async def write_letter(message: Message, state: FSMContext):
    await message.delete()
    user = User.get_user(message.chat.id)
    await Note(message=message, user=user).writing_notepad_db(state)


@dp.callback_query(F.data == "Записи в блокноте")
async def writing_in_notepad(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).get_records()


@dp.callback_query(F.data[:7] == "Блокнот")
async def writing_in_notepad(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).return_notepad()


@dp.callback_query(F.data == "Удалить запись")
async def view_one_note(callback: types.CallbackQuery):
    await callback.message.delete()
    user = User.get_user(callback.message.chat.id)
    await Note(callback=callback, user=user).delete_entry()


async def main():
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

