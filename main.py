"""Main module with all processing functions"""

from flask import Flask, render_template, redirect, session, request
from flask_login import LoginManager, login_user, current_user, \
    login_required, logout_user
from flask_restful import Api
from forms import LoginForm, RegisterForm, EditAccountForm, \
    ChangePasswordForm, AddPostForm, EditPostForm, ChangeAvatarForm, SearchForm
from data.__all_models import users, post
from data import db_session
import users_resourse
import datetime
import math
import os

# Classes extracting
User = users.User
Post = post.Post

# Flask settings
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

# API settings
api = Api(app)
api.add_resource(users_resourse.UsersListResource, '/api/users')
api.add_resource(users_resourse.UsersResource, '/api/users/<int:user_id>')

# Database initialization
db_session.global_init("db/database.sqlite")

# Authorization manager initialization
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'please_register'

# Pages settings
ONE_PAGE_SUBSCRIBERS_COUNT = 10
ONE_PAGE_POSTS_COUNT = 10


# Function for authorization manager
@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


# Authorization page function
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template(
            'login.html', error="Неправильный логин или пароль", form=form
        )
    return render_template('login.html', form=form)


# Logout function
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Password reliability checking function
def check_password(password):
    digit = False
    alpha = False

    for i in password:
        if i in '0123456789':
            digit = True
        if i.lower() in 'qwertyuiopasdfghjklzxcvbnmйцу' \
                        'кенгшщзхъфывапролджэячсмитьбю':
            alpha = True

    if not alpha:
        return 'В пароле должны быть буквы'

    if password.upper() == password or password.lower() == password:
        return 'В пароле должны быть заглавные и строчные буквы'

    if not digit:
        return 'В пароле должны быть цифры'

    return 'OK'


# Registration page function
@app.route('/register', methods=['GET', 'POST'])
def register():
    session = db_session.create_session()
    form = RegisterForm()
    if form.validate_on_submit():
        if session.query(User).filter(User.login == form.login.data).first():
            return render_template(
                'register_form.html',
                form=form,
                error='Пользователь с таким логином уже существует'
            )

        password_check = check_password(form.password.data)
        if password_check != 'OK':
            return render_template('register_form.html', form=form,
                                   error=password_check)

        new_user = User()
        new_user.login = form.login.data
        new_user.set_password(form.password.data)
        new_user.registration_date = datetime.datetime.now()
        session.add(new_user)
        session.commit()
        return redirect('/')
    return render_template('register_form.html', form=form)


# User page function
@app.route('/user/<int:user_id>/<int:page_number>', methods=['GET', 'POST'])
@login_required
def user_page(user_id, page_number):
    session1 = db_session.create_session()
    if current_user.is_authenticated:
        user = session1.query(User).filter(User.id == user_id).first()
        cur_user = session1.query(User).filter(
            User.id == current_user.id
        ).first()

        posts = list(user.posts)
        page_info = {
            'page_number': page_number,
            'pages_count': math.ceil(
                len(list(user.posts)) / ONE_PAGE_POSTS_COUNT
            )
        }

        if 'sort_post_mode' in session:
            sort_post_mode = session['sort_post_mode']
        else:
            sort_post_mode = 1

        sort_post_mode = int(sort_post_mode)

        if sort_post_mode == 1:
            posts.sort(key=lambda post: post.id, reverse=True)
        elif sort_post_mode == 2:
            posts.sort(key=lambda post: post.id)
        elif sort_post_mode == 3:
            posts.sort(
                key=lambda post: len(list(post.liked_users)), reverse=True
            )

        if len(posts) > ONE_PAGE_POSTS_COUNT:
            if page_number <= page_info['pages_count']:
                posts = posts[(page_number - 1) * ONE_PAGE_POSTS_COUNT:
                              page_number * ONE_PAGE_POSTS_COUNT]
            else:
                return redirect(f'/user/{user_id}')

        if user:
            return render_template(
                'user_base.html',
                user=user,
                current_user=cur_user,
                posts_list=posts,
                page_info=page_info,
                back_url='/user/{{ current_user.id }}/{{ page_info.page_number }}'
            )
        else:
            return redirect('/')
    else:
        return 'Зарегайся пж, мне лень это место делать'


