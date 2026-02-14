from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
import psycopg2
import psycopg2.extras
from auth_middleware import token_required
from datetime import datetime
from e2b_service import run_test_cases
from harness import wrap_code, SUPPORTED_HARNESS_LANGUAGES


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

        # Verify the challenge exists and get function metadata
        cursor.execute(
            "SELECT id, function_name FROM coding_challenges WHERE id = %s",
            (challenge_id,))
        challenge = cursor.fetchone()
        if challenge is None:
            connection.close()
            return jsonify({"error": "Challenge not found"}), 404

        # Fetch test cases for this challenge
        cursor.execute(
            """SELECT id, input, expected_output, is_hidden
               FROM test_cases
               WHERE challenge_id = %s
               ORDER BY id""",
            (challenge_id,))
        test_cases = cursor.fetchall()

        # Run code against test cases if they exist
        execution_result = None
        status = "submitted"

        if test_cases:
            # Wrap code with harness for function-based challenges
            code_to_execute = code
            if challenge.get("function_name"):
                if language not in SUPPORTED_HARNESS_LANGUAGES:
                    connection.close()
                    return jsonify({
                        "error": f"Function-based execution is not yet supported for {language}. Please use Python or JavaScript."
                    }), 400
                code_to_execute = wrap_code(code, challenge["function_name"], language)

            execution_result = run_test_cases(code_to_execute, language, test_cases)
            status = execution_result["overall_status"]

        # Save the submission with the determined status (original code, not wrapped)
        cursor.execute("""
            INSERT INTO submissions (user_id, challenge_id, code, language, status, notes, submitted_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, challenge_id, code, language, status, notes, datetime.utcnow())
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

        # Build response
        response = dict(created_submission)

        if execution_result:
            response["passed_count"] = execution_result["passed_count"]
            response["total_count"] = execution_result["total_count"]

            # Sanitize hidden test cases — don't reveal input/expected_output
            sanitized_results = []
            for tr in execution_result["test_results"]:
                if tr["is_hidden"]:
                    sanitized_results.append({
                        "test_case_id": tr["test_case_id"],
                        "passed": tr["passed"],
                        "is_hidden": True,
                        "status": tr["status"],
                        "time": tr["time"],
                    })
                else:
                    sanitized_results.append(tr)

            response["test_results"] = sanitized_results

        return jsonify(response), 201
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
