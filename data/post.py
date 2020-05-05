from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
import sqlalchemy
from sqlalchemy import orm


liked_users_table = sqlalchemy.Table(
    'liked_users_table',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('users', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('posts', sqlalchemy.Integer, sqlalchemy.ForeignKey('posts.id'))
)


# Класс модели поста
class Post(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    author_id = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey("users.id"))
    author = orm.relation('User')
    title = sqlalchemy.Column(sqlalchemy.String)
    text = sqlalchemy.Column(sqlalchemy.String)
    creating_date = sqlalchemy.Column(sqlalchemy.DateTime)
    editing_date = sqlalchemy.Column(sqlalchemy.DateTime)

    creating_date_norm_view = sqlalchemy.Column(sqlalchemy.String)
    editing_date_norm_view = sqlalchemy.Column(sqlalchemy.String)

    liked_users = orm.relation('User', secondary='liked_users_table')