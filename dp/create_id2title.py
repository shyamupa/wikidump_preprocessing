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

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)


def parse_schema(wikiprefix, encoding):
    """
    Parameters
    ----------------
    wikiprefix: str
        The prefix for the data file ()

    Returns
    ---------------
    Dictionary that maps field name to zero indexed number
    For instance, given:
    ...
    `page_id` int(8) unsigned NOT NULL AUTO_INCREMENT,
    `page_namespace` int(11) NOT NULL DEFAULT '0',
    `page_title` varbinary(255) NOT NULL DEFAULT '',
    `page_restrictions` tinyblob NOT NULL,
    ...
    This should return {`page_id` : 0, `page_namespace` : 1, `page_title` : 2, `page_restrictions` : 3}
    """
    schema = {}
    filename = wikiprefix + "-page.sql.gz"
    logging.info("Parsing schema for %s", filename)
    f = gzip.open(filename, "rt", encoding=encoding)
    start_parse = False
    fields = []
    for line in f:
        if start_parse:
            if "PRIMARY KEY" not in line:
                fields.append(line)
            else:
                break
        else:
            if not line.startswith("CREATE TABLE"):
                continue
            else:
                start_parse = True
    f.close()
    for i, s in enumerate(fields):
        schema[s.split()[0][1:-1]] = i
    return schema


def split_str(split_char, split_str):
    """
    Parameters
    -------------
    split_char: char
        The character to split upon
    split_str: str
        The string to split

    Returns
    -------------
    List of string tokens splitted by split_char
    
    This takes care of corner cases such as quotation: "xx,xx" and escape character, 
    which will not be handled correctly by python split function.
    """
    return_list = []
    i = 0
    last_pos = 0
    while i < len(split_str):
        if split_str[i] == '\'':
            i += 1
            while split_str[i] != '\'' and i < len(split_str):
                if split_str[i] == '\\':
                    i += 2
                else:
                    i += 1
        else:
            if split_str[i] == split_char:
                return_list.append(split_str[last_pos:i])
                last_pos = i + 1
        i += 1
    return_list.append(split_str[last_pos:])
    return return_list


def read_id2title(wikiprefix, encoding, outpath):
    """
    page id in fr wikipedia --> target_lang (usually en) wikipedia title
    """
    filename = wikiprefix + "-page.sql.gz"
    logging.info("Reading id2title sql" + filename)
    schema = parse_schema(wikiprefix, encoding)
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
