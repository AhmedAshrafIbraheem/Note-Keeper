import os
import sys
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

    chosen_read = choice([read_unix_socket, read_2_unix_socket])

    cnx = pymysql.connect(user=db_user, password=db_password, unix_socket=unix_socket, db=db_name)
    rd_cnx = pymysql.connect(user=db_user, password=db_password, unix_socket=chosen_read, db=db_name)


    def cross_read_connect():
        return pymysql.connect(user=db_user, password=db_password, unix_socket=read_cross_unix_socket, db=db_name)






else:
    # If running locally, use the TCP connections instead
    # Set up Cloud SQL Proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
    # so that your application can use 127.0.0.1:3306 to connect to your
    # Cloud SQL instance
    dbhost = '127.0.0.1'

    chosen_read = choice([1234, 1235])
    print(chosen_read)
    cnx = pymysql.connect(user='master_user', password='noteappmaster', host=dbhost, db='note_database')
    rd_cnx = pymysql.connect(user='master_user', password='noteappmaster', host=dbhost, port=chosen_read, db='note_database')

    def cross_read_connect():
        return pymysql.connect(user='master_user', password='noteappmaster', port=1236, db='note_database')
    # cnx = pymysql.connect(user='note_keeper', password='', host='localhost', db='NoteKeeperDB')
    # rd_cnx = cnx



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
        cur = cnx.cursor()
        cur.execute("INSERT INTO Users (email, password) VALUES ('{}', '{}');".format(email, hashed_password))
        cnx.commit()
        cur.close()
        return True
    except pymysql.OperationalError as e:
        # if e[0] == 2002:
        #     print("Could not connect to database")
        #   return False
        pass
    except pymysql.IntegrityError as Ie:
        print("Duplicate entry " + str(sys.exc_info()[1]))
        pass
    return False


def create_note(user_id: int, note: str):
    try:
        dt_string = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = cnx.cursor()
        cur.execute("INSERT INTO Notes (user_id, note, time_created) "
                    "VALUES ({}, '{}', '{}');".format(user_id, note, dt_string))
        cnx.commit()
        cur.close()
    except:
        pass


def update_note(user_id: int, note_id: int, edited_note: str):
    try:
        cur = cnx.cursor()
        cur.execute(
            "UPDATE Notes SET note='{}' WHERE id={} AND user_id= {} LIMIT 1;".format(edited_note, note_id, user_id))
        cnx.commit()
        cur.close()
    except:
        pass


def remove_note(user_id: int, note_id: int):
    try:
        cur = cnx.cursor()
        cur.execute("DELETE FROM Notes WHERE id={} AND user_id= {} LIMIT 1;".format(note_id, user_id))
        cnx.commit()
        cur.close()
    except:
        pass


def _user_exist(email: str, connection):
    cur = connection.cursor()
    cur.execute("SELECT * FROM Users WHERE email='{}' LIMIT 1;".format(email))
    connection.commit()
    ret = cur.fetchone()
    cur.close()
    return ret



def user_exist(email: str, password: str):
    # Return user if exits and None otherwise
    try:
        ret = _user_exist(email, rd_cnx)
        if sha256_crypt.verify(password, ret[2]):
            return User(ret[0], ret[1])
    except:
        rd_cross_cnx = cross_read_connect()
        ret = _user_exist(email, rd_cross_cnx)
        rd_cross_cnx.close()
        if sha256_crypt.verify(password, ret[2]):
            return User(ret[0], ret[1])


def _get_user(user_id: int, connection):
    cur = connection.cursor()
    cur.execute("SELECT email FROM Users WHERE id={} LIMIT 1;".format(user_id))
    connection.commit()
    ret = cur.fetchone()
    cur.close()
    return ret

def get_user(user_id: int) -> User:
    try:
        ret = _get_user(user_id, rd_cnx)
        return User(user_id, ret[0])
    except pymysql.OperationalError:
        rd_cross_cnx = cross_read_connect()
        ret = _get_user(user_id, rd_cross_cnx)
        rd_cross_cnx.close()
        return User(user_id, ret[0])


def _get_note(user_id: int, note_id: int, connection):
    cur = connection.cursor()
    cur.execute("SELECT * FROM Notes WHERE id={} AND user_id= {} LIMIT 1;".format(note_id, user_id))
    connection.commit()
    ret = cur.fetchone()
    cur.close()
    return ret

def get_note(user_id: int, note_id: int):
    try:
        ret = _get_note(user_id, note_id, rd_cnx)
        if ret:
            return Note(ret[0], ret[1], ret[2], ret[3])
    except pymysql.OperationalError:
        rd_cross_cnx = cross_read_connect()
        ret = _get_note(user_id, note_id, rd_cross_cnx)
        rd_cross_cnx.close()
        if ret:
            return Note(ret[0], ret[1], ret[2], ret[3])
    return None

def _read_latest_100_notes(user_id: int, connection):
    cur = connection.cursor()
    cur.execute("SELECT * FROM Notes WHERE user_id= {} ORDER BY id DESC LIMIT 100;".format(user_id))
    connection.commit()
    ret = cur.fetchall()
    cur.close()
    return ret

def read_latest_100_notes(user_id: int) -> [Note]:
    try:
        ret = _read_latest_100_notes(user_id, rd_cnx)
        return [Note(note[0], note[1], note[2], note[3]) for note in ret]
    except pymysql.OperationalError:
        rd_cross_cnx = cross_read_connect()
        ret = _read_latest_100_notes(user_id, rd_cross_cnx)
        rd_cross_cnx.close()
        return [Note(note[0], note[1], note[2], note[3]) for note in ret]
    return []


def _read_100_notes(user_id: int, timestamp, connection):
    cur = connection.cursor()
    cur.execute("SELECT * FROM Notes WHERE user_id= {} AND time_created <= '{}' "
                "ORDER BY id DESC LIMIT 100;".format(user_id, timestamp))
    connection.commit()
    ret = cur.fetchall()
    cur.close()
    return ret

def read_100_notes(user_id: int, date: dt.date, time: dt.time) -> [Note]:
    timestamp = dt.datetime.combine(date, time)
    try:
        ret = _read_100_notes(user_id, timestamp, rd_cnx)
        return [Note(note[0], note[1], note[2], note[3]) for note in ret]
    except pymysql.OperationalError:
        rd_cross_cnx = cross_read_connect()
        ret = _read_100_notes(user_id, timestamp, rd_cross_cnx)
        rd_cross_cnx.close()
        return [Note(note[0], note[1], note[2], note[3]) for note in ret]
    return []


