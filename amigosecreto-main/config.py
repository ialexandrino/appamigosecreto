import os

class Config:
    SECRET_KEY = 'sua_chave_secreta_aqui'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///amigosecreto.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
