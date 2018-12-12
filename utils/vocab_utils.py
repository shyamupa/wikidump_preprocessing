"""Build vocab for labels, words."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import logging
import utils.constants as K


def get_word(idx, i2w):
    if idx in i2w:
        return i2w[idx]
    else:
        return K.OOV_TOKEN


def get_typeidx(type, t2i):
    if type in t2i:
        return t2i[type]
    else:
        return K.OOV_ID


def get_idx(word, w2i):
    word = word.lower()
    if word in w2i:
        return w2i[word]
    else:
        return K.OOV_ID

# start_word, end_word = "<s>", "<eos>"
# unk_word, unk_wid = 'unk', "<unk_wid>"  # unk word, unk entity
#
# def MentionGenerator(loader):
#     while True:
#         if loader.epochs == 1:
#             break
#         mention = loader.next()
#         print(mention)
#         seen +=1
#
# def get_label_vocab(all_labels, all_wids, label2idx=None, knwn_wid2idx=None):
#     """Creates vocab of BIO labels and intents seen in all data.
#
#   Args:
#     all_labels: all types seen in data.
#     all_intents: all intents seen in data.
#     label2idx: dictionary to create/add to of bio labels to ids.
#     intent2idx: dictionary to create/add to of intents to ids.
#
#   Returns:
#     label2idx, intent2idx dictionary.
#   """
#     logging.info("creating label vocab ...")
#     if label2idx is None:
#         label2idx = {}
#     if knwn_wid2idx is None:
#         knwn_wid2idx = {unk_wid: 0}
#
#     for mtypes in all_labels:
#         for mtype in mtypes:
#             if mtype not in label2idx:
#                 label2idx[mtype] = len(label2idx)
#
#     for wid in all_wids:
#         if wid not in knwn_wid2idx:
#             knwn_wid2idx[wid] = len(knwn_wid2idx)
#
#     return label2idx, knwn_wid2idx
#
#
# def get_word_vocab(all_sentences, word2idx=None):
#     """Creates vocab of words seen in all data.
#
#   Args:
#     all_sentences: all the sentences (including test)
#     word2idx: dictionary to create/add to the chars and their ids.
#
#   Returns:
#     char2idx dictionary.
#   """
#     if word2idx is None:
#         word2idx = {unk_word: 0, start_word: 1, end_word: 2}
#     else:
#         pass
#     for sentence in all_sentences:
#         for token in sentence:
#             if token not in word2idx:
#                 word2idx[token] = len(word2idx)
#     return word2idx
#
#
# def get_char_vocab(all_sentences, char2idx=None):
#     """Creates vocab of characters seen in all data.
#
#   Args:
#     all_sentences: all the sentences (including test)
#     char2idx: dictionary to create/add to the chars and their ids.
#
#   Returns:
#     char2idx , idx2char dictionary and max word length.
#   """
#     if char2idx is None:
#         char2idx = {unk_word: 0}  # assume we never have a a OOV char
#     chars = [char for sent in all_sentences for word in sent for char in word]
#     maxwordlen = max([len(word) for sent in all_sentences for word in sent])
#     for char in chars:
#         if char not in char2idx:
#             char2idx[char] = len(char2idx)
#     idx2char = dict([(v, k) for (k, v) in char2idx.iteritems()])
#     logging.info("Found %i unique characters", len(char2idx))
#     logging.info("max word len %d", maxwordlen)
#     return char2idx, idx2char, maxwordlen
