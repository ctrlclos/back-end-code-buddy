from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
import psycopg2
import psycopg2.extras
from auth_middleware import token_required
import gemini_service

test_cases_blueprint = Blueprint('test_cases_blueprint', __name__)


@test_cases_blueprint.route('/challenges/<challenge_id>/test-cases', methods=['GET'])
@token_required
def list_test_cases(challenge_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("SELECT id FROM coding_challenges WHERE id = %s", (challenge_id,))
        if cursor.fetchone() is None:
            connection.close()
            return jsonify({"error": "Challenge not found"}), 404

        cursor.execute(
            """SELECT id, challenge_id, input, expected_output, is_hidden, created_at
               FROM test_cases
               WHERE challenge_id = %s
               ORDER BY id""",
            (challenge_id,))
        test_cases = cursor.fetchall()

        connection.close()
        return jsonify(test_cases), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@test_cases_blueprint.route('/challenges/<challenge_id>/test-cases', methods=['POST'])
@token_required
def create_test_case(challenge_id):
    try:
        user_id = g.user["id"]

        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute(
            "SELECT id, author FROM coding_challenges WHERE id = %s",
            (challenge_id,))
        challenge = cursor.fetchone()
        if challenge is None:
            connection.close()
            return jsonify({"error": "Challenge not found"}), 404
        if challenge["author"] != user_id:
            connection.close()
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        tc_input = data.get("input", "")
        expected_output = data.get("expected_output")
        is_hidden = data.get("is_hidden", False)

        if expected_output is None:
            connection.close()
            return jsonify({"error": "expected_output is required"}), 400

        cursor.execute(
            """INSERT INTO test_cases (challenge_id, input, expected_output, is_hidden)
               VALUES (%s, %s, %s, %s)
               RETURNING id, challenge_id, input, expected_output, is_hidden, created_at""",
            (challenge_id, tc_input, expected_output, is_hidden))
        created_test_case = cursor.fetchone()

        connection.commit()
        connection.close()
        return jsonify(created_test_case), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@test_cases_blueprint.route('/test-cases/<test_case_id>', methods=['PUT'])
@token_required
def update_test_case(test_case_id):
    try:
        user_id = g.user["id"]

        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute(
            """SELECT tc.id, c.author
               FROM test_cases tc
               JOIN coding_challenges c ON tc.challenge_id = c.id
               WHERE tc.id = %s""",
            (test_case_id,))
        result = cursor.fetchone()
        if result is None:
            connection.close()
            return jsonify({"error": "Test case not found"}), 404
        if result["author"] != user_id:
            connection.close()
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        tc_input = data.get("input", "")
        expected_output = data.get("expected_output")
        is_hidden = data.get("is_hidden", False)

        if expected_output is None:
            connection.close()
            return jsonify({"error": "expected_output is required"}), 400

        cursor.execute(
            """UPDATE test_cases
               SET input = %s, expected_output = %s, is_hidden = %s
               WHERE id = %s
               RETURNING id, challenge_id, input, expected_output, is_hidden, created_at""",
            (tc_input, expected_output, is_hidden, test_case_id))
        updated_test_case = cursor.fetchone()

        connection.commit()
        connection.close()
        return jsonify(updated_test_case), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@test_cases_blueprint.route('/test-cases/<test_case_id>', methods=['DELETE'])
@token_required
def delete_test_case(test_case_id):
    try:
        user_id = g.user["id"]

        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute(
            """SELECT tc.id, tc.challenge_id, tc.input, tc.expected_output,
                      tc.is_hidden, tc.created_at, c.author
               FROM test_cases tc
               JOIN coding_challenges c ON tc.challenge_id = c.id
               WHERE tc.id = %s""",
            (test_case_id,))
        result = cursor.fetchone()
        if result is None:
            connection.close()
            return jsonify({"error": "Test case not found"}), 404
        if result["author"] != user_id:
            connection.close()
            return jsonify({"error": "Unauthorized"}), 401

        cursor.execute("DELETE FROM test_cases WHERE id = %s", (test_case_id,))

        connection.commit()
        connection.close()

        del result["author"]
        return jsonify(result), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@test_cases_blueprint.route('/challenges/<challenge_id>/generate-test-cases', methods=['POST'])
@token_required
def generate_test_cases(challenge_id):
    try:
        user_id = g.user["id"]
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        cursor.execute(
            """
            SELECT id, author, title, description, difficulty,
            data_structure_type, function_name,
            function_params, return_type
            FROM coding_challenges WHERE id = %s
            """,
            (challenge_id,)
        )
        challenge = cursor.fetchone()
        connection.close()

        if challenge is None:
            return jsonify({"error": "Challenge not found"}), 404
        if challenge["author"] != user_id:
            return jsonify({"error": "Unauthorized"}), 401

        generated = gemini_service.generate_test_cases(challenge)

        return jsonify(generated), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    
