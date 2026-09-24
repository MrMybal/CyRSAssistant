"""Shared UTF-8 catalogs for the overlay, service and provider responses."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from importlib.resources import files
import json
import re
from string import Formatter


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate translation key: " + key)
        result[key] = value
    return result


def load_catalogs():
    result = {}
    for path in sorted(files("companion").joinpath("locales").iterdir(), key=lambda p: p.name):
        if path.name.endswith(".json"):
            item = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
            code = item["code"]
            if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*", code) or path.name != code + ".json":
                raise ValueError("Invalid locale filename/code: " + path.name)
            if not isinstance(item.get("name"), str) or not item["name"] or not isinstance(item.get("messages"), dict):
                raise ValueError("Invalid locale metadata: " + path.name)
            result[code] = item
    if "en" not in result:
        raise ValueError("The English catalog is required")
    return {code: result[code] for code in sorted(result, key=lambda code: (code != "en", code))}


CATALOGS = load_catalogs()
_language = ContextVar("cyrs_language", default="en")


def normalize(code):
    code = str(code or "en").lower().replace("_", "-")
    if code in CATALOGS:
        return code
    base = code.split("-", 1)[0]
    return base if base in CATALOGS else "en"


def render(key, values=None, language=None):
    language = normalize(_language.get() if language is None else language)
    translated = CATALOGS[language]["messages"].get(key, CATALOGS["en"]["messages"].get(key, key))
    return translated.format_map(values) if values else translated


class Message(str):
    """Keeps service status text translatable when the overlay language changes."""
    def __new__(cls, key, values):
        obj = super().__new__(cls, render(key, values))
        obj.key, obj.values = key, values
        return obj


def tr(key, **values):
    return Message(key, values)


def render_message(message, language):
    if isinstance(message, Message):
        return render(message.key, message.values, language)
    return render(str(message), language=language)


@contextmanager
def using_language(code):
    token = _language.set(normalize(code))
    try:
        yield
    finally:
        _language.reset(token)


def localized(argument):
    """Pin the request language; thread-pool requests cannot change one another."""
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            state = args[argument] if len(args) > argument else kwargs.get("state", kwargs.get("config", {}))
            with using_language(state.get("language", "en")):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def response_instructions(state):
    code = normalize(state.get("language", "en"))
    return ("\nThe selected interface language is " + CATALOGS[code]["name"] + " (" + code + "). "
            "Use it for your replies, explanations and new human-readable effect labels, unless the user explicitly requests another language. "
            "Keep shader filenames, identifiers, tool names, JSON keys and existing conversation messages unchanged.")


def validate_catalogs(catalogs=None):
    catalogs = CATALOGS if catalogs is None else catalogs
    base = catalogs["en"]["messages"]
    printf = re.compile(r"%(?:[-+#0 ]|\d|\.|\*)*(?:hh|ll|[hljztL])?[diuoxXfFeEgGaAcspn%]")
    def placeholders(text):
        return sorted((field, spec, conversion or "") for _, field, spec, conversion in Formatter().parse(text) if field is not None)
    def printf_tokens(text):
        tokens, position = [], 0
        while True:
            position = text.find("%", position)
            if position < 0:
                return tokens
            token = printf.match(text, position)
            if token is None or token.group().endswith("n"):
                raise ValueError("Invalid printf placeholder in translation")
            tokens.append(token.group())
            position = token.end()
    for code, catalog in catalogs.items():
        for key, value in catalog["messages"].items():
            if not isinstance(key, str) or not isinstance(value, str) or not key or not value or "\0" in key + value or "###" in key + value:
                raise ValueError("Invalid translation in " + code)
            if key not in base or (code == "en" and key != value):
                raise ValueError("Unknown/noncanonical English message: " + key)
            if placeholders(key) != placeholders(value) or printf_tokens(key) != printf_tokens(value):
                raise ValueError("Translation placeholders differ: " + code + ": " + key)
