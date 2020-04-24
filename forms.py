from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo


class RegisterForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired(message='Поле не заполнено')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Поле не заполнено')])
    repeat_password = PasswordField('Повторите пароль',
                                    validators=[DataRequired(message='Поле не заполнено'),
                                                EqualTo('password',
                                                        message='Пароли не совпадают')])
    submit = SubmitField('Зарегестрироваться')


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
