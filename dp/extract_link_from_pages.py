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


class LinkInfo:
    def __init__(self, text, href):
        self._text = text
        self._href = href
        self._start = -1

    def set_location(self, location_start):
        self._start = location_start

    def as_result(self):
        return {'start': self._start, 'end': self._start + len(self._text), 'label': self._text}


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
                        raise RuntimeError("Really? Only a link and nothing else?")
                    if len(c.contents) != 1:
                        continue
                    if c.contents[0].name is not None:
                        continue

                    prev_node_search_str = ""
                    if prev_node is not None:
                        if prev_node.name is None:
                            prev_node_search_str = prev_node
                        else:
                            prev_node.get_text()
                    next_node_search_str = ""
                    if next_node is not None:
                        if next_node.name is None:
                            next_node_search_str = next_node
                        else:
                            next_node.get_text()
                    loc = this_page['text'].find(prev_node_search_str + c.contents[0] + next_node_search_str,
                                                 next_search_pos)
                    next_search_pos = loc + 1
                    this_link_info = LinkInfo(c.contents[0], c['href'])
                    this_link_info.set_location(loc + len(prev_node_search_str))
                    link_result = this_link_info.as_result()

                    actual_partition = this_page['text'][link_result['start']:link_result['end']]
                    # check if the parsed location is correct
                    if actual_partition != link_result['label']:
                        sys.stderr.write('got in text: %s, expected %s\n' % (actual_partition, link_result['label']))
                        sys.stderr.flush()
                    else:
                        link_result['label'] = normalizer.normalize(link_result['label'])
                        if not ignore_null:
                            list_of_links.append(link_result)
                        else:
                            if link_result['label'] != 'NULLTITLE':
                                list_of_links.append(link_result)

            # if there are no links, we can move onto the next doc
            if len(list_of_links) == 0:
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


def extract_from_one_directory(directory, out, encoding, normalizer, ignore_null):
    all_files = []
    for f in os.listdir(path=directory):
        full_path = os.path.join(directory, f)
        all_files.append(full_path)
    for wiki in all_files:
        original_dir = os.path.basename(os.path.dirname(wiki))
        original_file_name = os.path.basename(wiki)
        extract_from_one_file(wiki, encoding, os.path.join(out, "%s/%s.json" % (original_dir, original_file_name)),
                              normalizer, ignore_null)


def extract_links(dump_prefix, out, encoding, normalizer, ignore_null):
    dump_prefix_abs = os.path.abspath(dump_prefix)
    all_files = []
    all_dirs = []
    for directory in os.listdir(path=dump_prefix_abs):
        subdir = os.path.join(dump_prefix_abs, directory)
        if os.path.isdir(subdir):
            all_dirs.append(subdir)
    ps = []
    for directory in all_dirs:
        ps.append(Process(target=extract_from_one_directory, args=(directory, out, encoding, normalizer, ignore_null)))
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
