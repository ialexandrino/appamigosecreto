import os
class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', '')


    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ.get('MYSQL_USER', 'admin_user')}:"
        f"{os.environ.get('MYSQL_PASSWORD', '')}@"
        f"{os.environ.get('MYSQL_HOST', 'amigosecreto')}/"
        f"{os.environ.get('MYSQL_DB', 'amigosecreto')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
