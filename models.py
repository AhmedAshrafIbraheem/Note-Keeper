from flask_login import UserMixin
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt


class User(UserMixin):
    def __init__(self, user_id: int, email: str, password: str):
        self.id = user_id
        self.email = email
        self.password = password


class Note:
    def __init__(self, note_id: int, user_id: int, note: str):
        self.id = note_id
        self.user = user_id
        self.note = note


def add_user(email: str, password: str, mysql: MySQL) -> bool:
    hashed_password = sha256_crypt.encrypt(password)
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Users (email, password) VALUES ('{}', '{}');".format(email, hashed_password))
        mysql.connection.commit()
        cur.close()
        return True
    except:
        return False


def user_exist(email: str, password: str, mysql: MySQL):
    # Return user if exits and None otherwise
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Users WHERE email='{}' LIMIT 1;".format(email))
        ret = cur.fetchone()
        cur.close()
        if sha256_crypt.verify(password, ret[2]):
            return User(ret[0], ret[1], ret[2])
    except:
        return None


def get_user(user_id: int, mysql: MySQL) -> User:
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Users WHERE id={} LIMIT 1;".format(user_id))
        ret = cur.fetchone()
        cur.close()
        return User(ret[0], ret[1], ret[2])
    except:
        pass


def create_note(user_id: int, note: str, mysql: MySQL):
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Notes (user_id, note) VALUES ({}, '{}');".format(user_id, note))
        mysql.connection.commit()
        cur.close()
    except:
        pass


def get_note(user_id: int, note_id: int, mysql: MySQL):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Notes WHERE id={} AND user_id= {} LIMIT 1;".format(note_id, user_id))
        ret = cur.fetchone()
        cur.close()
        if ret:
            return Note(ret[0], ret[1], ret[2])
    except:
        pass
    return None


def update_note(user_id: int, note_id: int, edited_note: str, mysql: MySQL):
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE Notes SET note='{}' WHERE id={} AND user_id= {} LIMIT 1;".format(edited_note, note_id, user_id))
        mysql.connection.commit()
        cur.close()
    except:
        pass


def remove_note(user_id: int, note_id: int, mysql: MySQL):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM Notes WHERE id={} AND user_id= {} LIMIT 1;".format(note_id, user_id))
        mysql.connection.commit()
        cur.close()
    except:
        pass


def read_latest_100_notes(user_id: int, mysql: MySQL) -> [Note]:
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Notes WHERE user_id= {} LIMIT 100;".format(user_id))
        ret = cur.fetchall()
        cur.close()
        return [Note(note[0], note[1], note[2]) for note in ret]
    except:
        return []

