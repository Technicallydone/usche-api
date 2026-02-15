def capitalize_string(s: str | None) -> str | None:
    if not s:
        return None
    return s.strip().capitalize()