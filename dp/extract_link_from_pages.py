# coding=utf-8

from bs4 import BeautifulSoup
from dp.title_normalizer import TitleNormalizer
from utils.misc_utils import load_id2title, load_redirects
import argparse
import sys
import os
import json
import copy

class LinkInfo:
    def __init__(self, link_full_text, text, href):
        self._full_text = link_full_text
        self._text = text
        self._href = href
        self._start = -1
        self._extra_count = len(link_full_text) - len(text)
        self._text_start = link_full_text.rfind(text)

    def set_location(self, location_start):
        self._start = location_start

    def set_processed_loc(self, result):
        self._processed_start = result

    def full_text(self):
        return self._full_text

    def text(self):
        return self._text

    def href(self):
        return self._href

    def text_start(self):
        return self._text_start

    def extra_count(self):
        return self._extra_count

    def location_raw(self):
        return self._start

    def location_processed(self):
        return self._processed_start

    def as_result(self):
        return {'start': self._processed_start, 'end': self._processed_start + len(self._text), 'label': self._text}


def extract_from_one_file(file_path, encoding, out_path, normalizer):
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
            this_page['linked_spans'] = []
            page_str = str(doc)

            all_links_last_searched = {}
            list_of_links = []

            # get all links with their location in raw document
            for link in doc.find_all('a'):
                link_text = ""
                if (len(link.contents) > 0):
                    link_text = str(link.contents[0])
                this_link = LinkInfo(link_full_text=str(link), text=link_text, href=link['href'])
                search_pos = 0
                if this_link.text() not in all_links_last_searched:
                    search_pos = 0
                    all_links_last_searched[this_link.text()] = search_pos
                else:
                    search_pos = all_links_last_searched[this_link.text()]
                found_pos = page_str.find(this_link.full_text(), search_pos)
                if found_pos == -1:
                    raise RuntimeError("link text not found")
                this_link.set_location(found_pos)
                list_of_links.append(this_link)

            # if there are no links, we can move onto the next doc
            if len(list_of_links) == 0:
                pages.append(this_page)
                continue

            # Process link by link
            shrunk_char_count = 0
            current_location = this_page['text'].find(doc.contents[0]) + len(doc.contents[0])
            list_of_links[0].set_processed_loc(current_location)
            first_processed_loc = current_location
            first_raw_loc = list_of_links[0].location_raw()
            shrunk_char_count += list_of_links[0].extra_count()
            this_page_brief = copy.copy(this_page)
            this_page_brief.pop('linked_spans', None)
            pages_brief.append(this_page_brief)
            this_page['linked_spans'].append(list_of_links[0].as_result())
            for i in range(len(list_of_links) - 1):
                current_link = list_of_links[i + 1]
                current_link.set_processed_loc(
                    current_link.location_raw() - first_raw_loc + first_processed_loc - shrunk_char_count)
                shrunk_char_count += current_link.extra_count()
                link_result = current_link.as_result()
                link_result['label'] = normalizer.normalize(link_result['label'])
                this_page['linked_spans'].append(link_result)

            pages.append(this_page)
    dir_to_write = os.path.dirname(out_path)
    os.makedirs(dir_to_write, exist_ok=True)
    with open(out_path, 'w') as out_f:
        out_f.write(json.dumps(pages, indent=4))
    with open("%s.brief" % out_path, 'w') as out_f:
        out_f.write(json.dumps(pages_brief, indent=4))
    return doc_count


def extract_links(dump_prefix, out, encoding, normalizer):
    dump_prefix_abs = os.path.abspath(dump_prefix)
    all_files = []
    for directory in os.listdir(path=dump_prefix_abs):
        subdir = os.path.join(dump_prefix_abs, directory)
        for f in os.listdir(path=subdir):
            full_path = os.path.join(subdir, f)
            all_files.append(full_path)
    pages = []
    count = 0
    doc_count = 0
    for wiki in all_files:
        original_dir = os.path.basename(os.path.dirname(wiki))
        original_file_name = os.path.basename(wiki)
        doc_count += extract_from_one_file(wiki, encoding, os.path.join(out, "%s/%s.json" % (original_dir, original_file_name)), normalizer)
        count += 1
        sys.stdout.write("\b[%10d / %10d] Files, %10d Articles Processed, Done File: %s\r" % (
        count, len(all_files), doc_count, wiki))
        sys.stdout.flush()
    sys.stdout.write("\n")
    sys.stdout.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract links from downloaded wiki pages')
    parser.add_argument('--dump', type=str, required=True,
                        help='prefix to the dumped pages, e.g., trwiki_with_links')
    parser.add_argument('--out', type=str, required=True,
                        help='json file to write the link info in. eg. trwiki-20170420.json')
    parser.add_argument('--id2t', type=str, required=True, help='id --> title')
    parser.add_argument('--redirects', type=str, required=True, help='redirect --> title')
    parser.add_argument('--lang', type=str, required=True, help='language code')
    args = parser.parse_args()
    args = vars(args)
    redirect2title = load_redirects(args["redirects"])
    id2t, t2id, is_redirect_map = load_id2title(args["id2t"])
    normalizer = TitleNormalizer(lang=args['lang'],
                                 redirect_map=redirect2title,
                                 t2id=t2id)
    extract_links(dump_prefix=args["dump"], out=args["out"], encoding="utf-8", normalizer=normalizer)
