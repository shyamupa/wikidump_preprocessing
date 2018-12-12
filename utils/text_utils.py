# coding=utf-8
import logging

__author__ = 'Shyam'

# from polyglot.text import Text
import re
import string
import difflib
# import Levenshtein
import unicodedata


def edit_distance(title, surface):
    # TODO See CTsai code
    title = title.replace("_", " ")
    i = title.find("(")
    if i > 0: title = title[:i]
    stoks = surface.split(" ")
    ttoks = title.split(" ")
    if len(ttoks) == 3 and len(stoks) == 2 and ttoks[1].endswith("."):
        title = ttoks[0] + " " + ttoks[2]
    # TODO try other things
    # https://stackoverflow.com/questions/6690739/fuzzy-string-comparison-in-python-confused-with-which-library-to-use
    # Levenshtein.ratio('hello world', 'hello')
    dist = difflib.SequenceMatcher(None, title, surface).ratio()
    return dist


def _getLnrm(word):
    """Normalizes the given arg by stripping it of diacritics, lowercasing, and
    removing all non-alphanumeric characters.
    """

    org_word, org_len = word, len(word)
    word = ''.join(
        [c for c in unicodedata.normalize('NFD', word) if unicodedata.category(c) != 'Mn'])
    word = word.lower()
    word = ''.join(
        [c for c in word if c in set('abcdefghijklmnopqrstuvwxyz0123456789')])
    new_len = len(word)
    # if org_len != new_len:
    #     logging.info("something looks wrong org:%s new:%s",org_word, word)
    return word


def load_stopwords(f):
    words = [l.strip() for l in open(f)]
    return set(words)


def ispunc(token):
    return token in string.punctuation


def zero_digits(s):
    """
    Replace every digit in a string by a zero.
    """
    return re.sub('\d', '0', s)


def tokenizer(raw_text, lang):
    # print(raw_text)
    # text = Text(raw_text, hint_language_code=lang)
    # return text.words
    return raw_text.split(" ")

if __name__ == '__main__':
    inp = ["Suárez", "Báñez", "Fátima"]
    for i in inp:
        nrm = _getLnrm(i)
        print(i, len(i), nrm, len(nrm))
