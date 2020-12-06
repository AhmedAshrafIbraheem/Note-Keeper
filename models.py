import os
import sys
import pymysql
from passlib.hash import sha256_crypt

db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_password = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
read_db_connection_name = os.environ.get('CLOUD_SQL_READ_DB')

if os.environ.get('GAE_ENV') == 'standard':
    # If deployed, use the local socket interface for accessing Cloud SQL
    unix_socket = '/cloudsql/{}'.format(db_connection_name)
    read_unix_socket = '/cloudsql/{}'.format('notekeeperapp-296101:us-east4:notekeepersql-replica')
    cnx = pymysql.connect(user=db_user, password=db_password, unix_socket=unix_socket, db=db_name)
    rd_cnx = pymysql.connect(user=db_user, password=db_password, unix_socket=read_unix_socket, db=db_name)

else:
    # If running locally, use the TCP connections instead
    # Set up Cloud SQL Proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
    # so that your application can use 127.0.0.1:3306 to connect to your
    # Cloud SQL instance
    dbhost = '127.0.0.1'
    rdhost = '127.0.0.1:1234'
    cnx = pymysql.connect(user='master_user', password='noteappmaster', host=dbhost, db='note_database')
    rd_cnx = pymysql.connect(user='master_user', password='noteappmaster', host=dbhost, port=1234, db='note_database')


class User:
    def __init__(self, user_id: int, email: str):
        self.id = user_id
        self.email = email


class Note:
    def __init__(self, note_id: int, user_id: int, note: str):
        self.id = note_id
        self.user = user_id
        self.note = note


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


def user_exist(email: str, password: str):
    # Return user if exits and None otherwise
    try:
        cur = rd_cnx.cursor()
        cur.execute("SELECT * FROM Users WHERE email='{}' LIMIT 1;".format(email))
        ret = cur.fetchone()
        rd_cnx.commit()
        cur.close()
        if sha256_crypt.verify(password, ret[2]):
            return User(ret[0], ret[1])
    except:
        return None


def get_user(user_id: int) -> User:
    try:
        cur = rd_cnx.cursor()
        cur.execute("SELECT email FROM Users WHERE id={} LIMIT 1;".format(user_id))
        ret = cur.fetchone()
        rd_cnx.commit()
        cur.close()
        return User(user_id, ret[0])
    except:
        pass


def create_note(user_id: int, note: str):
    try:
        cur = cnx.cursor()
        cur.execute("INSERT INTO Notes (user_id, note) VALUES ({}, '{}');".format(user_id, note))
        cnx.commit()
        cur.close()
    except:
        pass


def get_note(user_id: int, note_id: int):
    try:
        cur = rd_cnx.cursor()
        cur.execute("SELECT * FROM Notes WHERE id={} AND user_id= {} LIMIT 1;".format(note_id, user_id))
        rd_cnx.commit()
        ret = cur.fetchone()
        cur.close()
        if ret:
            return Note(ret[0], ret[1], ret[2])
    except:
        pass
    return None


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


def read_latest_100_notes(user_id: int) -> [Note]:
    try:
        cur = rd_cnx.cursor()
        cur.execute("SELECT * FROM Notes WHERE user_id= {} LIMIT 100;".format(user_id))
        ret = cur.fetchall()
        rd_cnx.commit()
        cur.close()

        return [Note(note[0], note[1], note[2]) for note in ret]
    except Exception as e:
        print("Read error" + str(e))
    return []
