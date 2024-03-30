import math
import sqlite3
import time
import datetime


class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def getMenu(self):
        sql = '''SELECT * FROM Mainmenu'''
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res:
                return res
        except:
            print("Error get data from DataBase")
        return []

    def addPost(self, site, author, title, description, urlToImage, url, text):
        if author is None:
            author = ""
        try:
            self.__cur.execute("SELECT COUNT() as 'count' FROM posts WHERE url LIKE ?", (url,))
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print("Статья с данным url уже есть!")
                return False
            tm = math.floor(time.time())
            self.__cur.execute("INSERT INTO posts VALUES (NULL,?,?,?,?,?,?,?,?)",
                               (site, author, title, description, url,
                                urlToImage, text, tm))
            self.__db.commit()
        except Exception as e:
            print(f"Error adding post. {e}")
            return False
        return True

    def getPostAnonce(self):
        try:
            self.__cur.execute(f"SELECT id, title, description, url, urlToImage, time FROM posts ORDER BY time DESC")
            res = self.__cur.fetchall()
            if res:
                res_arr = []
                for el in res:
                    timestamp = el['time']
                    dt_object = datetime.datetime.fromtimestamp(timestamp)
                    res_arr.append({'id': el['id'], 'title': el['title'], 'description': el['description'],
                                    'url': el['url'], 'urlToImage': el['urlToImage'],
                                    'time': dt_object.strftime("%H:%M:%S, %d.%m.%Y")})
                return res_arr
        except sqlite3.Error as e:
            print(f"Ошибка при получении постов из БД. {e}")
        return []

    def getPost(self, alias):
        try:
            self.__cur.execute(f"SELECT author, title, text, time FROM posts WHERE id LIKE ? LIMIT 1", (alias,))
            res = self.__cur.fetchone()
            if res:
                timestamp = res['time']
                dt_object = datetime.datetime.fromtimestamp(timestamp)
                post_time = dt_object.strftime("%H:%M:%S, %d.%m.%Y")
                return res['title'], res['text'], post_time, res['author']
        except sqlite3.Error as e:
            print(f"Ошибка при получении поста из БД. {e}")
        return False, False, False, False

    def addUser(self, name, email, hpsw):
        try:
            self.__cur.execute(f"SELECT count() as count FROM users WHERE email LIKE '{email}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print("Такой пользователь уже есть")
                return False
            tm = math.floor(time.time())
            self.__cur.execute("INSERT INTO users VALUES(NULL,?,?,?,NULL,?)", (name, email, hpsw, tm))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления в БД" + str(e))
            return False
        return True

    def getUser(self, user_id):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE id = {user_id} LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False
            return res
        except sqlite3.Error as e:
            print(f"Ошибка при получении информации о пользователе из БД. {e}")
        return False

    def getUserByEmail(self, email):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email = '{email}' LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False
            print("Пользователь найден")
            return res
        except sqlite3.Error as e:
            print(f"Ошибка при получении информации о пользователе из БД. {e}")
        return False

    def updateUserAvatar(self, img, user_id):
        if not img:
            return False
        try:
            binary = sqlite3.Binary(img)
            self.__cur.execute(f"UPDATE users SET avatar = ? WHERE id = ?", (binary, user_id))
            self.__db.commit()

        except sqlite3.Error as e:
            print(f"Ошибка обновления аватара. {e}")
            return False
        return True