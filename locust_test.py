#
# import requests
#
# deploy_test = False
#
# if deploy_test:
#     URL = 'https://notekeeperapp-296101.uk.r.appspot.com/login'
# else:
#     URL = 'http://127.0.0.1:8080/login'
#
#
# client = requests.session()
#
# r = client.get(URL)
#
# csrftoken = client.cookies
# csrf_token = {}
#
# csrf_token['session'] = csrftoken
# csrf_token = str(b'\xe2\xaf\xbc:\xdd')
# login_data = dict(email='acoolmind13@gmail.com', password='12345678')#{login:"somepersonsname", password:"supergreatpassword", csrfmiddlewaretoken:csrftoken}
# client.post(URL, data=login_data )
#
# note_data = dict(note="This from locust test 2 after change after change change")
# client.post('http://127.0.0.1:8080/notes/add', data=note_data )
# client.get('http://127.0.0.1:8080/logout')
# client.close()

import time
from locust import HttpUser, task

note_data = dict(note="register form implement")
login_data = dict(email='locust12345@gmail.com', password='12345678')
register_data = dict(email = "", password='12345678')

user_counter = 50


class QuickTasks(HttpUser):
    # @task
    # def add_note(self):
    #     self.client.post("/notes/add", data=note_data)
    #     time.sleep(1)

    @task
    def get_notes(self):
        self.client.get("/notes")
        time.sleep(1)

    def on_start(self):
        global user_counter
        login_data['email'] = "User{}@gmail.com".format(user_counter)
        user_counter += 1
        self.client.post("/login", data=login_data)

    def on_stop(self):
        self.client.get("/logout")
