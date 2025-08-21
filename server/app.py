from flask import Flask, request, session, jsonify
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, User, Recipe
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = 'change-me'  # use a real secret in env

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

# helpers
def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)

def auth_required():
    return current_user() is not None

def error_response(errors, code):
    # errors should be a list of strings
    return jsonify({'errors': errors}), code

# Resources
class Signup(Resource):
    def post(self):
        data = request.get_json() or {}
        try:
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            user.password_hash = data.get('password')
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return user.to_dict(), 201
        except IntegrityError:
            db.session.rollback()
            return error_response(['Username must be unique'], 422)
        except ValueError as ve:
            # from custom validations
            return error_response([str(ve)], 422)

class CheckSession(Resource):
    def get(self):
        user = current_user()
        if not user:
            return error_response(['Not authorized'], 401)
        return user.to_dict(), 200

class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(), 200
        return error_response(['Invalid username or password'], 401)

class Logout(Resource):
    def delete(self):
        if not auth_required():
            return error_response(['Not authorized'], 401)
        session.pop('user_id', None)
        return '', 204

class RecipeIndex(Resource):
    def get(self):
        if not auth_required():
            return error_response(['Not authorized'], 401)
        recipes = Recipe.query.all()
        return [r.to_dict(include_user=True) for r in recipes], 200

    def post(self):
        if not auth_required():
            return error_response(['Not authorized'], 401)
        data = request.get_json() or {}
        try:
            user = current_user()
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user.id
            )
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(include_user=True), 201
        except ValueError as ve:
            db.session.rollback()
            return error_response([str(ve)], 422)

api.add_resource(Signup, '/signup')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(RecipeIndex, '/recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)