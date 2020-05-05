import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

subscriptions_list_table = sqlalchemy.Table(
    'subscriptions',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('subscription_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
)

requested_subscriptions_list_table = sqlalchemy.Table(
    'requested_subscriptions',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('requested_user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
)

subscribers_list_table = sqlalchemy.Table(
    'subscribers',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('subscriber_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
)

requested_subscribers_list_table = sqlalchemy.Table(
    'requested_subscribers',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('subscriber_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
)


# Класс модели пользователя
class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    login = sqlalchemy.Column(sqlalchemy.String)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    registration_date = sqlalchemy.Column(sqlalchemy.DateTime)
    description = sqlalchemy.Column(sqlalchemy.String, default='')
    posts = orm.relation("Post", back_populates='author')
    liked_posts = orm.relation("Post", back_populates='liked_users')

    subscriptions = orm.relation(
        'User',
        secondary=subscriptions_list_table,
        primaryjoin=(subscriptions_list_table.c.user_id == id),
        secondaryjoin=(subscriptions_list_table.c.subscription_id == id),
        lazy='dynamic'
    )

    requested_subscriptions = orm.relation(
        'User',
        secondary=requested_subscriptions_list_table,
        primaryjoin=(requested_subscriptions_list_table.c.user_id == id),
        secondaryjoin=(requested_subscriptions_list_table.c.requested_user_id == id),
        lazy='dynamic'
    )

    subscribers = orm.relation(
        'User',
        secondary=subscribers_list_table,
        primaryjoin=(subscribers_list_table.c.user_id == id),
        secondaryjoin=(subscribers_list_table.c.subscriber_id == id),
        lazy='dynamic'
    )

    requested_subscribers = orm.relation(
        'User',
        secondary=requested_subscribers_list_table,
        primaryjoin=(requested_subscribers_list_table.c.user_id == id),
        secondaryjoin=(requested_subscribers_list_table.c.subscriber_id == id),
        lazy='dynamic'
    )

    private_account = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    avatar_photo_id = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
