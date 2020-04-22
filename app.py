"""Example flask app that stores passwords hashed with Bcrypt. Yay!"""

from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Tweet
from forms import UserForm, TweetForm

# for intergrity error - making sure no duplicate username or so
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL', 'postgres:///auth_demo')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = False
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'abc123')
app.config['DEBUG_TB_INTERCEEPT_REDIRECTS'] = False

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route("/")
def homepage():
    """Show homepage with links to site areas."""

    return render_template("index.html")

@app.route("/tweets", methods=['GET', 'POST'])
def show_tweets():

    # if not session['user_id']:
    if 'user_id' not in session:
        flash("Please sign in first to see tweets", "danger")
        return redirect('/')
    
    form = TweetForm()

    all_tweets = Tweet.query.all()

    if form.validate_on_submit():
        text = form.text.data

        new_tweet = Tweet(text=text, user_id=session['user_id'])
        db.session.add(new_tweet)
        db.session.commit()

        flash(f"{new_tweet.user.username} you just created a new tweet!", "success")
        return redirect("/tweets")

    return render_template('tweets.html', form=form, tweets=all_tweets)


@app.route('/tweets/<int:id>', methods=['POST'])
def delete_tweet(id):
    """ delete tweet """
    
    # protection from serverside request 
    if 'user_id' not in session:
        flash("please log in first!", "danger")
        return redirect('/login')

    #protection from client side users
    tweet = Tweet.query.get_or_404(id)
    if tweet.user_id == session['user_id']:
        db.session.delete(tweet)
        db.session.commit()

        flash("Tweet deleted!", "info")
        return redirect('/tweets')
    flash("You do not have the permission", "danger")
    return redirect('/tweets')

@app.route("/register", methods=['GET', 'POST'])
def register_user():

    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.username.data
        new_user = User.register(username, password)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            #form error display
            form.username.errors.append("User name is already taken. Please pick another one")

            return render_template('register.html', form=form)

        session['user_id'] = new_user.id

        flash(f"Welcome {username}!, successfully created your account!", "success")
        return redirect('/tweets')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:

            session['user_id'] = user.id
            
            # flash error
            flash(f"Welcome back {user.username}!", "primary")
            return redirect('/tweets')
        else:
            # form validation error
            form.username.errors = ['Invalid username/password']

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_user():
    session.pop('user_id')
    flash("Good bye! see you soon", "info")
    return redirect('/')