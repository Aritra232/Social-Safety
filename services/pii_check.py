import re

def check_pii(text):
    if re.search(r'\d{11}', text):
        return {"safe": False}

    if re.search(r'\S+@\S+', text):
        return {"safe": False}

    return {"safe": True}