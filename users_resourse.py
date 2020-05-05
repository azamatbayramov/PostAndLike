from flask_restful import abort, Resource
from data import db_session
from data.__all_models import users
from flask import jsonify

User = users.User


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).all()
    if not user:
        abort(404, message=f"User {user_id} not found")


class UsersResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).filter(User.id == user_id).first()
        return jsonify({'user': user.to_dict(only=('id', 'login', 'registration_date', 'description',
                                                   'private_account', 'avatar_photo_id'))})


class UsersListResource(Resource):
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify({'users': [user.to_dict(only=('id', 'login', 'registration_date',
                                                     'description', 'private_account',
                                                     'avatar_photo_id')) for user in users]})
