import json

SUPPORTED_HARNESS_LANGUAGES = {"python", "javascript"}


# -- Starter code generators --------------------------------------------------

def _python_starter(function_name, function_params, return_type):
    params = ", ".join(p["name"] for p in function_params)
    return f"def {function_name}({params}):\n    pass\n"


def _js_starter(function_name, function_params, return_type):
    params = ", ".join(p["name"] for p in function_params)
    return f"function {function_name}({params}) {{\n    \n}}\n"


# -- Harness wrappers ---------------------------------------------------------

def _python_wrap(user_code, function_name):
    return (
        "import json, sys\n\n"
        f"{user_code}\n\n"
        "_args = json.loads(sys.stdin.read())\n"
        f"_result = {function_name}(*_args)\n"
        "print(json.dumps(_result, separators=(',', ':')))\n"
    )


def _js_wrap(user_code, function_name):
    return (
        f"{user_code}\n\n"
        "const _input = require('fs').readFileSync('/dev/stdin', 'utf8');\n"
        "const _args = JSON.parse(_input);\n"
        f"const _result = {function_name}(..._args);\n"
        "console.log(JSON.stringify(_result));\n"
    )


# -- Public API ----------------------------------------------------------------

def generate_starter_code(function_name, function_params, return_type, language):
    # Generate language-specific starter code from function metadata.
    if language == "python":
        return _python_starter(function_name, function_params, return_type)
    elif language == "javascript":
        return _js_starter(function_name, function_params, return_type)
    return None


def generate_all_starter_code(function_name, function_params, return_type):
    # Generate starter code for all supported harness languages. Returns dict.
    result = {}
    for lang in SUPPORTED_HARNESS_LANGUAGES:
        code = generate_starter_code(function_name, function_params, return_type, lang)
        if code:
            result[lang] = code
    return result


def wrap_code(user_code, function_name, language):
    # Wrap user's function code with a JSON I/O harness for execution.
    if language == "python":
        return _python_wrap(user_code, function_name)
    elif language == "javascript":
        return _js_wrap(user_code, function_name)
    raise ValueError(f"Harness wrapping not supported for {language}")