# Function for unauthorized user
@app.route('/please_register_or_auth', methods=['GET', 'POST'])
def please_register():
    return render_template('please_register.html')


# Function for subscribe to user
@app.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    args = dict(request.args)
    session = db_session.create_session()
    user = session.query(User).filter(User.id == args['user_id']).first()
    cur_user = session.query(User).filter(User.id == current_user.id).first()
    if user:
        if user.id != current_user.id:
            if user.private_account:
                if user not in cur_user.requested_subscriptions:
                    cur_user.requested_subscriptions.append(user)
                if cur_user not in user.requested_subscribers:
                    user.requested_subscribers.append(cur_user)
            else:
                if user not in current_user.subscriptions:
                    session.merge(current_user).subscriptions.append(user)
                if current_user not in user.subscribers:
                    user.subscribers.append(session.merge(current_user))
            session.commit()

        return redirect(args['back_url'])
    else:
        return redirect('/')


# Function for subscription cancelling
@app.route('/cancel_subscription', methods=['GET', 'POST'])
@login_required
def cancel_subscription():
    args = dict(request.args)
    session = db_session.create_session()
    user = session.query(User).filter(User.id == args['user_id']).first()
    if user:
        if user.id != current_user.id:
            if user in current_user.subscriptions:
                session.merge(current_user).subscriptions.remove(user)
            if current_user in user.subscribers:
                user.subscribers.remove(session.merge(current_user))
            if user.private_account:
                if user in current_user.requested_subscriptions:
                    session.merge(current_user).requested_subscriptions.remove(user)
                if current_user in user.requested_subscribers:
                    user.requested_subscribers.remove(session.merge(current_user))

            session.commit()
            return redirect(args['back_url'])
    else:
        return redirect('/')


# Function for subscriber deleting
@app.route('/delete_subscriber', methods=['GET', 'POST'])
@login_required
def delete_subscriber():
    args = dict(request.args)
    session = db_session.create_session()
    user = session.query(User).filter(User.id == args['user_id']).first()
    cur_user = session.query(User).filter(User.id == current_user.id).first()
    if user:
        if user.id != cur_user.id:
            if user in cur_user.subscribers:
                cur_user.subscribers.remove(user)
            if cur_user in user.subscriptions:
                user.subscriptions.remove(cur_user)
            session.commit()
            return redirect(args['back_url'])

    else:
        return redirect('/')


# Function for subscriber accepting
@app.route('/accept_subscriber', methods=['GET', 'POST'])
@login_required
def accept_subscriber():
    if current_user.private_account:
        args = dict(request.args)
        session = db_session.create_session()

        cur_user = session.query(User).filter(
            User.id == current_user.id
        ).first()

        user = session.query(User).filter(User.id == args['user_id']).first()
        if user:
            if user.id != current_user.id:
                if user not in list(cur_user.subscribers):
                    cur_user.subscribers.append(user)
                if user in list(cur_user.requested_subscribers):
                    cur_user.requested_subscribers.remove(user)
                if cur_user not in list(user.subscriptions):
                    user.subscriptions.append(cur_user)
                if cur_user in list(user.requested_subscriptions):
                    user.requested_subscriptions.remove(cur_user)

                session.commit()

            return redirect(args['back_url'])

        else:
            return redirect('/')
    else:
        return redirect('/')


# Function for post sorting mode editing
@app.route('/set_sort_post_mode', methods=['GET', 'POST'])
@login_required
def set_sort_post_mode():
    args = dict(request.args)
    session['sort_post_mode'] = args['type']
    return redirect(args['back_url'])


