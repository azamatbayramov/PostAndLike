"""Forms classes"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length
from flask_wtf.file import FileField


# Registration form
class RegisterForm(FlaskForm):
    login = StringField(
        'Логин',
        validators=[DataRequired(message='Поле не заполнено'),
                    Length(min=3, message='Логин слишком короткий')]
    )

    password = PasswordField(
        'Пароль',
        validators=[DataRequired(message='Поле не заполнено'),
                    Length(min=6, message='Пароль слишком короткий')]
    )

    repeat_password = PasswordField(
        'Повторите пароль',
        validators=[DataRequired(message='Поле не заполнено'),
                    EqualTo('password', message='Пароли не совпадают')]
    )
    submit = SubmitField('Зарегестрироваться')


# Authorization form
class LoginForm(FlaskForm):
    login = StringField(
        'Логин', validators=[DataRequired(message='Поле не заполнено')]
    )

    password = PasswordField(
        'Пароль', validators=[DataRequired(message='Поле не заполнено')]
    )

    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


# Account editing form
class EditAccountForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    description = TextAreaField('Описание')
    submit = SubmitField('Сохранить')


# Account password change form
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(
        'Старый пароль', validators=[DataRequired(message='Поле не заполнено')]
    )

    new_password = PasswordField(
        'Новый пароль',
        validators=[DataRequired(message='Поле не заполнено'),
                    Length(min=6, message='Пароль слишком короткий')]
    )

    repeat_password = PasswordField(
        'Повторите новый пароль',
        validators=[DataRequired(message='Поле не заполнено'),
                    EqualTo('new_password', message='Пароли не совпадают')]
    )

    submit = SubmitField('Сохранить')


# Adding post form
class AddPostForm(FlaskForm):
    title = StringField('Заголовок')

    text = TextAreaField(
        'Текст', validators=[DataRequired(message='Поле не заполнено')]
    )

    submit = SubmitField('Опубликовать')


# Post editing form
class EditPostForm(FlaskForm):
    title = StringField('Заголовок')

    text = TextAreaField(
        'Текст', validators=[DataRequired(message='Поле не заполнено')]
    )

    submit = SubmitField('Сохранить')


# Avatar change form
class ChangeAvatarForm(FlaskForm):
    file = FileField('Фото(в формате jpg)')
    submit = SubmitField('Сохранить')


# User search form
class SearchForm(FlaskForm):
    text = StringField(
        'Поле ввода', validators=[DataRequired(message='Поле не заполнено')]
    )

    search_type = SelectField(
        'Тип поиска', choices=[('1', 'По ID'), ('2', 'По логину')], default=1
    )

    submit = SubmitField('Поиск')
