import json
import re


JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def parse_json_response(content, fallback):
    text = (content or "").strip()
    block_match = JSON_BLOCK_PATTERN.search(text)
    if block_match:
        text = block_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def json_prompt_schema(schema):
    return json.dumps(schema, indent=2)
