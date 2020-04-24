from flask import Flask
from data import db_session
from data.__all_models import users
import random
import datetime
from flask import render_template, redirect
from flask_login import LoginManager
from flask_login import login_user, current_user, login_required, logout_user
from flask import make_response, jsonify
from flask import url_for, request
from forms import LoginForm, RegisterForm
from flask_restful import Api
import requests
import os
import math

User = users.User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

db_session.global_init("db/database.sqlite")
session = db_session.create_session()

login_manager = LoginManager()
login_manager.init_app(app)

ONE_PAGE_SUBSCRIBERS_COUNT = 2

PAGE_ID = [
    '/',
    '/user/{user_id}'
]


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               title='Авторизация',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User()
        new_user.login = form.login.data
        new_user.set_password(form.password.data)
        new_user.registration_date = datetime.datetime.now()
        session.add(new_user)
        session.commit()
        return redirect('/')
    return render_template('register_form.html', form=form)


@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
def user_page(user_id):
    if current_user.is_authenticated:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            return render_template('user_base.html', user=user, current_user=current_user)
        else:
            return redirect('/')
    else:
        return 'Зарегайся пж, мне лень это место делать'


@app.route('/subscribe/<int:user_id>', methods=['GET', 'POST'])
@login_required
def subscribe(user_id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        if user.id != current_user.id:
            if user.private_account:
                if user not in current_user.requested_subscriptions:
                    session.merge(current_user).requested_subscriptions.append(user)
                if current_user not in user.new_requested_subscribers:
                    user.new_requested_subscribers.append(session.merge(current_user))
            else:
                if user not in current_user.subscriptions:
                    session.merge(current_user).subscriptions.append(user)
                if current_user not in user.subscribers:
                    user.subscribers.append(session.merge(current_user))
            session.commit()

        return redirect(f'/user/{user.id}')

    else:
        return redirect('/')


@app.route('/cancel_subscription', methods=['GET', 'POST'])
@login_required
def cancel_subscription():
    args = dict(request.args)
    user_id = int(args['id'])
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        if user.id != current_user.id:
            if user in current_user.subscriptions:
                session.merge(current_user).subscriptions.remove(user)
            if current_user in user.subscribers:
                user.subscribers.remove(session.merge(current_user))
            if user.private_account:
                if user in current_user.requested_subsriptions:
                    session.merge(current_user).requested_subscriptions.remove(user)
                if current_user in user.new_requested_subscribers:
                    user.new_requested_subscribers.append(session.merge(current_user))
                if current_user in user.requested_subscribers:
                    user.requested_subscribers.append(session.merge(current_user))

            session.commit()
            return redirect(args['back_url'])
    else:
        return redirect('/')


@app.route('/delete_subscriber', methods=['GET', 'POST'])
@login_required
def delete_subscriber():
    args = dict(request.args)
    user_id = int(args['id'])
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        if user.id != current_user.id:
            if user in current_user.subscribers:
                session.merge(current_user).subscribers.remove(user)
            if current_user in user.subscriptions:
                user.subscriptions.remove(session.merge(current_user))

            session.commit()
            return redirect(args['back_url'])

    else:
        return redirect('/')


@app.route('/accept_subscriber/<int:user_id>', methods=['GET', 'POST'])
@login_required
def accept_subscriber(user_id):
    if current_user.private_account:
        session = db_session.create_session()
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            if user.id != current_user.id:
                if user in current_user.req:
                    session.merge(current_user).subscribers.remove(user)
                if current_user in user.subscriptions:
                    user.subscriptions.remove(session.merge(current_user))

                session.commit()

            return redirect(f'/user/{user.id}')

        else:
            return redirect('/')


@app.route('/subscribers/<int:user_id>/<int:page_number>', methods=['GET', 'POST'])
def subscribers(user_id, page_number):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        subscribers = list(user.subscribers)
        page_info = {
            'page_number': page_number,
            'pages_count': math.ceil(len(list(user.subscribers)) / ONE_PAGE_SUBSCRIBERS_COUNT)
        }
        if len(subscribers) > ONE_PAGE_SUBSCRIBERS_COUNT:
            if page_number <= page_info['pages_count']:
                subscribers = subscribers[(page_number - 1) * ONE_PAGE_SUBSCRIBERS_COUNT:
                                              page_number * ONE_PAGE_SUBSCRIBERS_COUNT]
            else:
                return redirect('/')

        if user.private_account:
            if current_user not in user.subscriptions:
                return redirect(f'/user/{user.id}')

        if len(subscribers) <= 0:
            return redirect(f'/user/{user.id}')

        return render_template('subscribers_list.html', subscribers=subscribers,
                               user=user, current_user=current_user, page_info=page_info)
    else:
        return redirect('/')


@app.route('/subscriptions/<int:user_id>/<int:page_number>', methods=['GET', 'POST'])
def subscriptions(user_id, page_number):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        subscriptions = list(user.subscriptions)
        page_info = {
            'page_number': page_number,
            'pages_count': math.ceil(len(list(user.subscriptions)) / ONE_PAGE_SUBSCRIBERS_COUNT)
        }
        if len(subscriptions) > ONE_PAGE_SUBSCRIBERS_COUNT:
            if page_number <= page_info['pages_count']:
                subscriptions = subscriptions[(page_number - 1) * ONE_PAGE_SUBSCRIBERS_COUNT:
                                              page_number * ONE_PAGE_SUBSCRIBERS_COUNT]
            else:
                return redirect('/')

        if user.private_account:
            if current_user not in user.subscriptions:
                return redirect(f'/user/{user.id}')

        if len(subscriptions) <= 0:
            return redirect(f'/user/{user.id}')

        return render_template('subscriptions_list.html', subscriptions=subscriptions,
                               user=user, current_user=current_user, page_info=page_info)
    else:
        return redirect('/')


@app.route('/')
def index():
    return render_template('base.html', title='ПЯЛ', current_user=current_user)


def main():
    app.run()


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    main()
