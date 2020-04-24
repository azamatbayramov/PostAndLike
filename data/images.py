import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Image(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    adding_date = sqlalchemy.Column(sqlalchemy.DateTime)
    file_name = sqlalchemy.Column(sqlalchemy.String)
