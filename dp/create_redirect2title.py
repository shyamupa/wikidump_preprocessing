# coding=utf-8
import argparse
import os
import logging
import sys
logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)
from utils.misc_utils import load_id2title
import gzip
from .dp_common import *


def read_redirects(filename, encoding, id2t):
    """
    page id in fr wikipedia --> target_lang (usually en) wikipedia title
    """
    logging.info("Reading redirects sql" + filename)
    redirect2title = {}
    total, missed = 0, 0
    schema = parse_schema(filename, encoding)
    if 'rd_from' not in schema:
        raise RuntimeException('Redirect from id not found in schema!')
    if 'rd_title' not in schema:
        raise RuntimeException('Redirect title not found in schema!')
    f = gzip.open(filename, "rt", encoding=encoding,errors="ignore")
    for line in f:
        if "INSERT INTO" not in line:
            continue
        start = line.index("(")
        line = line[start + 1:]
        parts = line.split("),(")
        for part in parts:
            all_fields = split_str(',', part)
            redirect_page_id = all_fields[schema['rd_from']]
            title = all_fields[schema['rd_title']]
            # THIS GETS MISSED BECAUSE WE DO NOT HAVE FR ID TO TITLE FOR ALL PAGES
            #title = title[:len(title) - 1]
            #title = title.replace(" ", "_")
            #if "\\" in title:
            #    title = title.replace("\\", "")
            # print(list(id2t.keys())[0:5])
            if redirect_page_id in id2t:
                re_title = id2t[redirect_page_id]
                # print(re_title,title)
                redirect2title[re_title] = title
            else:
                # print("missed",redirect_page_id)
                missed += 1
            total += 1
    logging.info("missed ids %d total redirects %d", missed, total)
    logging.info("redirect map size %d", len(redirect2title))
    return redirect2title


def page_redirects_from_datamachine(f, id2t):
    redirect2title = {}
    total, missed = 0, 0
    for l in open(f, encoding="utf-8"):
        parts = l.strip().split("\t")
        if len(parts) != 2:
            print("error", parts)
            continue
        page_id, redirect = parts
        # print(pid,redirect)
        if "\\" in redirect:
            redirect = redirect.replace("\\", "")
        if page_id in id2t:
            redirect2title[redirect] = id2t[page_id]
        else:
            # print(pid,redirect)
            missed += 1
        total += 1
    logging.info("missed %d total redirects %d", missed, total)
    return redirect2title


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create a page id to title map.')
    parser.add_argument('--wiki', type=str, required=True, help='path to folder containing output/ from datamachine.')
    parser.add_argument('--id2t', type=str, required=True, help='path to id 2 title map.')
    parser.add_argument('--out', type=str, required=True, help='tsv file to write the redirect-->title map in.')
    args = parser.parse_args()
    args = vars(args)
    id2title_path = args["id2t"]
    wiki_path = args["wiki"]
    outpath = args["out"]
    id2t, t2id, redirect_set = load_id2title(id2title_path)
    # print(len(id2t))
    # sys.exit(0)

    # redirect2title = page_redirects_from_datamachine(os.path.join(wiki_path, "output/page_redirects.txt"), id2t)
    # with open(outpath, "w") as out:
    #     for k in redirect2title:
    #         buf = "\t".join([k, redirect2title[k]])
    #         out.write(buf + "\n")

    redirect2title = read_redirects(wiki_path+"-redirect.sql.gz", "utf-8", id2t)
    with open(outpath, "w") as out:
        if "zhwiki" in wiki_path:
            buf = "\t".join(["杰布·布什", "傑布·布希"])
            out.write(buf + "\n")
        for k in redirect2title:
            buf = "\t".join([k, redirect2title[k]])
            out.write(buf + "\n")
