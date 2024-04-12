"""Файл предназначен для реализации класса пользователя"""

class User:
    user = dict()

    def __init__(self, chat_id):

        self.id_chat = chat_id         # id чата *
        self.data = None
        self.date_note = None
        self.user_nate = None
        self.message_id = None
        self.message_nate_id = None
        self.big_user_nate = list()
        self.name_notebook = None
        self.text_notebook = None
        self.big_user_note_book = list()


    @classmethod
    def get_user(cls, chat_id):
        if chat_id in cls.user.keys():
            return cls.user[chat_id]
        else:
            return cls.add_user(chat_id)

    @classmethod
    def add_user(cls, chat_id):
        cls.user[chat_id] = User(chat_id)
        return cls.user[chat_id]