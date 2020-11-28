from flask import Flask, render_template, redirect, url_for, flash
from flask_login import current_user, login_required, logout_user, login_user, LoginManager
from models import add_user, user_exist, read_latest_100_notes, create_note, remove_note, get_note, update_note, get_user
from forms import LoginForm, RegisterForm, NoteForm
from flask_bootstrap import Bootstrap
# import pymysql
from gevent.pywsgi import WSGIServer
import os


app = Flask(__name__)
# #mysql = MySQL(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = "You must be logged in to access this page."
login_manager.login_view = "login"

SECRET_KEY = b'\xe2\xaf\xbc:\xdd'
app.config['SECRET_KEY'] = SECRET_KEY
# app.config['MYSQL_HOST'] = '127.0.0.1'
# app.config['MYSQL_HOST'] = '127.0.0.1'
# app.config['MYSQL_USER'] = os.environ.get('CLOUD_SQL_USERNAME')
# app.config['MYSQL_PASSWORD'] = os.environ.get('CLOUD_SQL_PASSWORD')
# app.config['MYSQL_DB'] = os.environ.get('CLOUD_SQL_DATABASE_NAME')


@login_manager.user_loader
def load_user(user_id: int):
    return get_user(int(user_id))


@app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html", title="Forbidden"), 403


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html", title="Page Not Found"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("errors/500.html", title="Server Error"), 500



@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', title="Welcome")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        success = add_user(email, password)
        if success:
            flash('Thanks for registering')
            return redirect(url_for('login'))
        else:
            flash('User already exist')

    return render_template('register.html', form=form, title="Register")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = user_exist(email, password)
        #print(user.email)
        if user:
            print("this runs")
            print(login_user(user))
            return redirect(url_for("notes"))
        else:
            flash("Invalid email or password.")

    return render_template("login.html", form=form, title="Login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have successfully been logged out.")
    return redirect(url_for("login"))


@app.route('/notes', methods=['GET'])
@login_required
def notes():
    user_id = current_user.id
    user_notes = read_latest_100_notes(user_id)
    return render_template('notes.html', notes=user_notes, title="Notes")


@app.route('/notes/add', methods=['GET', 'POST'])
@login_required
def add_note():
    form = NoteForm()
    if form.validate_on_submit():
        user_id = current_user.id
        create_note(user_id, form.note.data)
        flash("You have successfully added a new note.")
        return redirect(url_for("notes"))
    return render_template("updateNote.html", add_note=True, form=form, title="Add Note")


@app.route('/notes/edit/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id: int):
    user_id = current_user.id
    cur_note = get_note(user_id, note_id)
    form = NoteForm(obj=cur_note)
    if form.validate_on_submit():
        update_note(user_id, note_id, form.note.data)
        flash("You have successfully updated your note.")
        return redirect(url_for("notes"))
    return render_template("updateNote.html", add_note=False, form=form, title="Edit Note")


@app.route('/notes/delete/<int:note_id>', methods=['GET'])
@login_required
def delete_note(note_id: int):
    user_id = current_user.id
    remove_note(user_id, note_id)
    flash("You have successfully deleted the note.")
    return redirect(url_for("notes"))


if __name__ == '__main__':
    #app.run(host='127.0.0.1', port=8080, debug=True)
    http_server = WSGIServer(('', 8080), app)
    http_server.serve_forever()
