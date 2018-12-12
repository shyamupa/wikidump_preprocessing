from collections import namedtuple, defaultdict
import pickle
import sys
import logging
import os
import utils.constants as K
import json
from utils.vocab_utils import get_idx

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)

import time
import numpy as np

__author__ = 'Shyam'


def save(fname, obj):
    with open(fname, 'wb') as f:
        pickle.dump(obj, f)


def save_fast(fname, obj):
    with open(fname, 'wb') as f:
        pickle.dump(obj, f, protocol=4)


def load(fname):
    with open(fname, 'rb') as f:
        return pickle.load(f)


def save_json(fname, obj):
    with open(fname, 'w') as f:
        json.dump(obj, f)


def load_json(fname):
    with open(fname, 'r') as f:
        return json.load(f)


def load_langlinks(lang):
    fr2entitles, en2frtitles = load_map("data/" + lang + "wiki/idmap/fr2entitles")
    return fr2entitles, en2frtitles


def load_crosswikis(crosswikis_pkl):
    stime = time.time()
    print("[#] Loading normalized crosswikis dictionary ... ")
    crosswikis_dict = load(crosswikis_pkl)
    ttime = (time.time() - stime) / 60.0
    print(" [#] Crosswikis dictionary loaded!. Time: {0:2.4f} mins. Size : {1}".format(ttime, len(crosswikis_dict)))
    return crosswikis_dict


def load_map(path):
    pkl_path = path + ".pkl"
    if os.path.exists(pkl_path):
        logging.info("pkl found! loading map %s", pkl_path)
        m, rev_m = load(pkl_path)
    else:
        f = open(path)
        m = {}
        err = 0
        logging.info("pkl not found ...")
        logging.info("loading map from %s", path)
        for idx, l in enumerate(f):
            parts = l.strip().split("\t")
            if len(parts) != 2:
                logging.info("error on line %d %s", idx, parts)
                err += 1
                continue
            k, v = parts
            if k in m:
                logging.info("duplicate key %s was this on purpose?", k)
            m[k] = v
        rev_m = {v: k for k, v in m.items()}
        logging.info("map of size %d loaded %d err lines", len(m), err)
        logging.info("saving pkl... %s", pkl_path)
        obj = m, rev_m
        save(pkl_path, obj)
    return m, rev_m


def load_counts(path, uniqc=True):
    pkl_path = path + ".pkl"
    if os.path.exists(pkl_path):
        logging.info("pkl found! loading counts %s", pkl_path)
        item2count = load(pkl_path)
    else:
        f = open(path)
        item2count = {}
        err = 0
        logging.info("pkl not found ...")
        logging.info("loading counts from %s", path)
        for idx, l in enumerate(f):
            if uniqc:
                parts = l.strip().split(" ")
            else:
                parts = l.strip().split("\t")
            if len(parts) != 2:
                logging.info("error on line %d %s", idx, parts)
                err += 1
                continue
            if uniqc:
                cnt, item = parts
            else:
                item, cnt = parts
            if item in item2count:
                logging.info("duplicate key %s was this on purpose?", item)
            item2count[item] = int(cnt)
        logging.info("map of size %d loaded %d err lines", len(item2count), err)
        logging.info("saving pkl... %s", pkl_path)
        obj = item2count
        save(pkl_path, obj)
    return item2count


def load_ordered_keys(path):
    data = [line.strip().split("\t") for line in open(path)]
    data = [d[0] for d in data]
    return data


def load_vocab(path, wid=False):
    pkl_path = path + ".pkl"
    if os.path.exists(pkl_path):
        logging.info("pkl found! loading map %s", pkl_path)
        m, rev_m = load(pkl_path)
    else:
        f = open(path)
        if wid:
            m = {K.NULL_TITLE_WID: K.NULL_TITLE_ID}
        else:
            m = {K.OOV_TOKEN: K.OOV_ID}
        logging.info("loading vocab from %s", path)
        for idx, l in enumerate(f):
            word = l.strip()
            m[word] = idx + 1
        rev_m = {v: k for k, v in m.items()}
        logging.info("vocab of size %d loaded", len(m))
        logging.info("saving pkl... %s", pkl_path)
        obj = m, rev_m
        save(pkl_path, obj)
    return m, rev_m


