def remove_quotes(txt):  # strip it and removes quotes in the beginning and in the end of the string
    if txt:
        return txt.strip().strip('"').strip("'")
    return "🤷‍♂️"