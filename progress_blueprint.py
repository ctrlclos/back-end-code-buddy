from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
import psycopg2.extras
from auth_middleware import token_required

progress_blueprint = Blueprint('progress_blueprint', __name__)

@progress_blueprint.route('/progress/stats', method=['GET'])
@token_required
def get_stats():
    try:
        user_id = g.user["id"]
        connection = get_db_connection()

        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        cursor.execute("""
                    SELECT
                    COUNT(DISTINCT s.challenge_id) AS attempted,
                    COUNT(DISTINCT CASE
                            WHEN s.status = 'passed'
                            THEN s.challenge_id
                    END) AS solved,
                    COUNT(*) AS total_submissions
                    FROM submissions s
                    WHERE s.user_id = %s
                    """, (user_id,))
        overall = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as total FROM coding_challenges")
        total_challenges = cursor.fetchone()["total"]

        cursor.execute("""
                    SELECT c.difficulty,
                    COUNT(DISTINCT s.challenge_id) AS attempted,
                    COUNT(DISTINCT CASE
                        WHEN s.status = 'passed'
                        THEN s.challenge_id
                    END) AS solved
                    FROM submissions s
                    JOIN coding_challenges ON s.challenge_id = c.id
                    WHERE s.user_id = %s
                    GROUP BY c.difficulty
                    """, (user_id,))
        by_difficulty = cursor.fetchall()

        cursor.execute("""
                    SELECT
                    COUNT(DISTINCT s.challenge_id) AS attempted,
                    COUNT(DISTINCT CASE
                        WHEN s.status = 'passed'
                        THEN s.challenge_id
                    END) AS solved
                    FROM submissions s
                    JOIN coding_challenges c ON s.challenge_id = c.id
                    WHERE s.user_id = %s
                        AND c.data_structure IS NOT NULL
                        GROUP BY c.data_structure_type
                    """, (user_id,))
        by_data_structure = cursor.fetchall()

        connection.close()

        attempted = overall["attempted"]
        solved = overall["solved"]
        solve_rate = round(
            (solved / attempted) * 100, 2
        ) if attempted > 0 else 0

        return jsonify({
            "attempted": attempted,
            "solved": solved,
            "total_submissions": overall["total_submissions"],
            "total_challenges": total_challenges,
            "solve_rate": solve_rate,
            "by_difficulty": by_difficulty,
            "by_data_structure": by_data_structure,
            }), 200

    except Exception as error:
        return jsonify({
        "error": str(error)
        }), 500
@progress_blueprint.route('/progress/activity', methods=['GET'])
@token_required
def get_activity():
    try:
        user_id = g.user["id"]
        try:
            limit = int(request.args.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20
        limit = min(max(limit, 1), 50)

        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        cursor.execute("""
                    SELECT
                        s.id,
                        s.challenge_id,
                        c.title AS challenge_title,
                        c.difficulty,
                        c.data_structure_type,
                        s.language,
                        s.submitted_at,
                    FROM submissions s
                    JOIN coding_challenges c ON s.challenge_id = c.id
                    WHERE s.user_id = %s
                    ORDER BY s.submitted_at DESC
                    LIMIT %s
                       """, (user_id, limit))
        activity = cursor.fetchall()
        connection.close()
        return jsonify(activity), 200
    except Exception as error:
        return jsonify({"error": str(error)}),500