def load_wid2desc(path):
    f = open(path)
    m = {}
    err = 0
    logging.info("loading desc from %s", path)
    for idx, l in enumerate(f):
        parts = l.strip().split("\t")
        if len(parts) != 2:
            # logging.info("error on line %d %s", idx, parts)
            err += 1
            continue
        k, v = parts
        m[k] = v.split(" ")
    m[K.NULL_TITLE_WID] = 100 * [K.OOV_TOKEN]  # [K.OOV_ID]
    logging.info("map of size %d loaded err lines %d", len(m), err)
    return m


def map_desc(wid2desc, w2i):
    logging.info("prepping descvecs")
    padded_cnt = 0
    trimmed_cnt = 0
    # missed = 0
    # descs = []
    # for i in range(len(idx2wid)):
    # wid = idx2wid[i]
    # if wid not in wid2desc:
    #     missed += 1
    #     desc_idxs = [K.OOV_ID] * 100
    # else:
    ans = {}
    for wid in wid2desc:
        tokens = wid2desc[wid]
        desc_idxs = [get_idx(word=tok, w2i=w2i) for tok in tokens]
        desc_idxs = [idx for idx in desc_idxs if idx != K.OOV_ID]
        if len(desc_idxs) < 100:
            desc_idxs += [K.OOV_ID] * (100 - len(desc_idxs))
            padded_cnt += 1
        else:
            desc_idxs = desc_idxs[:100]
            trimmed_cnt += 1
        # descs.append(desc_idxs)
        # if i > 0 and i % 10000 == 0:
        #     logging.info("seen %d", i)
        ans[wid] = desc_idxs
    logging.info("padded %d trimmed %d desc", padded_cnt, trimmed_cnt)
    return ans


def load_wid2title_map(path):
    pkl_path = path + ".pkl"
    if os.path.exists(pkl_path):
        logging.info("pkl found! loading map %s", pkl_path)
        m, rev_m = load(pkl_path)
    else:
        f = open(path)
        m = {K.NULL_TITLE_WID: K.NULL_TITLE}  # wiki id for NULL_TITLE
        logging.info("loading vocab from %s", path)
        for idx, l in enumerate(f):
            parts = l.strip().split("\t")
            if len(parts) != 3: continue
            wid, title, cnt = parts
            m[wid] = title
        rev_m = {v: k for k, v in m.items()}
        logging.info("vocab of size %d loaded", len(m))
        logging.info("saving pkl... %s", pkl_path)
        obj = m, rev_m
        save(pkl_path, obj)
    return m, rev_m


def load_title2cnt(f):
    pkl_path = f + ".pkl"
    if os.path.exists(pkl_path):
        logging.info("found counts pkl %s", pkl_path)
        title2cnt = load(pkl_path)
        return title2cnt
    else:
        title2cnt = {}
        for line in open(f):
            parts = line.strip().split("\t")
            if len(parts) != 3:
                continue
            _, title, cnt = parts
            title2cnt[title] = int(cnt)
        save(pkl_path, title2cnt)
        logging.info("saving counts pkl to %s", pkl_path)
    return title2cnt


