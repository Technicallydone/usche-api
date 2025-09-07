import re
import unicodedata


def strip_unicode(text: str):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


