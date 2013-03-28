import datetime
import sqlalchemy
import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    screen_name = sqlalchemy.Column(sqlalchemy.String(50))
    date_added = sqlalchemy.Column(sqlalchemy.DateTime())
    key = sqlalchemy.Column(sqlalchemy.String(50))
    secret = sqlalchemy.Column(sqlalchemy.String(50))

class Song(Base):
    __tablename__ = "song"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    active = sqlalchemy.Column(sqlalchemy.Boolean)
    path = sqlalchemy.Column(sqlalchemy.String(255))
    image = sqlalchemy.Column(sqlalchemy.String(255))
    title = sqlalchemy.Column(sqlalchemy.String(255))
    artist = sqlalchemy.Column(sqlalchemy.String(255))
    description = sqlalchemy.Column(sqlalchemy.Text)
    date_added = sqlalchemy.Column(sqlalchemy.DateTime())
    # Who uploaded it
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))

    user = relationship(User)

class PlayCode(Base):
    __tablename__ = "playcode"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    song_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('song.id'), nullable=False)
    code = sqlalchemy.Column(sqlalchemy.String(255))
    played = sqlalchemy.Column(sqlalchemy.Boolean)

    song = relationship(Song)

    def __init__(self, song_id):
        self.song_id = song_id
        self.played = False
        self.code = str(uuid.uuid4())

class Share(Base):
    __tablename__ = "share"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    song_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('song.id'), nullable=False)
    user_from_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'), nullable=False)
    user_to_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'), nullable=False)
    date_shared = sqlalchemy.Column(sqlalchemy.DateTime())
    # The number of times they can play it
    numplays = sqlalchemy.Column(sqlalchemy.Integer)
    # the number of times they can share it
    numshares = sqlalchemy.Column(sqlalchemy.Integer)

    song = relationship(Song)
    user_from = relationship(User, foreign_keys=[user_from_id])
    user_to = relationship(User, foreign_keys=[user_to_id])

class Want(Base):
    __tablename__ = "want"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    song_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('song.id'), nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'), nullable=False)
    wanted_from_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'), nullable=False)
    date_wanted = sqlalchemy.Column(sqlalchemy.DateTime())

    user = relationship(User, foreign_keys=[user_id])
    song = relationship(Song)
    wanted_from = relationship(User, foreign_keys=[wanted_from_id])

class Play(Base):
    __tablename__ = "play"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'), nullable=False)
    song_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('song.id'), nullable=False)
    ip = sqlalchemy.Column(sqlalchemy.String(255))
    date_played = sqlalchemy.Column(sqlalchemy.DateTime())

    user = relationship(User)
    song = relationship(Song)

class Click(Base):
    # Someone clicked a link from twitter and we store it
    __tablename__ = "click"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    # Who clicked (if logged in)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    # Who tweeted
    tweet_user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    # Who they tweeted at (if they were asking)
    tweet_target_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    ip = sqlalchemy.Column(sqlalchemy.String(255))
    date_clicked = sqlalchemy.Column(sqlalchemy.DateTime())

    user = relationship(User, foreign_keys=[user_id])
    tweet_user = relationship(User, foreign_keys=[tweet_user_id])
    tweet_target = relationship(User, foreign_keys=[tweet_target_id])
