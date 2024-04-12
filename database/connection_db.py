from pydantic import BaseModel
from sqlmodel import Session, create_engine

from setting import config


class App(BaseModel):
    """
    Конфигурация приложения
    """
    server_host: str
    server_post: int


class DataBase(BaseModel):
    """
    Конфигурация Базы Данных
    """
    user: str
    password: str
    db_name: str
    host: str
    port: str

    def DSN(self):
        return f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}'


class Config(BaseModel):
    App: App
    DataBase: DataBase


config = Config(**config)


engin = create_engine(
    config.DataBase.DSN()
)


def get_session():
    '''
    Реализации сессии для работы с базой данных pss
    :return:
    '''
    with Session(engin) as session:
        yield session