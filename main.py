from flask import Flask, render_template, redirect, url_for, flash, session, request, g
from models import add_user, user_exist, read_latest_100_notes, create_note, remove_note, get_note, update_note, \
    get_user, read_100_notes
from flask_bootstrap import Bootstrap
from gevent.pywsgi import WSGIServer
from forms import LoginForm, RegisterForm, NoteForm, OlderNotesForm

app = Flask(__name__)
bootstrap = Bootstrap(app)


SECRET_KEY = b'\xe2\xaf\xbc:\xdd'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['WTF_CSRF_ENABLED'] = False

@app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html", title="Forbidden"), 403


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html", title="Page Not Found"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("errors/500.html", title="Server Error"), 500


@app.route('/favicon.ico')
def favicon():
    return "Note_Keepers"


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', title="Welcome")


# Get user email information for use in html
@app.before_request
def before_request():
    if 'user_id' in session:
        g.user = get_user(session['user_id'])


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

    return render_template('register.html', title="Register", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = user_exist(email, password)

        if user:
            session['user_id'] = user.id
            return redirect(url_for("notes"))
        else:
            flash("Invalid email or password.")

    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("You have successfully been logged out.")
    return redirect(url_for("login"))


@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'user_id' in session:
        user_id = session['user_id']
        form = OlderNotesForm()
        user_notes = []
        if form.validate_on_submit():
            date = form.date.data
            time = form.time.data
            user_notes = read_100_notes(user_id, date, time)
        else:
            user_notes = read_latest_100_notes(user_id)
        return render_template('notes.html', notes=user_notes, title="Notes", form=form)

    return redirect(url_for("login"))


@app.route('/notes/add', methods=['GET', 'POST'])
def add_note():
    if 'user_id' in session:
        form = NoteForm()
        if form.validate_on_submit():
            user_id = session['user_id']
            note = form.note.data
            create_note(user_id, note)
            flash("You have successfully added a new note.")
            return redirect(url_for("notes"))

        return render_template("updateNote.html", add_note=True, title="Add Note", form=form)

    return redirect(url_for("login"))


@app.route('/notes/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id: int):
    if 'user_id' in session:
        user_id = session['user_id']
        cur_note = get_note(user_id, note_id)
        form = NoteForm(obj=cur_note)
        if form.validate_on_submit():
            updated_note = form.note.data
            update_note(user_id, note_id, updated_note)
            flash("You have successfully updated your note.")
            return redirect(url_for("notes"))

        return render_template("updateNote.html", add_note=False, title="Edit Note", form=form)

    return redirect(url_for("login"))


@app.route('/notes/delete/<int:note_id>', methods=['GET'])
def delete_note(note_id: int):
    if 'user_id' in session:
        user_id = session['user_id']
        remove_note(user_id, note_id)
        flash("You have successfully deleted the note.")
        return redirect(url_for("notes"))

    return redirect(url_for("login"))


if __name__ == '__main__':
    #app.run(host='127.0.0.1', port=8080, debug=True)
    http_server = WSGIServer(('', 443), app)
    http_server.serve_forever()