# TODO this is useless
def load_xiao_mid2name(path="data/xiao/mid2name.tsv"):
    pkl_path = path + ".pkl"
    if os.path.exists(pkl_path):
        logging.info("pkl found! loading map %s", pkl_path)
        xiao_mid2names = load(pkl_path)
    else:
        xiao_mid2names = {}
        for line in open(path):
            parts = line.strip().split('\t')
            if len(parts) != 2: continue
            mid, name = parts
            mid = mid.strip("/")
            mid = mid.replace("/", ".")
            if mid not in xiao_mid2names:
                xiao_mid2names[mid] = []
            xiao_mid2names[mid].append(name)
        logging.info("map of size %d loaded", len(xiao_mid2names))
        logging.info("saving pkl... %s", pkl_path)
        obj = xiao_mid2names
        save(pkl_path, obj)
    return xiao_mid2names


def load_id2title(f):
    pkl_path = f + ".pkl"
    if os.path.exists(pkl_path):
        logging.info("found id2t pkl %s", pkl_path)
        id2t, t2id, redirect_set = load(pkl_path)
    else:
        id2t, t2id = {}, {}
        redirect_set = set([])
        for line in open(f):
            parts = line.strip().split("\t")
            if len(parts) != 3:
                logging.info("bad line %s", line)
                continue
            # page_id, title = parts
            page_id, page_title, is_redirect = parts
            id2t[page_id] = page_title
            t2id[page_title] = page_id
            if is_redirect == "1":
                redirect_set.add(page_title)
        obj = id2t, t2id, redirect_set
        save(pkl_path, obj)
        logging.info("saving id2t pkl to %s", pkl_path)
    logging.info("id2t of size %d", len(id2t))
    return id2t, t2id, redirect_set


def load_disamb2title(f):
    id2t, t2id = load_map(f)
    return id2t, t2id


def load_redirects(path):
    pkl_path = path + ".pkl"
    if os.path.exists(pkl_path):
        logging.info("pkl found! loading map %s", pkl_path)
        redirect2title = load(pkl_path)
    else:
        f = open(path)
        redirect2title = {}
        err = 0
        logging.info("pkl not found ...")
        logging.info("loading map from %s", path)
        for idx, l in enumerate(f):
            parts = l.strip().split("\t")
            if len(parts) != 2:
                logging.info("error on line %d %s", idx, parts)
                err += 1
                continue
            redirect, title = parts
            if redirect in redirect2title:
                logging.info("duplicate keys! was this on purpose?")
            redirect2title[redirect] = title
        logging.info("map of size %d loaded %d err lines", len(redirect2title), err)
        logging.info("saving pkl... %s", pkl_path)
        obj = redirect2title
        save(pkl_path, obj)
    logging.info("r2t of size %d", len(redirect2title))
    return redirect2title


NamedEntity = namedtuple('NamedEntity', ['wid', 'title', 'mid', 'types', 'count'])


def load_nekb(kbfile):
    # ="data/enwiki/wid_title_mid_types_counts.txt"
    pkl_path = kbfile + ".nekb.pkl"
    if os.path.exists(pkl_path):
        logging.info("pkl found! loading map %s", pkl_path)
        wid2ne, mid2ne, title2ne = load(pkl_path)
    else:
        logging.info("pkl not found! making nekb maps...")
        wid2ne, mid2ne, title2ne = {}, {}, {}
        for idx, line in enumerate(open(kbfile)):
            parts = line.strip().split("\t")
            # print(parts)
            title, wid, mid, types, cnt = parts
            cnt = int(cnt)
            types = types.split(" ")
            ne = NamedEntity(wid, title, mid, types, cnt)
            wid2ne[ne.wid] = ne
            mid2ne[ne.mid] = ne
            title2ne[ne.title] = ne
        obj = wid2ne, mid2ne, title2ne
        save(pkl_path, obj)
    return wid2ne, mid2ne, title2ne


def memory_usage_psutil():
    # return the memory usage in GB
    import psutil
    process = psutil.Process(os.getpid())
    mem = process.memory_info()[0] / float(2 ** 30)
    logging.info("current memory usage:%d GB", mem)
    return mem


ConllToken = namedtuple("ConllToken",
                        ['token', "wikititle",
                         "name_mention",
                         "entity_type",
                         "entity_type_confidence",
                         "enwikititle",
                         "tag"])