# Account editing page function
@app.route('/edit_account', methods=['GET', 'POST'])
@login_required
def edit_account():
    form = EditAccountForm(obj=current_user)
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()

        if user.login != form.login.data and session.query(User).filter(
                User.login == form.login.data).first():

            return render_template(
                'edit_account.html',
                form=form,
                error='Пользователь с таким логином уже существует'
            )

        user.login = form.login.data
        user.description = form.description.data

        session.commit()
        return redirect('/my_user')
    return render_template('edit_account.html', form=form)


# Avatar changing function
@app.route('/change_avatar', methods=['GET', 'POST'])
@login_required
def change_avatar():
    form = ChangeAvatarForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        filenames_list = os.listdir(path='static/img')
        last_photo_id = int(filenames_list[-1].split('.')[0])
        new_photo_id = last_photo_id + 1
        f = form.file.data
        if f.filename.split('.')[-1] != 'jpg':
            return render_template('change_avatar_page.html', form=form,
                                   error='Фото должно быть формата .jpg')
        f.save(f'static/img/{new_photo_id}.jpg')
        user.avatar_photo_id = new_photo_id
        session.commit()
        return redirect('/my_user')
    return render_template('change_avatar_page.html', form=form)


# Function for redirecting user from simple url to own page
@app.route('/my_user', methods=['GET', 'POST'])
@login_required
def my_user():
    return redirect(f'/user/{current_user.id}')


# Function for redirecting user from simple url to own subscriptions
@app.route('/my_subscriptions', methods=['GET', 'POST'])
@login_required
def my_subscriptions():
    return redirect(f'/subscriptions/{current_user.id}')


# Function for redirecting user from simple url to own subscribers
@app.route('/my_subscribers', methods=['GET', 'POST'])
@login_required
def my_subscribers():
    return redirect(f'/subscribers/{current_user.id}')


# Settings page function
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template('settings_page.html', current_user=current_user)


# Account private settings changing page function
@app.route('/change_private', methods=['GET', 'POST'])
@login_required
def change_private():
    args = dict(request.args)
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    user.private_account = {'on': True, 'off': False}[args['private']]
    session.commit()
    return redirect(args['back_url'])


# Account password changing page function
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()

        if not user.check_password(form.old_password.data):
            return render_template('change_password.html', form=form,
                                   error='Старый пароль неверен')

        password_check = check_password(form.new_password.data)
        if password_check != 'OK':
            return render_template('change_password.html', form=form,
                                   error=password_check)

        user.set_password(form.new_password.data)
        session.commit()
        return redirect('/settings')
    return render_template('change_password.html', form=form)


# Function for redirecting user from simple url to user page
@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@app.route('/user/<int:user_id>/', methods=['GET', 'POST'])
@login_required
def redirect_user(user_id):
    return redirect(f'/user/{user_id}/1')


# Function for redirecting user from simple url to user subscriptions
@app.route('/subscriptions/<int:user_id>', methods=['GET', 'POST'])
@app.route('/subscriptions/<int:user_id>/', methods=['GET', 'POST'])
@login_required
def redirect_subscriptions(user_id):
    return redirect(f'/subscriptions/{user_id}/1')


# Function for redirecting user from simple url to user subscribers
@app.route('/subscribers/<int:user_id>', methods=['GET', 'POST'])
@app.route('/subscribers/<int:user_id>/', methods=['GET', 'POST'])
@login_required
def redirect_subscribers(user_id):
    return redirect(f'/subscribers/{user_id}/1')


