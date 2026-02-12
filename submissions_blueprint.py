from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
import psycopg2
import psycopg2.extras
from auth_middleware import token_required
from datetime import datetime


submissions_blueprint = Blueprint('submissions_blueprint', __name__)


@submissions_blueprint.route('/challenges/<challenge_id>/submit', methods=['POST'])
@token_required
def create_submission(challenge_id):
    try:
        user_id = g.user["id"]
        data = request.get_json()
        code = data.get("code")
        language = data.get("language")
        notes = data.get("notes")

        if not code or not language:
            return jsonify({"error": "Code and language are required"}), 400

        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)

        # Verify the challenge exists
        cursor.execute("SELECT id FROM coding_challenges WHERE id = %s", (challenge_id,))
        challenge = cursor.fetchone()
        if challenge is None:
            connection.close()
            return jsonify({"error": "Challenge not found"}), 404

        cursor.execute("""
            INSERT INTO submissions (user_id, challenge_id, code, language, status, notes, submitted_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, challenge_id, code, language, "submitted", notes, datetime.utcnow())
        )
        submission_id = cursor.fetchone()["id"]

        cursor.execute("""
            SELECT s.id,
                s.user_id,
                s.challenge_id,
                s.code,
                s.language,
                s.status,
                s.notes,
                s.submitted_at,
                u.username
            FROM submissions s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = %s
            """, (submission_id,))
        created_submission = cursor.fetchone()

        connection.commit()
        connection.close()
        return jsonify(created_submission), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@submissions_blueprint.route('/challenges/<challenge_id>/submissions', methods=['GET'])
@token_required
def list_submissions(challenge_id):
    try:
        user_id = g.user["id"]

        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)

        # Verify the challenge exists
        cursor.execute("SELECT id FROM coding_challenges WHERE id = %s", (challenge_id,))
        challenge = cursor.fetchone()
        if challenge is None:
            connection.close()
            return jsonify({"error": "Challenge not found"}), 404

        cursor.execute("""
            SELECT s.id,
                s.user_id,
                s.challenge_id,
                s.code,
                s.language,
                s.status,
                s.notes,
                s.submitted_at,
                u.username
            FROM submissions s
            JOIN users u ON s.user_id = u.id
            WHERE s.challenge_id = %s AND s.user_id = %s
            ORDER BY s.submitted_at DESC
            """, (challenge_id, user_id))
        submissions = cursor.fetchall()

        connection.close()
        return jsonify(submissions), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500
