_model = None

def get_model():
    global _model
    if _model is None:
        from detoxify import Detoxify
        _model = Detoxify("original")
    return _model

def check_toxicity(text):
    try:
        result = get_model().predict(text)

        is_toxic = result["toxicity"] > 0.6

        return {
            "language_and_tone": not is_toxic,
            "content_appropriateness": not is_toxic,
            "kindness": not is_toxic
        }

    except Exception as e:
        return {
            "language_and_tone": False,
            "content_appropriateness": False,
            "kindness": False
        }