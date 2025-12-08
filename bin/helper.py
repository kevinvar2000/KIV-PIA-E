import pycountry

MAX_FILE_SIZE_MB = 10

def get_supported_languages():
    """
    Return a list of supported languages with ISO 639-1 codes.

    This function iterates over languages provided by the `pycountry` library,
    filters those that have an `alpha_2` (ISO 639-1) code, and returns a list
    of tuples in the form `(alpha_2_code, language_name)`. The resulting list
    is sorted alphabetically by the language name.

    Returns:
        list[tuple[str, str]]: A list of `(alpha_2_code, language_name)` tuples,
        sorted by the language name.
    """
    languages = sorted([(lang.alpha_2, lang.name) for lang in pycountry.languages if hasattr(lang, 'alpha_2')], key=lambda x: x[1])
    return languages