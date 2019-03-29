# coding=utf-8
from bs4 import BeautifulSoup
from dp.title_normalizer import TitleNormalizer
from utils.misc_utils import load_id2title, load_redirects
from multiprocessing import Process
import argparse
import sys
import os
import json
import copy
import logging

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)
import urllib.parse

"""
Class that encapsulates information about one link
"""
class LinkInfo:
    """
    Parameters
    --------------
    text: str
        The text value of the link
    href: str
        The href value of the link
    """
    def __init__(self, text, href):
        self._text = text
        self._href = href
        self._start = -1

    """
    Parameters
    -------------
    location_start: str
        The location of the link inside the original article
    -------------
    Used to set location of the link
    """
    def set_location(self, location_start):
        self._start = location_start

    """
    Get text from link
    """
    def text(self):
        return self._text

    """
    Return the link information as a python dictionary object

    Returns
    -------------
    A python dictionary object with the following keys:
        start: The start position of the link in the original article. This will be the same as the location set through set_location call
        end: The end position of the link in the original article
        label: The link label marked by href
    """
    def as_result(self):
        processed_href = urllib.parse.unquote(self._href).replace(' ', '_')
        return {'start': self._start, 'end': self._start + len(self._text), 'label': processed_href}


"""
Extract link information from one file and dumps into json outputs

Parameters
------------------
file_path: str
    Input file path, should be a complete path
encoding: str
    Encoding of the input file
out_path: str
    Output file path, should be a complete path
normalizer: TitleNormalizer object
    Normalizer to use to normalize the the titles
ignore_null: Bool
    If ignore_null is set to True, output will not contain titles that cannot be normalized through the normalizer. 
    Otherwise, NULLTITLE will be included in the output file

Returns
-------------------
Number of articles processed

Side Effect
-------------------
Outputs two file, one named `out_path`, containing a list of page with their text, id, title, text, and linked_spans. 
Another named `out_path.brief`, where linked_span info is omitted
"""
def extract_from_one_file(file_path, encoding, out_path, normalizer, ignore_null):
    pages = []
    pages_brief = []
    doc_count = 0
    with open(file_path, 'r', encoding=encoding) as f:
        soup = BeautifulSoup(f, "html.parser")
        for doc in soup.find_all('doc'):
            doc_count += 1
            this_page = {}
            this_page['curid'] = doc['id']
            this_page['title'] = doc['title']
            this_page['text'] = doc.get_text()
            pages_brief.append(copy.copy(this_page))
            this_page['linked_spans'] = []

            list_of_links = []
            next_search_pos = 0

            for c in doc.contents:
                # node is link:
                if c.name == 'a':
                    prev_node = c.previous_sibling
                    next_node = c.next_sibling
                    if prev_node is None and next_node is None:
                        raise RuntimeError("Page contained one link and nothing else, is data corrupted?")
                    # Skip the links that has its text section as nested tag (for example, the <nowiki> links)
                    if len(c.contents) != 1:
                        continue
                    if c.contents[0].name is not None:
                        continue

                    # Text of the link, for instance, in the link <a href=xxx>link</a>, text is 'link'
                    link_text = c.contents[0]

                    # The text of previous node (usually just text paragraph), the link node's text, and the next node's text will uniquely identify the location of the link in the text
                    # For instance, if we have the following selection from an article:
                    # 
                    # Consider this <a href='Article'>article</a> which contains a link
                    #
                    # In the case above, link node would be <a href='Article'>article</a>, prev_node would be the string 'Consider this ', and next_node would be ' which contains a link'
                    # The assembled search string would be 'Consider this article which contains a link'. Searching that in the processed text of the web page would give us the location of the search string
                    # We then add length of the prev_node to that location to get the location of the link
                    # Notice that there is a chance that this search string may appear more than once. For this purpose, we keep a record of last search position and starts every new search from that. 
                    prev_node_search_str = ""
                    if prev_node is not None:
                        if prev_node.name is None:
                            prev_node_search_str = prev_node
                        else:
                            # handle the case when the prev_node is also a link
                            prev_node.get_text()
                    next_node_search_str = ""
                    if next_node is not None:
                        if next_node.name is None:
                            next_node_search_str = next_node
                        else:
                            next_node.get_text()
                    link_and_adjacent_text_search_str = prev_node_search_str + link_text + next_node_search_str;        
                    loc = this_page['text'].find(link_and_adjacent_text_search_str,
                                                 next_search_pos)
                    next_search_pos = loc + 1
                    this_link_info = LinkInfo(link_text, c['href'])
                    this_link_info.set_location(loc + len(prev_node_search_str))
                    link_result = this_link_info.as_result()

                    actual_partition = this_page['text'][link_result['start']:link_result['end']]
                    # check if the parsed location is correct
                    if actual_partition != this_link_info.text():
                        logging.warning('got in text: %s, expected %s' % (actual_partition, link_result['label']))
                    else:
                        link_result['label'] = normalizer.normalize(link_result['label'])
                        if not ignore_null:
                            list_of_links.append(link_result)
                        else:
                            if link_result['label'] != 'NULLTITLE':
                                list_of_links.append(link_result)

            # if there are no links, we can move onto the next doc
            if len(list_of_links) == 0:
                logging.debug("Page titled %s in file %s has no links" % (this_page['title'], file_path))
                pages.append(this_page)
                continue
            else:
                this_page['linked_spans'] = list_of_links

            pages.append(this_page)

    dir_to_write = os.path.dirname(out_path)
    os.makedirs(dir_to_write, exist_ok=True)
    with open(out_path, 'w') as out_f:
        out_f.write(json.dumps(pages, indent=4))
    with open("%s.brief" % out_path, 'w') as out_f:
        out_f.write(json.dumps(pages_brief, indent=4))
    return doc_count


