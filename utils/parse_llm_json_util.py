import json

def parse_llm_json(content):
    if isinstance(content, (dict, list)):
        return content
    if content is None:
        raise ValueError("empty content")
    text = str(content).strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1].strip()
    if text.lower().startswith("json"):
        lines = text.splitlines()
        if lines and lines[0].strip().lower() == "json":
            text = "\n".join(lines[1:]).strip()
    try:
        return json.loads(text)
    except Exception:
        start_brace = text.find("{")
        start_bracket = text.find("[")
        candidates = [i for i in [start_brace, start_bracket] if i != -1]
        if not candidates:
            raise
        start = min(candidates)
        end = text.rfind("}") if text[start] == "{" else text.rfind("]")
        if end == -1 or end <= start:
            raise
        snippet = text[start:end + 1].strip()
        return json.loads(snippet)