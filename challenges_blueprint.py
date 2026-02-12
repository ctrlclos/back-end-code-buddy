from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
import psycopg2
import psycopg2.extras
from auth_middleware import token_required
from datetime import datetime


challenges_blueprint = Blueprint('challenges_blueprint', __name__)


@challenges_blueprint.route('/challenges', methods=['POST'])
@token_required
def create_challenge():
    try:
        author_id = g.user["id"]

        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        difficulty = data.get("difficulty")
        data_structure_type = data.get("data_structure_type")

        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
                        INSERT INTO coding_challenges (author, title, description, difficulty, data_structure_type, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                       (author_id, title, description, difficulty, data_structure_type, datetime.utcnow(), datetime.utcnow())
                       )
        challenge_id = cursor.fetchone()["id"]
        cursor.execute("""SELECT c.id,
                            c.author AS author_id,
                            c.title,
                            c.description,
                            c.difficulty,
                            c.data_structure_type,
                            c.created_at,
                            c.updated_at,
                            u.username AS author_username
                        FROM coding_challenges c
                        JOIN users u ON c.author = u.id
                        WHERE c.id = %s
                       """, (challenge_id,))
        created_challenge = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify(created_challenge), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500

ALLOWED_SORT_FIELDS = {"difficulty", "created_at"}
DIFFICULT_ORDER = {"easy": 1, "medium": 2, "hard": "3"}

@challenges_blueprint.route('/challenges', methods=['GET'])
def challenges_index():
    try:
        difficulty_filter = request.args.get("difficulty")
        data_structure_filter = request.args.get("data_structure_type")
        sort_by = request.args.get("sort_by", "created_at")

        if sort_by not in ALLOWED_SORT_FIELDS:
            sort_by = "created_at"

        base_query = """SELECT c.id,
                        c.author AS author_id,
                        c.title,
                        c.description,
                        c.difficulty,
                        c.data_structure_type,
                        c.created_at,
                        c.updated_at,
                        u.username AS author_username
                    FROM coding_challenges c
                    INNER JOIN users u ON c.author = u.id
                """
        params = []
        conditions = []

        if difficulty_filter:
            conditions.append("c.difficulty = %s")
            params.append(difficulty_filter)

        if data_structure_filter:
            conditions.append("c.data_structure_type = %s")
            params.append(data_structure_filter)

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        if sort_by == "difficulty":
            base_query = base_query + " ORDER BY CASE c.difficulty WHEN 'easy' THEN 1 WHEN 'medium' THEN 2 WHEN 'hard' THEN 3 END"
        else:
            base_query = base_query + " ORDER BY c.created_at DESC"

        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(base_query, tuple(params))
        challenges = cursor.fetchall()

        connection.commit()
        connection.close()
        return jsonify(challenges), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@challenges_blueprint.route('/challenges/<challenge_id>', methods=['GET'])
def show_challenge(challenge_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT c.id,
                c.author AS author_id,
                c.title,
                c.description,
                c.difficulty,
                c.data_structure_type,
                c.created_at,
                c.updated_at,
                u.username AS author_username
            FROM coding_challenges c
            INNER JOIN users u ON c.author = u.id
            WHERE c.id = %s""",
                       (challenge_id,))
        challenge = cursor.fetchone()
        connection.close()
        if challenge is not None:
            return jsonify(challenge), 200
        else:
            return jsonify({"error": "Challenge not found"}), 404
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@challenges_blueprint.route('/challenges/<challenge_id>', methods=['PUT'])
@token_required
def update_challenge(challenge_id):
    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        difficulty = data.get("difficulty")
        data_structure_type = data.get("data_structure_type")

        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM coding_challenges WHERE id = %s", (challenge_id,))
        challenge_to_update = cursor.fetchone()
        if challenge_to_update is None:
            return jsonify({"error": "Challenge not found"}), 404
        connection.commit()
        if challenge_to_update["author"] != g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401

        cursor.execute("""UPDATE coding_challenges
                        SET title = %s, description = %s, difficulty = %s, data_structure_type = %s, updated_at = %s
                        WHERE id = %s RETURNING id""",
                       (title, description, difficulty, data_structure_type, datetime.utcnow(), challenge_id))
        updated_challenge_id = cursor.fetchone()["id"]
        cursor.execute("""SELECT c.id,
                            c.author AS author_id,
                            c.title,
                            c.description,
                            c.difficulty,
                            c.data_structure_type,
                            c.created_at,
                            c.updated_at,
                            u.username AS author_username
                        FROM coding_challenges c
                        JOIN users u ON c.author = u.id
                        WHERE c.id = %s
                       """, (updated_challenge_id,))
        updated_challenge = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify(updated_challenge), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@challenges_blueprint.route('/challenges/<challenge_id>', methods=['DELETE'])
@token_required
def delete_challenge(challenge_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM coding_challenges WHERE id = %s", (challenge_id,))
        challenge_to_delete = cursor.fetchone()
        if challenge_to_delete is None:
            return jsonify({"error": "Challenge not found"}), 404
        connection.commit()
        if challenge_to_delete["author"] != g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("DELETE FROM coding_challenges WHERE id = %s", (challenge_id,))
        connection.commit()
        connection.close()
        return jsonify(challenge_to_delete), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500
