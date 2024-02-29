from flask import Flask, render_template, redirect, session, flash
#from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///flask_feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)
app.app_context().__enter__()
#toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():
    """Home page that redirects to register page"""
    if "username" not in session:
        flash("You need to register or log in!", "danger")
        return redirect('/register')
    return redirect(f'/users/{session['username']}')

@app.route('/register', methods=["GET", "POST"])
def register_user():
    """A form that when submitted will register/create a user"""
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            flash('This username already exists', "danger")
            return render_template('register.html', form=form)

        session['username'] = new_user.username
        flash('You have been registered', "success")
        return redirect(f'/users/{new_user.username}')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """A form to login a user and redirects to profile details page"""
    if "username" in session:
        return redirect(f"/users/{session['username']}")
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash("You're logged in!", 'success')
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            flash('Invalid username/password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout_user():
    """The user will be logged out and the session will be cleared"""
    session.clear()
    flash("You've logged out successfully")
    return redirect('/')

@app.route('/users/<username>')
def user_profile(username):
    """Shows details about the users and feedback they gave"""
    if "username" not in session:
        flash("You need to log in!", "danger")
        return redirect('/login')
    if session['username'] != username:
        flash("You can only view your profile", "danger")
        return redirect(f'/users/{session['username']}')

    user = User.query.filter_by(username=username).first()
    feedback = Feedback.query.filter_by(username=username).all()
    return render_template('profile.html', user=user, feedback=feedback)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """Removing users and their feedback"""
    if "username" not in session:
        flash("You need to log in!", "danger")
        return redirect('/login')
    if session['username'] != username:
        flash("You can only delete your profile", "danger")
        return redirect(f'/users/{session['username']}')
    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.clear()
    return redirect('/')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    """Form to add/process feedback"""
    if "username" not in session:
        flash("You need to log in!", "danger")
        return redirect('/login')
    if session['username'] != username:
        flash("You can only add feedback from your profile", "danger")
        return redirect(f'/users/{session['username']}')
    
    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        username = session['username']
        new_feedback = Feedback(title=title, content=content, username=username)
        db.session.add(new_feedback)
        db.session.commit()
        return redirect(f'/users/{session['username']}')
    return render_template('add_feedback.html', form=form)

@app.route('/feedback/<int:feedback_id>/update', methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Form to edit feedback"""
    if "username" not in session:
        flash("You need to log in!", "danger")
        return redirect('/login')

    feedback = Feedback.query.get(feedback_id)
    if session['username'] != feedback.username:
        flash("You can only update your feedback", "danger")
        return redirect(f'/users/{session['username']}')

    form = FeedbackForm(title=feedback.title, content=feedback.content)

    if form.validate_on_submit():
        edit_title = form.title.data
        edit_content = form.content.data
        feedback.title = edit_title
        feedback.content = edit_content
        feedback.username = feedback.username
        db.session.commit()
        return redirect(f'/users/{session['username']}')
    return render_template('update_feedback.html', form=form)

@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    """Deletes feedback and redirects to user's profile"""
    if "username" not in session:
        flash("You need to log in!", "danger")
        return redirect('/login')

    feedback = Feedback.query.get(feedback_id)
    if session['username'] != feedback.username:
        flash("You can only delete your feedback", "danger")
        return redirect(f'/users/{session['username']}')
    
    db.session.delete(feedback)
    db.session.commit()
    return redirect(f'/users/{session['username']}')
 