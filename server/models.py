from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column('password_hash', db.String, nullable=False)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)

    recipes = db.relationship('Recipe', backref='user', lazy=True)

    @property
    def password_hash(self):
        raise AttributeError('Password hashes are not viewable')

    @password_hash.setter
    def password_hash(self, password_plain):
        if not password_plain or len(password_plain) < 6:
            raise ValueError('Password must be at least 6 characters')
        self._password_hash = generate_password_hash(password_plain)

    def authenticate(self, password_plain):
        if not password_plain:
            return False
        return check_password_hash(self._password_hash, password_plain)

    @validates('username')
    def validate_username(self, key, value):
        if not value or value.strip() == '':
            raise ValueError('Username must be present')
        return value

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'image_url': self.image_url,
            'bio': self.bio
        }

class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('title')
    def validate_title(self, key, value):
        if not value or value.strip() == '':
            raise ValueError('Title must be present')
        return value

    @validates('instructions')
    def validate_instructions(self, key, value):
        if not value or len(value) < 50:
            raise ValueError('Instructions must be at least 50 characters')
        return value

    @validates('minutes_to_complete')
    def validate_minutes(self, key, value):
        try:
            ivalue = int(value)
        except Exception:
            raise ValueError('Minutes to complete must be an integer')
        if ivalue < 0:
            raise ValueError('Minutes to complete must be non negative')
        return ivalue

    def to_dict(self, include_user=False):
        data = {
            'id': self.id,
            'title': self.title,
            'instructions': self.instructions,
            'minutes_to_complete': self.minutes_to_complete,
        }
        if include_user:
            data['user'] = self.user.to_dict()
        return data