def load_prob_map(out_prefix, kind):
    path = out_prefix + "." + kind
    pkl_path = path + ".pkl"
    if os.path.exists(pkl_path):
        logging.info("pkl found! %s", pkl_path)
        mmap = load(pkl_path)
    else:
        mmap = defaultdict(lambda: defaultdict(float))
        logging.info("loading from %s", path)
        for idx, line in enumerate(open(path)):
            parts = line.split("\t")
            if len(parts) != 4:
                logging.info("error on line %d: %s", idx, line)
                continue
            y, x, prob, _ = parts
            mmap[y][x] = float(prob)
        logging.info("pkling ... %s", pkl_path)

        pkl_map = {}
        for y in mmap:
            if y not in pkl_map: pkl_map[y] = {}
            for x in mmap[y]:
                pkl_map[y][x] = mmap[y][x]
        save(pkl_path, pkl_map)
    return mmap


def get_conll_sentences(filename):
    """
    Returns all the (content) sentences in a corpus file
    :param corpus_file: the corpus file
    :return: the next sentence (yield)
    """
    bad = 0
    # Read all the sentences in the file
    f_in = open(filename)
    s = []
    for line in f_in:
        if len(line.strip()) == 0:
            yield s
            s = []
        else:
            parts = line.strip().split(' ')
            if len(parts) == 3:
                token, _, tag = parts
                s.append(ConllToken(token=token, wikititle=None, name_mention=None,
                                    entity_type=None, entity_type_confidence=None, enwikititle=None, tag=tag))
            elif len(parts) == 7:
                token, wikititle, name_mention, entity_type, entity_type_confidence, enwikititle, tag = parts
                conlltok = ConllToken(token, wikititle, name_mention, entity_type, entity_type_confidence, enwikititle,
                                      tag)
                s.append(conlltok)
            else:
                bad += 1
    logging.info("bad line %d", bad)


def safe_next(it):
    try:
        return next(it)
    except StopIteration:
        it.reset()
        return next(it)


class InterleaveIterator:
    def __init__(self, iterators, dist, maxsteps):
        self.cnt = 0
        if len(iterators) != len(dist):
            logging.info("dist %s",dist)
            logging.info("iterators %s",len(iterators))
            raise NotImplementedError
        self.iterators = iterators
        self.seen = {i: 0 for i, _ in enumerate(iterators)}
        self.finished = False
        self.dist = dist
        self.maxsteps = maxsteps

    def reset(self):
        pass
        # self.finished = False
        # self.small_it.reset()

    def __iter__(self):  # needed to make iterator
        return self

    # def stop_or_next(self):
    #     try:
    #         nxt = next(self.small_it)
    #         return nxt
    #     except StopIteration:
    #         self.finished = True
    #         raise StopIteration

    def __next__(self):

        if self.finished:
            raise StopIteration

        idx = np.random.choice(range(len(self.iterators)), p=self.dist)
        # idx = self.cnt % self.freq
        # if idx == 0:
        #     # print("self.cnt",self.cnt)
        #     nxt = safe_next(self.train_it)
        # elif idx == 1:
        #     # print("self.cnt",self.cnt)
        #     nxt = safe_next(self.it1)
        # elif idx == 2:
        #     # print("self.cnt",self.cnt)
        #     nxt = safe_next(self.it2)
        # else:
        #     # print("self.cnt",self.cnt)
        #     # nxt = self.stop_or_next()
        #     nxt = safe_next(self.small_it)
        nxt = safe_next(self.iterators[idx])
        self.seen[idx] += 1
        self.cnt += 1
        if self.cnt % 5000 == 0:
            logging.info("%s %d", self.seen, sum(self.seen.values()))
        # if self.cnt >= self.maxsteps:
        #     self.finished = True
        #     logging.info("finishing!")
        #     logging.info("%s %d", self.seen, sum(self.seen.values()))
        return nxt


