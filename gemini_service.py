import os
import json
from google import genai

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key in ("your-api-key-here", "your_gemini_api_key"):
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Add a valid key to your .env file. "
                "Get one at https://aistudio.google.com/apikey"
            )
        _client = genai.Client(api_key=api_key)
    return _client

MODEL = "gemini-3-flash-preview"

SYSTEM_INSTRUCTION = (
    "You are a senior software engineer and expert test case designer. "
    "Your job is to generate high-quality test cases for coding challenges.\n\n"
    "Rules you MUST follow:\n"
    "- Every test case must have a CORRECT expected_output. Double-check your work.\n"
    "- Include a mix of: basic cases, standard cases, edge cases, and stress cases.\n"
    "- For function-based challenges, the 'input' field must be a JSON array of arguments "
    "matching the function parameters in the exact order they are defined.\n"
    "- For function-based challenges, the 'expected_output' field must be the JSON-encoded "
    "return value of the function.\n"
    "- For stdin/stdout challenges, 'input' is raw text piped to stdin and "
    "'expected_output' is the exact text expected on stdout (whitespace-trimmed).\n"
    "- Make the first 2 test cases visible (is_hidden: false) and the rest hidden (is_hidden: true).\n"
    "- Do NOT include explanations — only return the structured JSON."
)

RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "input": {
                "type": "string",
                "description": (
                    "The test case input. For function-based challenges, a JSON array "
                    "of arguments. For stdin/stdout challenges, raw text."
                ),
            },
            "expected_output": {
                "type": "string",
                "description": (
                    "The expected output. For function-based challenges, the JSON "
                    "return value. For stdin/stdout challenges, raw text."
                ),
            },
            "is_hidden": {
                "type": "boolean",
                "description": (
                    "Whether this test case is hidden from practicioners "
                    "(they only see pass/fail)."
                ),
            },
        },
        "required": ["input", "expected_output", "is_hidden"],
    },
}

def _build_prompt(challenge, count):
    is_function_based = bool(challenge.get("function_name"))

    prompt = f"Generate {count} test cases for the following coding challenge:\n\n"
    prompt += f"Title: {challenge['title']}\n"
    prompt += f"Description: {challenge['description']}\n"
    prompt += f"Difficulty: {challenge['difficulty']}\n"

    if challenge.get("data_structure_type"):
        prompt += f"Data Structure: {challenge['data_structure_type']}\n"

    if is_function_based:
        params = challenge.get("function_params") or []
        params_str = ", ".join(f"{p['name']}: {p['type']}" for p in params)
        return_type = challenge.get("return_type", "string")

        prompt += f"\nFunction Signature: {challenge['function_name']}({params_str}) -> {return_type}\n"
        prompt += "\nFormat requirements:\n"
        prompt += '- "input" must be a JSON array of arguments matching the function parameters in order.\n'
        prompt += "  Example for twoSum(nums: int[], target: int): [[2,7,11,15], 9]\n"
        prompt += '- "expected_output" must be the JSON return value of the function.\n'
        prompt += "  Example: [0,1]\n"
    else:
        prompt += "\nThis is a stdin/stdout challenge (no function signature).\n"
        prompt += "Format requirements:\n"
        prompt += '- "input" is raw text piped to stdin.\n'
        prompt += '- "expected_output" is the exact text expected on stdout.\n'

    prompt += f"\nGenerate exactly {count} test cases with this distribution:\n"
    prompt += "1. A simple/basic case (is_hidden: false)\n"
    prompt += "2. A standard case (is_hidden: false)\n"

    if count >= 3:
        prompt += "3. An edge case — empty input, single element, minimum values, etc. (is_hidden: true)\n"
    if count >= 4:
        prompt += "4. A larger input case to test efficiency (is_hidden: true)\n"
    if count >= 5:
        prompt += "5. A tricky corner case (is_hidden: true)\n"

    return prompt

def generate_test_cases(challenge, count = 5):
    prompt = _build_prompt(challenge, count)
    response = _get_client().models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "response_mime_type": "application/json",
            "response_json_schema": RESPONSE_SCHEMA,
            "temperature": 0.3,
        },
    )
    test_cases = json.loads(response.text)
    return test_cases
