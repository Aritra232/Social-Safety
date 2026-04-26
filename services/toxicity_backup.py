from detoxify import Detoxify

_model = None

def get_model():
    global _model
    if _model is None:
        _model = Detoxify("original")
    return _model

def check_toxicity(text):
    try:
        result = get_model().predict(text)

        if result["toxicity"] > 0.6:
            return {"safe": False, "reason": "Toxic content detected (backup check)"}

        return {"safe": True}

    except Exception as e:
        return {"safe": False, "reason": f"Toxicity backup check failed: {str(e)}"}