# Subscribers page function
@app.route('/subscribers/<int:user_id>/<int:page_number>', methods=['GET', 'POST'])
@login_required
def subscribers(user_id, page_number):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        subscribers = list(user.subscribers)
        page_info = {
            'page_number': page_number,
            'pages_count': math.ceil(
                len(list(user.subscribers)) / ONE_PAGE_SUBSCRIBERS_COUNT
            )
        }
        if len(subscribers) > ONE_PAGE_SUBSCRIBERS_COUNT:
            if page_number <= page_info['pages_count']:
                subscribers = subscribers[
                              (page_number - 1) * ONE_PAGE_SUBSCRIBERS_COUNT:
                              page_number * ONE_PAGE_SUBSCRIBERS_COUNT
                              ]
            else:
                return redirect('/')

        if user.private_account and current_user.id != user.id:
            if current_user not in user.subscriptions and current_user != user:
                return redirect(f'/user/{user.id}')

        if len(subscribers) <= 0:
            if not (current_user.id == user.id and len(
                    list(current_user.requested_subscribers)) > 0):
                return redirect(f'/user/{user.id}')

        return render_template(
            'subscribers_list.html',
            subscribers=subscribers,
            user=user,
            current_user=current_user,
            page_info=page_info
        )
    else:
        return redirect('/')


# Subscriptions page function
@app.route('/subscriptions/<int:user_id>/<int:page_number>', methods=['GET', 'POST'])
@login_required
def subscriptions(user_id, page_number):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        subscriptions = list(user.subscriptions)
        page_info = {
            'page_number': page_number,
            'pages_count': math.ceil(
                len(list(user.subscriptions)) / ONE_PAGE_SUBSCRIBERS_COUNT
            )
        }
        if len(subscriptions) > ONE_PAGE_SUBSCRIBERS_COUNT:
            if page_number <= page_info['pages_count']:
                subscriptions = subscriptions[
                                (page_number - 1) * ONE_PAGE_SUBSCRIBERS_COUNT:
                                page_number * ONE_PAGE_SUBSCRIBERS_COUNT
                                ]
            else:
                return redirect('/')

        if user.private_account and current_user.id != user.id:
            if current_user not in user.subscriptions:
                return redirect(f'/user/{user.id}')

        if len(subscriptions) <= 0:
            return redirect(f'/user/{user.id}')

        return render_template(
            'subscriptions_list.html',
            subscriptions=subscriptions,
            user=user,
            current_user=current_user,
            page_info=page_info
        )
    else:
        return redirect('/')


# Requested subscribers page function
@app.route('/requested_subscribers/<int:page_number>', methods=['GET', 'POST'])
@login_required
def requested_subscribers(page_number):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    subscribers = list(user.requested_subscribers)
    page_info = {
        'page_number': page_number,
        'pages_count': math.ceil(
            len(list(user.subscriptions)) / ONE_PAGE_SUBSCRIBERS_COUNT
        )
    }
    if len(subscribers) > ONE_PAGE_SUBSCRIBERS_COUNT:
        if page_number <= page_info['pages_count']:
            subscribers = subscribers[
                          (page_number - 1) * ONE_PAGE_SUBSCRIBERS_COUNT:
                          page_number * ONE_PAGE_SUBSCRIBERS_COUNT
                          ]
        else:
            return redirect('/')
    if len(subscribers) <= 0:
        return redirect('/my_subscribers')

    return render_template(
        'requested_subscribers_page.html',
        subscribers=subscribers,
        user=user,
        current_user=current_user,
        page_info=page_info
    )


# Post adding function
@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = AddPostForm()
    session = db_session.create_session()
    if form.validate_on_submit():
        new_post = Post()
        new_post.author = session.merge(current_user)
        new_post.title = form.title.data
        new_post.text = form.text.data
        now_datetime = datetime.datetime.now()
        new_post.creating_date = datetime.datetime.now()
        new_post.creating_date_norm_view = date_to_normal_view(now_datetime)
        session.add(new_post)
        session.commit()
        return redirect(f'/user/{current_user.id}/1')
    return render_template('add_edit_post_page.html', form=form, add=True)


# Post editing function
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    args = dict(request.args)
    session = db_session.create_session()
    post = session.query(Post).filter(Post.id == post_id).first()
    if post.author.id == current_user.id:
        form = EditPostForm(obj=post)
        if form.validate_on_submit():
            post.title = form.title.data
            post.text = form.text.data
            now_datetime = datetime.datetime.now()
            post.editing_date = now_datetime
            post.editing_date_norm_view = date_to_normal_view(now_datetime)
            session.commit()
            return redirect(args['back_url'])
        return render_template('add_edit_post_page.html', form=form, add=False)
    return redirect('/')


