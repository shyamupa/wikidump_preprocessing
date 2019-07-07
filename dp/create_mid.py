# coding=utf-8
from spacy.tokenizer import Tokenizer
import json
import spacy.util
import argparse
import sys
import os
from multiprocessing import Process
from dp.title_normalizer import TitleNormalizer
from utils.misc_utils import load_id2title, load_redirects
import logging

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)

"""
Return a tokenizer built from a given langauge code (e.g. 'en' for English)

Returns
----------
A tokenizer object

Parameters
----------
lang Language code
"""
def get_tokenizer(lang):
    lang_cls = spacy.util.get_lang_class(lang)
    return lang_cls().Defaults.create_tokenizer()

"""
Check if a token has intersection with the link

"""
def check_if_tok_match_link(link, token):
    link_start = link['start']
    link_end = link['end']
    tok_start = token.idx
    tok_end = token.idx + len(token)
    if tok_start >= link_end:
        return False
    if tok_end < link_start:
        return False
    return True

"""
Produce one MID file given one json file containing info on links

Parameters
----------
window Size of context window
filename File path of the input json file
encoding Encoding of the input file
outfile File path of the output csv file. Result will be written into this file
tokenizer Tokenizer to use, should be a spacy Tokenizer object
normalizer Normalizer to use to normalize the titles
"""
def create_mid_for_one_file(window, filename, tokenizer, encoding, outfile, normalizer):
    f = open(filename, 'r', encoding=encoding)
    doc = json.load(f)
    info_to_dump = []
    for article in doc:
        article_id = article['curid']
        article_title = article['title']
        article_all_mentions = []
        tok_info = []
        links = None
        if 'linked_spans' in article:
            links = article['linked_spans']
        article_text = article['text']

        if links is not None:
            toks_info = []
            article_toks = tokenizer(article_text)
            for link in links:
                # Add to all mentions for the article
                article_all_mentions.append(link['label'])
                # Get the tokens that intersects with the link
                matched_toks = [tok for tok in article_toks if check_if_tok_match_link(link, tok)]
                if len(matched_toks) > 0:
                    # Sort the tokens based on its index in the document
                    link_toks = sorted(matched_toks, key=lambda t : t.i)
                    tok_start_idx = matched_toks[0].i
                    tok_end_idx = matched_toks[-1].i
                    tok = {'start': tok_start_idx, 'end': tok_end_idx, 'mention': link['label'], 'window': article_text[link['start'] - window:link['end'] + window]}
                    tok_info.append(tok)
        info_to_dump.append({'id': article_id, 'title': article_title, 'mentions': ' '.join(article_all_mentions), 'links': tok_info})
    f.close()

    # dump to file
    with open(outfile, 'w', encoding=encoding) as csvfile:
        # writer = csv.writer(csvfile, dialect='excel-tab')
        for article in info_to_dump:
            if len(article['links']) > 0:
                for l in article['links']:
                    buf = "\t".join(['MID',
                                     article['id'],
                                     normalizer.normalize(article['title']),
                                     str(l['start']),
                                     str(l['end']),
                                     l['mention'],
                                     l['window'],
                                     article['mentions']])
                    csvfile.write(buf)


"""
Produce MID files for a list of input files and output files

Parameters
----------
inputs List of input files
outputs List of output files
"""
def batch_create_mids(inputs, outputs, window, tokenizer, encoding, normalizer):
    if len(inputs) != len(outputs):
        raise RuntimeError("Input and Output is not the same length!")
    for i in range(len(inputs)):
        create_mid_for_one_file(window, inputs[i], tokenizer, encoding, outputs[i], normalizer)

"""
Produce MID files given a directory where json files live in its subdirectories

Parameters
----------
link_dump_prefix Path to directory containing all input json files. For instance 'output/trwiki/output/link_in_pages'
out Path to output directory. For instance 'output/trwiki/output/mid'

Side Effects
------------
It will create one process per CPU allowed for this parent process. To limit CPU usage, use taskset
"""
def create_mids(link_dump_prefix, out, encoding, lang, window, normalizer):
    dump_prefix_abs = os.path.abspath(link_dump_prefix)
    out_abs = os.path.abspath(out)
    inputs_list = []
    outputs_list = []
    # Get the number of CPUs we are given
    num_cpus = len(os.sched_getaffinity(0))
    for i in range(num_cpus):
        inputs_list.append([])
        outputs_list.append([])

    next_cpu_idx = 0
    for directory in os.listdir(path=dump_prefix_abs):
        subdir = os.path.join(dump_prefix_abs, directory)
        # Should not append non directory file to path
        if os.path.isdir(subdir):
            outdir = os.path.join(out_abs, directory)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            # Schedule work per cpu
            for f in os.listdir(path=subdir):
                if f.endswith('.json'):
                    inputs_list[next_cpu_idx].append(os.path.join(subdir, f))
                    outputs_list[next_cpu_idx].append(os.path.join(outdir, os.path.splitext(f)[0] + '.csv'))
                    next_cpu_idx += 1
                    next_cpu_idx %= num_cpus

    ps = []
    logging.info('%d CPU(s) will be used' % num_cpus)
    for i in range(num_cpus):
        logging.info('# %d CPU will handle %d files' % (i, len(inputs_list[i])))
    tokenizer = get_tokenizer(lang)
    for i in range(num_cpus):
        # Start one process per cpu available
        proc = Process(target=batch_create_mids, args=(inputs_list[i], outputs_list[i], window, tokenizer, encoding, normalizer))
        ps.append(proc)
    for p in ps:
        p.start()
    for p in ps:
        p.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Produce MID files from links info')
    parser.add_argument('--dump', type=str, required=True,
                        help='prefix to the dumped json file containing link info, e.g., link_in_pages')
    parser.add_argument('--out', type=str, required=True,
                        help='Directory to dump csv files, e.g., mid')
    parser.add_argument('--id2t', type=str, required=True, help='id --> title')
    parser.add_argument('--redirects', type=str, required=True, help='redirect --> title')
    parser.add_argument('--lang', type=str, required=True, help='language code')
    parser.add_argument('--window', type=str, required=True, help='context window length')
    args = parser.parse_args()
    args = vars(args)
    redirect2title = load_redirects(args["redirects"])
    id2t, t2id, is_redirect_map = load_id2title(args["id2t"])
    normalizer = TitleNormalizer(lang=args['lang'],
                                 redirect_map=redirect2title,
                                 t2id=t2id)
    create_mids(link_dump_prefix=args["dump"], out=args["out"], encoding="utf-8", lang=args['lang'], window=int(args['window']), normalizer=normalizer)
