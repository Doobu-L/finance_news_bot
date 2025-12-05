
def escape_markdown(text):
    """
    Escape Markdown characters to prevent parsing errors.
    Characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    escape_chars = r"_*[]()~`>#+-=|{}!"
    # In MarkdownV2 we might need more, but for basic Markdown (V1) or V2:
    # If using 'Markdown' parse_mode (V1), only _ * ` [ need escaping sometimes, 
    # but 'MarkdownV2' is stricter.
    # The snippet uses parse_mode='Markdown' (V1 style usually).
    # Let's try to be safe.
    # Actually, legacy 'Markdown' is loose. 'MarkdownV2' is strict.
    # The error "can't find end of the entity" suggests we are using a mode that expects closure.
    
    # Simple fix for V1 Markdown: escape * and _ and [
    # But wait, we WANT to use * for bold.
    # We should only escape * inside the title if it's part of the text, not our formatting.
    # But that's hard to distinguish.
    # A safer bet is:
    # 1. Sanitize the title content first.
    # 2. Apply our formatting (bold) afterwards.
    
    for char in "*_[`":
        text = text.replace(char, f"\\{char}")
    return text
