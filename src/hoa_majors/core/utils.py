def normalize_course_code(code: str) -> str:
    """
    Normalize course code: trim whitespace, convert to uppercase, and remove trailing 'E' for consistency.
    """
    code = code.strip().upper()
    if code.endswith("E"):
        return code[:-1]
    return code
