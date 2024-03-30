from flask import url_for
from flask_login import UserMixin


class UserLogin(UserMixin):
    def fromDB(self, user_id, db):
        self.__user = db.getUser(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user['id'])

    def getName(self):
        return self.__user['name'] if self.__user else "Нет имени"

    def getEmail(self):
        return self.__user['email'] if self.__user else "Нет email"

    def getAvatar(self, app):
        img = None
        if not self.__user["avatar"]:
            try:
                with app.open_resource(app.root_path + url_for('static', filename='img/default.png'), "rb") as file:
                    img = file.read()
            except FileNotFoundError as e:
                print(f"Дефолтный аватар не найден. {e}")
        else:
            img = self.__user['avatar']
        return img