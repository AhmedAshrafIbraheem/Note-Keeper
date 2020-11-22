from flask_login import UserMixin


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


users = {0: User(0, 'testorg1@testorg1.com', '123456789')}
notes = {}


def add_user(email: str, password: str) -> bool:
    for us in users.values():
        if email.__eq__(us.email):
            return False

    user_id = len(users)
    user = User(user_id, email, password)
    users[user_id] = user
    return True


def user_exist(email: str, password: str):
    # Return user if exits and None otherwise
    for us in users.values():
        if email.__eq__(us.email):
            if password.__eq__(us.password):
                return us
            break
    return None


def get_user(user_id: int) -> User:
    return users[user_id]


def read_latest_100_notes(user_id: int) -> [Note]:
    ret = []
    for ns in notes.values():
        if ns.user == user_id:
            ret.append(ns)
    return ret


def create_note(user_id: int, note: str):
    note_id = len(notes)
    note = Note(note_id, user_id, note)
    notes[note_id] = note


def get_note(user_id: int, note_id: int):
    note = notes[note_id]
    if note.user == user_id:
        return note
    return None


def update_note(user_id: int, note_id: int, edited_note: str):
    note = notes[note_id]
    if note.user == user_id:
        notes[note_id].note = edited_note


def remove_note(user_id: int, note_id: int):
    note = notes[note_id]
    if note.user == user_id:
        notes.pop(note_id)
