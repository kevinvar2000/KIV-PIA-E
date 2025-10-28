import pycountry

MAX_FILE_SIZE_MB = 10

def get_supported_languages():
    languages = sorted([(lang.alpha_2, lang.name) for lang in pycountry.languages if hasattr(lang, 'alpha_2')], key=lambda x: x[1])
    return languages