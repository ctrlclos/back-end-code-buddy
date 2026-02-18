"""
E2B code execution service.
Sends user code to E2B cloud sandboxes for execution and evaluates
results against test cases.
"""

import json
import os
import time
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

load_dotenv()


# Map app language strings to sandbox filenames and run commands
LANGUAGE_CONFIG = {
    "python": {
        "filename": "/tmp/solution.py",
        "run_cmd": "python3 /tmp/solution.py",
    },
    "javascript": {
        "filename": "/tmp/solution.js",
        "run_cmd": "node /tmp/solution.js",
    },
}


def _check_api_key():
    # Check that E2B_API_KEY is set in environment.
    if not os.environ.get("E2B_API_KEY"):
        return "E2B_API_KEY is not set. Add it to your .env file. Get one at https://e2b.dev/dashboard?tab=keys"
    return None


def _run_command(sandbox, cmd, stdin_input="", timeout=30):
    # Run a command in the sandbox, optionally piping stdin.
    # Returns a CommandResult with .stdout, .stderr, .exit_code.
    if stdin_input:
        sandbox.files.write("/tmp/stdin.txt", stdin_input)
        return sandbox.commands.run(f"{cmd} < /tmp/stdin.txt", timeout=timeout)
    return sandbox.commands.run(cmd, timeout=timeout)


def execute_code(source_code, language, stdin=""):
    # send code to an E2B sandbox for execution and return the result.
    # creates a new sandbox, writes the code file, pipes stdin, and
    # returns stdout/stderr/exit_code.
    config = LANGUAGE_CONFIG.get(language)
    if config is None:
        return {"error": f"Unsupported language: {language}"}

    key_error = _check_api_key()
    if key_error:
        return {"error": key_error}

    try:
        sandbox = Sandbox.create()
    except Exception as e:
        return {"error": f"E2B sandbox creation failed: {e}"}

    try:
        sandbox.files.write(config["filename"], source_code)

        start_time = time.time()
        result = _run_command(sandbox, config["run_cmd"], stdin_input=stdin, timeout=30)
        elapsed = round(time.time() - start_time, 3)

        return {
            "stdout": (result.stdout or "").rstrip("\n"),
            "stderr": result.stderr if result.exit_code != 0 else None,
            "status": {
                "id": 3 if result.exit_code == 0 else 11,
                "description": "Accepted" if result.exit_code == 0 else "Runtime Error",
            },
            "time": str(elapsed),
            "memory": None,
        }
    except Exception as e:
        error_msg = str(e)
        if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            return {"error": "Code execution timed out"}
        return {"error": f"Code execution failed: {error_msg}"}
    finally:
        sandbox.kill()


def _compare_outputs(actual, expected):
    if actual == expected:
        return True
    try:
        return json.loads(actual) == json.loads(expected)
    except (json.JSONDecodeError, TypeError):
        return False


def run_test_cases(source_code, language, test_cases):
    # executes code against a list of test cases in a single sandbox
    # returns per-case results.
    config = LANGUAGE_CONFIG.get(language)
    if config is None:
        return {
            "overall_status": "error",
            "passed_count": 0,
            "total_count": len(test_cases),
            "test_results": [{
                "test_case_id": tc["id"],
                "input": tc["input"],
                "expected_output": tc["expected_output"],
                "actual_output": None,
                "passed": False,
                "is_hidden": tc["is_hidden"],
                "status": "Error",
                "time": None,
                "error": f"Unsupported language: {language}",
            } for tc in test_cases],
        }

    key_error = _check_api_key()
    if key_error:
        return {
            "overall_status": "error",
            "passed_count": 0,
            "total_count": len(test_cases),
            "test_results": [{
                "test_case_id": tc["id"],
                "input": tc["input"],
                "expected_output": tc["expected_output"],
                "actual_output": None,
                "passed": False,
                "is_hidden": tc["is_hidden"],
                "status": "Error",
                "time": None,
                "error": key_error,
            } for tc in test_cases],
        }

    try:
        sandbox = Sandbox.create()
    except Exception as e:
        return {
            "overall_status": "error",
            "passed_count": 0,
            "total_count": len(test_cases),
            "test_results": [{
                "test_case_id": tc["id"],
                "input": tc["input"],
                "expected_output": tc["expected_output"],
                "actual_output": None,
                "passed": False,
                "is_hidden": tc["is_hidden"],
                "status": "Error",
                "time": None,
                "error": f"E2B sandbox creation failed: {e}",
            } for tc in test_cases],
        }

    try:
        # Write source code once
        sandbox.files.write(config["filename"], source_code)

        # Run each test case in the same sandbox
        test_results = []
        passed_count = 0
        has_error = False

        for tc in test_cases:
            try:
                start_time = time.time()
                result = _run_command(
                    sandbox, config["run_cmd"],
                    stdin_input=tc["input"], timeout=30,
                )
                elapsed = round(time.time() - start_time, 3)

                actual_output = (result.stdout or "").rstrip("\n")
                expected_output = tc["expected_output"].strip()
                passed = _compare_outputs(actual_output.strip(), expected_output)

                if passed:
                    passed_count += 1

                if result.exit_code != 0:
                    has_error = True

                test_results.append({
                    "test_case_id": tc["id"],
                    "input": tc["input"],
                    "expected_output": tc["expected_output"],
                    "actual_output": actual_output,
                    "passed": passed,
                    "is_hidden": tc["is_hidden"],
                    "status": "Accepted" if result.exit_code == 0 else "Runtime Error",
                    "time": str(elapsed),
                    "error": result.stderr if result.exit_code != 0 else None,
                })
            except Exception as e:
                test_results.append({
                    "test_case_id": tc["id"],
                    "input": tc["input"],
                    "expected_output": tc["expected_output"],
                    "actual_output": None,
                    "passed": False,
                    "is_hidden": tc["is_hidden"],
                    "status": "Error",
                    "time": None,
                    "error": str(e),
                })
                has_error = True

        total_count = len(test_cases)

        if has_error and passed_count == 0:
            overall_status = "error"
        elif passed_count == total_count:
            overall_status = "passed"
        else:
            overall_status = "failed"

        return {
            "overall_status": overall_status,
            "passed_count": passed_count,
            "total_count": total_count,
            "test_results": test_results,
        }
    finally:
        sandbox.kill()
