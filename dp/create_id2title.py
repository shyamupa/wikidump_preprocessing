# coding=utf-8
"""
Creates a map from wikipedia page id to wikipedia page title.
For instance the page id 534366 corresponds to the wikipedia page of "Barack_Obama".

Requires: The relevant *-page.sql.gz file
Arguments:
    1. prefix to the wikipedia dump (e.g., enwiki-20181020). The script reads the relevant information from the
    *-page.sql.gz file
    2. output filename. Output is tsv file with id and title as columns.
"""
from __future__ import print_function

import argparse
import gzip
import logging
from .dp_common import *

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)

def read_id2title(wikiprefix, encoding, outpath):
    """
    page id in fr wikipedia --> target_lang (usually en) wikipedia title
    """
    filename = wikiprefix + "-page.sql.gz"
    logging.info("Reading id2title sql" + filename)
    schema = parse_schema(filename, encoding)
    f = gzip.open(filename, "rt", encoding=encoding)
    bad = 0
    with open(outpath, "w") as out:

        for line in f:
            if "INSERT INTO" not in line:
                continue
            start = line.index("(")
            line = line[start + 1:]
            parts = line.split("),(")
            for part in parts:
                all_fields = split_str(',', part)
                if len(all_fields) != len(schema):
                    logging.info(
                        "warning: ignore part as number of fields does not match schema %s, %d but expected %d", part,
                        len(all_fields), len(schema))
                    bad += 1
                    continue
                page_id = all_fields[schema['page_id']]
                ns = all_fields[schema['page_namespace']]
                page_title = all_fields[schema['page_title']]
                # only ns 0 is genuine page, others are discussions, category pages etc.
                if ns != "0":
                    continue
                is_redirect = all_fields[schema['page_is_redirect']]
                # strip out the single quotes around 'Title'
                # page_title.strip("'") might remove genuine extra quotes around some titles, so should not be used
                page_title = page_title[1:-1]
                if "\\" in page_title:
                    page_title = page_title.replace("\\", "")
                # print(part)
                buf = "\t".join([page_id, page_title, is_redirect])
                # buf = "\t".join([page_id, page_title])
                out.write(buf + "\n")
        logging.info("warning: total bad formats in file: %d", bad)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a page id to title map.')
    parser.add_argument('--wiki', type=str, required=True,
                        help='prefix to the relevant wikipedia dump, e.g., enwiki-20181020')
    parser.add_argument('--out', type=str, required=True, help='tsv file to write the map in. eg. enwiki-20170420.id2t')
    args = parser.parse_args()
    args = vars(args)
    logging.info("reading id2title from sql file")
    read_id2title(wikiprefix=args["wiki"], outpath=args["out"], encoding="utf-8")
