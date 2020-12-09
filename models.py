import os
import datetime as dt
import pymysql
from random import choice
from passlib.hash import sha256_crypt

db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_password = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
read_db = os.environ.get('CLOUD_SQL_READ_DB')
read_db_2 = os.environ.get('CLOUD_SQL_READ_DB_2')
read_db_cross = os.environ.get('CLOUD_SQL_READ_DB_CROSS')


if os.environ.get('GAE_ENV') == 'standard':
    # If deployed, use the local socket interface for accessing Cloud SQL
    unix_socket = '/cloudsql/{}'.format(db_connection_name)
    read_unix_socket = '/cloudsql/{}'.format(read_db)
    read_2_unix_socket = '/cloudsql/{}'.format(read_db_2)
    read_cross_unix_socket = '/cloudsql/{}'.format(read_db_cross)

    def primary_connect():
        return pymysql.connect(user=db_user, password=db_password, unix_socket=unix_socket, db=db_name)

    def replica_read_connect():
        chosen_read = choice([read_unix_socket, read_2_unix_socket])
        return pymysql.connect(user=db_user, password=db_password, unix_socket=chosen_read, db=db_name)

    def cross_read_connect():
        return pymysql.connect(user=db_user, password=db_password, unix_socket=read_cross_unix_socket, db=db_name)

else:
    # If running locally, use the TCP connections instead
    # Set up Cloud SQL Proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
    # so that your application can use 127.0.0.1:3306 to connect to your
    # Cloud SQL instance
    dbhost = '127.0.0.1'

    def primary_connect():
        return pymysql.connect(user='master_user', password='noteappmaster', host=dbhost, db='note_database')

    def replica_read_connect():
        chosen_read = choice([1234, 1235])
        return pymysql.connect(user='master_user', password='noteappmaster', host=dbhost, port=chosen_read, db='note_database')

    def cross_read_connect():
        return pymysql.connect(user='master_user', password='noteappmaster', port=1236, db='note_database')


class User:
    def __init__(self, user_id: int, email: str):
        self.id = user_id
        self.email = email


class Note:
    def __init__(self, note_id: int, user_id: int, note: str, time_created: dt.datetime):
        self.id = note_id
        self.user = user_id
        self.note = note
        self.time_created = time_created


def add_user(email: str, password: str) -> bool:
    hashed_password = sha256_crypt.encrypt(password)
    try:
        cnx = primary_connect()
        cur = cnx.cursor()
        cur.execute("INSERT INTO Users (email, password) VALUES ('{}', '{}');".format(email, hashed_password))
        cnx.commit()
        cur.close()
        cnx.close()
        return True
    except:
        pass
    return False


def create_note(user_id: int, note: str):
    try:
        dt_string = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cnx = primary_connect()
        cur = cnx.cursor()
        cur.execute("INSERT INTO Notes (user_id, note, time_created) "
                    "VALUES ({}, '{}', '{}');".format(user_id, note, dt_string))
        cnx.commit()
        cur.close()
        cnx.close()
        return True
    except:
        return False


def update_note(user_id: int, note_id: int, edited_note: str):
    try:
        cnx = primary_connect()
        cur = cnx.cursor()
        cur.execute(
            "UPDATE Notes SET note='{}' WHERE id={} AND user_id= {} LIMIT 1;".format(edited_note, note_id, user_id))
        cnx.commit()
        cur.close()
        cnx.close()
        return True
    except:
        return False


def remove_note(user_id: int, note_id: int):
    try:
        cnx = primary_connect()
        cur = cnx.cursor()
        cur.execute("DELETE FROM Notes WHERE id={} AND user_id= {} LIMIT 1;".format(note_id, user_id))
        cnx.commit()
        cur.close()
        cnx.close()
        return True
    except:
        return False


def _user_exist(email: str, connect_func):
    try:
        connection = connect_func()
        cur = connection.cursor()
        cur.execute("SELECT * FROM Users WHERE email='{}' LIMIT 1;".format(email))
        connection.commit()
        ret = cur.fetchone()
        cur.close()
        connection.close()
        return ret
    except:
        return -1


def user_exist(email: str, password: str):
    # Return user if exits and None otherwise
    ret = _user_exist(email, replica_read_connect)
    if ret == -1:
        ret = _user_exist(email, cross_read_connect)
    if not ret or ret == -1:
        return None

    if sha256_crypt.verify(password, ret[2]):
        return User(ret[0], ret[1])

    return None


def _get_user(user_id: int, connect_func):
    try:
        connection = connect_func()
        cur = connection.cursor()
        cur.execute("SELECT email FROM Users WHERE id={} LIMIT 1;".format(user_id))
        ret = cur.fetchone()
        connection.commit()
        cur.close()
        connection.close()
        return ret
    except:
        return -1


def get_user(user_id: int) -> User:
    ret = _get_user(user_id, replica_read_connect)
    if ret == -1:
        ret = _get_user(user_id, cross_read_connect)
    if not ret or ret == -1:
        return None

    return User(user_id, ret[0])


def _get_note(user_id: int, note_id: int, connect_func):
    try:
        connection = connect_func()
        cur = connection.cursor()
        cur.execute("SELECT * FROM Notes WHERE id={} AND user_id= {} LIMIT 1;".format(note_id, user_id))
        ret = cur.fetchone()
        connection.commit()
        cur.close()
        connection.close()
        return ret
    except:
        return -1


def get_note(user_id: int, note_id: int):
    ret = _get_note(user_id, note_id, replica_read_connect)
    if ret == -1:
        ret = _get_note(user_id, note_id, cross_read_connect)
    if not ret or ret == -1:
        return None

    return Note(ret[0], ret[1], ret[2], ret[3])


def _read_latest_100_notes(user_id: int, connect_func):
    try:
        connection = connect_func()
        cur = connection.cursor()
        cur.execute("SELECT * FROM Notes WHERE user_id= {} ORDER BY id DESC LIMIT 100;".format(user_id))
        connection.commit()
        ret = cur.fetchall()
        cur.close()
        connection.close()
        return ret
    except:
        return -1


def read_latest_100_notes(user_id: int) -> [Note]:
    ret = _read_latest_100_notes(user_id, replica_read_connect)
    if ret == -1:
        ret = _read_latest_100_notes(user_id, cross_read_connect)
    if not ret or ret == -1:
        return []

    return [Note(note[0], note[1], note[2], note[3]) for note in ret]


def _read_100_notes(user_id: int, timestamp, connect_func):
    try:
        connection = connect_func()
        cur = connection.cursor()
        cur.execute("SELECT * FROM Notes WHERE user_id= {} AND time_created <= '{}' "
                    "ORDER BY id DESC LIMIT 100;".format(user_id, timestamp))
        connection.commit()
        ret = cur.fetchall()
        cur.close()
        connection.close()
        return ret
    except:
        return -1


def read_100_notes(user_id: int, date: dt.date, time: dt.time) -> [Note]:
    timestamp = dt.datetime.combine(date, time)
    ret = _read_100_notes(user_id, timestamp, replica_read_connect)
    if ret == -1:
        ret = _read_100_notes(user_id, timestamp, cross_read_connect)

    if not ret or ret == -1:
        return []

    return [Note(note[0], note[1], note[2], note[3]) for note in ret]