# Post deleting funcion
@app.route('/delete_post', methods=['GET', 'POST'])
@login_required
def delete_post():
    args = dict(request.args)
    session = db_session.create_session()
    post = session.query(Post).filter(Post.id == args['post_id']).first()
    if post.author.id == current_user.id:
        session.delete(post)
        session.commit()
        return redirect(args['back_url'])
    return redirect('/')


# Function to convert date to normal view
def date_to_normal_view(datetime):
    months_list = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн',
                   'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    month = months_list[datetime.month - 1]
    returned_text = f'{datetime.day} {month} {datetime.year} ' \
                    f'в {datetime.hour}:{str(datetime.minute).rjust(2, "0")}'
    return returned_text


# Function for setting like
@app.route('/set_like', methods=['GET', 'POST'])
@login_required
def set_like():
    args = dict(request.args)
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    post = session.query(Post).filter(Post.id == args['post_id']).first()
    if args['set'] == 'on':
        if user not in post.liked_users:
            post.liked_users.append(user)
    else:
        if user in post.liked_users:
            post.liked_users.remove(user)
    session.commit()
    return redirect(args['back_url'])


# Function for redirecting from simple url
@app.route('/posts/')
@app.route('/posts')
@login_required
def redirect_posts():
    return redirect('/posts/1')


# Main page function
@app.route('/posts/<int:page_number>')
@login_required
def posts(page_number):
    session1 = db_session.create_session()
    if current_user.is_authenticated:
        cur_user = session1.query(User).filter(User.id == current_user.id).first()
        posts = list()
        for i in cur_user.subscriptions:
            for s in i.posts:
                posts.append(s)
        for i in cur_user.posts:
            posts.append(i)
        page_info = {
            'page_number': page_number,
            'pages_count': math.ceil(len(posts) / ONE_PAGE_POSTS_COUNT)
        }

        if 'sort_post_mode' in session:
            sort_post_mode = session['sort_post_mode']
        else:
            sort_post_mode = 1

        sort_post_mode = int(sort_post_mode)

        if sort_post_mode == 1:
            posts.sort(key=lambda post: post.id, reverse=True)
        elif sort_post_mode == 2:
            posts.sort(key=lambda post: post.id)
        elif sort_post_mode == 3:
            posts.sort(
                key=lambda post: len(list(post.liked_users)), reverse=True
            )

        if len(posts) > ONE_PAGE_POSTS_COUNT:
            if page_number <= page_info['pages_count']:
                posts = posts[(page_number - 1) * ONE_PAGE_POSTS_COUNT:
                              page_number * ONE_PAGE_POSTS_COUNT]
            else:
                return redirect(f'/posts')

        return render_template(
            'main_page.html',
            current_user=current_user,
            posts_list=posts,
            page_info=page_info
        )


# Search page function
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    try:
        form = SearchForm()
        session = db_session.create_session()
        if form.validate_on_submit():
            if form.search_type.data == '2':
                users = session.query(User).filter(
                    User.login.like(f'%{form.text.data}%')
                ).all()

            elif form.search_type.data == '1':
                users = session.query(User).filter(
                    User.id == int(form.text.data)
                ).all()

            else:
                users = session.query(User).all()
            return render_template(
                'search_page.html',
                form=form,
                search_results=users
            )

        return render_template('search_page.html', form=form)
    except Exception:
        return redirect('/search')


# Function to redirect from main page
@app.route('/')
def main_page():
    return redirect('/posts')


# Main function
def main():
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port)


# 404 error page function
@app.errorhandler(404)
def not_found(error):
    return render_template('404_error_page.html')


# Site launch
if __name__ == '__main__':
    main()