"""
Extract link information from one directory and dumps into json outputs

Parameters, Returns and Side Effect similar to extract_from_one_file
"""
def extract_from_one_directory(directory, out, encoding, normalizer, ignore_null):
    all_files = []
    for f in os.listdir(path=directory):
        full_path = os.path.join(directory, f)
        all_files.append(full_path)
    num_articles = 0
    for wiki in all_files:
        original_dir = os.path.basename(os.path.dirname(wiki))
        original_file_name = os.path.basename(wiki)
        num_articles += extract_from_one_file(wiki, encoding, os.path.join(out, "%s/%s.json" % (original_dir, original_file_name)),
                              normalizer, ignore_null)
    logging.info("Process with pid %d finished, processed %d files and %d articles" % (os.getpid(), len(all_files), num_articles))

"""
Extract link information from one directory's subdirectories and dumps into json outputs

Parameters
------------------
dump_prefix: str
    Input file directory, all input files should be directly under this directory's subdirectories
out: str
    Output file directory, all output files will be staged under this directory's subdirectories, preserving the input directory's file layout
encoding: str
    Encoding of the input file
normalizer: TitleNormalizer object
    Normalizer to use to normalize the the titles
ignore_null: Bool
    If ignore_null is set to True, output will not contain titles that cannot be normalized through the normalizer. 
    Otherwise, NULLTITLE will be included in the output file

Returns
-------------------
Nothing

Side Effect
-------------------
Outputs N*2 files, where N is number of files under input directory's subdirs. 
For each file, two json output will be produced, as specified by extract_from_one_file function

It will create one process per subdirectory to parallelize the work 
On most systems the default behavior will most likely utilize all the cores available.
"""       
def extract_links(dump_prefix, out, encoding, normalizer, ignore_null):
    dump_prefix_abs = os.path.abspath(dump_prefix)
    all_files = []
    all_dirs = []
    for directory in os.listdir(path=dump_prefix_abs):
        subdir = os.path.join(dump_prefix_abs, directory)
        # Should not append non directory file to path
        if os.path.isdir(subdir):
            all_dirs.append(subdir)
    ps = []
    for directory in all_dirs:
        # Start one process per subdirectory
        proc = Process(target=extract_from_one_directory, args=(directory, out, encoding, normalizer, ignore_null));
        ps.append(proc)
        logging.info("Started new process to handle directory %s" % directory)
    for p in ps:
        p.start()
    for p in ps:
        p.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract links from downloaded wiki pages')
    parser.add_argument('--dump', type=str, required=True,
                        help='prefix to the dumped pages, e.g., trwiki_with_links')
    parser.add_argument('--out', type=str, required=True,
                        help='json file to write the link info in. eg. trwiki-20170420.json')
    parser.add_argument('--id2t', type=str, required=True, help='id --> title')
    parser.add_argument('--redirects', type=str, required=True, help='redirect --> title')
    parser.add_argument('--lang', type=str, required=True, help='language code')
    parser.add_argument('--preserve-null', type=str, required=False, help='if ignore null links in output')
    args = parser.parse_args()
    args = vars(args)
    redirect2title = load_redirects(args["redirects"])
    id2t, t2id, is_redirect_map = load_id2title(args["id2t"])
    normalizer = TitleNormalizer(lang=args['lang'],
                                 redirect_map=redirect2title,
                                 t2id=t2id)
    extract_links(dump_prefix=args["dump"], out=args["out"], encoding="utf-8", normalizer=normalizer,
                  ignore_null='preserve-null' not in args)
