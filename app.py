from flask import Flask, jsonify, g
from flask_cors import CORS
import os
import psycopg2
import psycopg2.extras
from auth_middleware import token_required
from auth_blueprint import authentication_blueprint
from challenges_blueprint import challenges_blueprint
from submissions_blueprint import submissions_blueprint
from test_cases_blueprint import test_cases_blueprint
from progress_blueprint import progress_blueprint
from db_helpers import get_db_connection

app = Flask(__name__)

cors_origin = os.environ.get('CORS_ORIGIN', '*')
supports_credentials = cors_origin != '*'
CORS(app, resources={
     r"/*": {"origins": cors_origin}}, supports_credentials=supports_credentials)

app.register_blueprint(authentication_blueprint)
app.register_blueprint(challenges_blueprint)
app.register_blueprint(submissions_blueprint)
app.register_blueprint(test_cases_blueprint)
app.register_blueprint(progress_blueprint)

@app.route('/users')
@token_required
def users_index():
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, username FROM users;")
    users = cursor.fetchall()
    connection.close()
    return jsonify(users), 200


@app.route('/users/<user_id>')
@token_required
def users_show(user_id):
    if int(user_id) != g.user["id"]:
        return jsonify({"err": "Unauthorized"}), 403
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, username FROM users WHERE id = %s;", (user_id,))
    user = cursor.fetchone()
    connection.close()
    if user is None:
        return jsonify({"err": "User not found"}), 404
    return jsonify(user), 200


if __name__ == '__main__':
    app.run(debug=True, port=3000)
