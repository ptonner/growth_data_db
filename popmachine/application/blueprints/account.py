from ..forms import SearchForm, RegisterForm, LoginForm
from ..app import mail
from ..safeurl import is_safe_url
from popmachine import models

from sqlalchemy import not_, or_
import flask
from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import login_required, current_user, login_user
from flask_mail import Message

profile = Blueprint('account', __name__)


@profile.route('/register', methods=["GET", "POST"])
def create_account():
    searchform = SearchForm()
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_confirm.data:
            flask.flash('passwords do not match!')
            return redirect(url_for('create_account'), method='GET')

        # print type(form.password.data)

        user = models.User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data.encode('utf-8')
        )
        current_app.machine.session.add(user)
        current_app.machine.session.commit()

        # Now we'll send the email confirmation link
        subject = "Confirm your email"

        token = current_app.ts.dumps(user.email, salt='email-confirm-key')

        confirm_url = url_for(
            'account.confirm_email',
            token=token,
            _external=True)

        html = render_template(
            'accounts/email-activate.html',
            confirm_url=confirm_url, searchform=searchform)

        msg = Message(subject,
                      sender="popmachine.db@gmail.com",
                      recipients=[user.email], html=html)
        mail.send(msg)

        # print user.email, html
        flask.flash(
            'account created, please check your email for verification.')

        return redirect(url_for("misc.index"))

    return render_template("accounts/create.html", form=form, searchform=searchform)


@profile.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = current_app.ts.loads(
            token, salt="email-confirm-key", max_age=86400)
    except:
        abort(404)

    user = current_app.machine.session.query(models.User).filter_by(
        email=email).one_or_none()

    if user is None:
        flask.abort(404)

    user.email_confirmed = True

    current_app.machine.session.add(user)
    current_app.machine.session.commit()

    return redirect(url_for('misc.signin'))


@profile.route('/login', methods=['GET', 'POST'])
def login():

    searchform = SearchForm()
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():

        user = current_app.machine.session.query(models.User).filter_by(
            username=request.form['name']).one_or_none()

        if user is None or not user.is_correct_password(str(request.form['password'])):
            flask.flash('Incorrect username or password.')
            return flask.redirect(flask.url_for('login', form=form, method='GET'))

        login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('misc.index'))
    return flask.render_template('login.html', form=form, searchform=searchform)


@profile.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('misc.index'))