class MixedIterator:
    def __init__(self, small_it, large_it, max_small_iters, freq=2):
        self.cnt = 0
        self.small_it = small_it
        self.large_it = large_it
        self.freq = freq
        self.small_iters = 0
        self.max_small_iters = max_small_iters

    def reset(self):
        pass
        # if self.max_small_iters == self.small_iters:
        #     return
        # else:
        #     self.small_it.reset()
        # self.large_it.reset()

    def __iter__(self):  # needed to make iterator
        return self

    def __next__(self):
        if self.small_iters >= self.max_small_iters:
            logging.info("Stopping because enough small iters made!")
            raise StopIteration
        self.cnt += 1
        if self.cnt % self.freq == 0:
            # logging.info("sending large")
            # print("sending large")
            try:
                return next(self.large_it)
            except StopIteration:
                self.large_it.reset()
                return next(self.large_it)
        # logging.info("sending small")
        # print("sending small")
        try:
            return next(self.small_it)
        except StopIteration:
            # logging.info("resetting small")
            self.small_it.reset()
            self.small_iters += 1
            # print("resetting small iters:",self.small_iters)
            if self.small_iters >= self.max_small_iters:
                logging.info("Stopping because enough small iters made!")
                # print("Stopping because enough small iters made!")
                # sys.exit(0)
                raise StopIteration
            else:
                return next(self.small_it)


def read_candidates_dict(path):
    ddict = {}
    f = open(path)
    missing_gold = 0
    for linum, line in enumerate(f):
        parts = line.strip().split("\t")
        surface, gold_wid, was_missed, candidates = parts[0], parts[1], parts[2], parts[3:]
        surface = surface[len("surface:"):]
        gold_wid = gold_wid[len("gold_wid:"):]
        candidates = [c.split('|') for c in candidates]
        cand_w_labels = []
        ###############
        ans = [(gold_wid, 0.0, 1)]
        found = False
        for c in candidates:
            title, wid, p_t_given_s, label = c[0], c[1], float(c[2]), int(c[4])
            # CAREFUL wid is STRING
            if gold_wid == wid:
                found = True
                ans[0] = (gold_wid, p_t_given_s, 1)
            else:
                ans.append((wid, p_t_given_s, label))
        if not found and len(candidates) > 0:
            ans = ans[:len(candidates)]
        wids, wid_cprobs, isgolds = zip(*ans)
        wids, wid_cprobs, isgolds = list(wids), list(wid_cprobs), list(isgolds)
        ddict[(surface, gold_wid)] = wids, wid_cprobs, isgolds
        ###############
        #######REPLACE########
        # for c in candidates:
        #     title, wid, p_t_given_s, label = c[0], c[1], float(c[2]), int(c[4])
        #     # CAREFUL wid is STRING
        #     cand_w_labels.append((title, wid, p_t_given_s, label))
        # found = False
        # for c_w_l in cand_w_labels:
        #     if c_w_l[-1] == 1:
        #         if found:
        #             print("cannot have more than one gold in candidates!")
        #             sys.exit(0)
        #         found = True
        # if not found:
        #     logging.info("missing gold %s %s", surface, gold_wid)
        #     print(surface, gold_wid, cand_w_labels)
        #     missing_gold += 1
        #     continue
        # cand_w_labels = sorted(cand_w_labels, key=lambda cand: -1 * cand[-1])
        # _, wids, wid_cprobs, isgolds = zip(*cand_w_labels)
        # wids, wid_cprobs, isgolds = list(wids), list(wid_cprobs), list(isgolds)
        # ddict[(surface, gold_wid)] = wids, wid_cprobs, isgolds
        #######REPLACE########
    logging.info("#%d missed gold in candidates!", missing_gold)
    return ddict


if __name__ == '__main__':
    read_candidates_dict(sys.argv[1])
