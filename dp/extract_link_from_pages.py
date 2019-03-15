# coding=utf-8

from bs4 import *
import argparse
import sys
import os
import json

def extract_from_one_file(file_path, encoding, out_path):
    pages = []
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
            for link in doc.find_all('a'):
                this_link = {}
                this_link['label'] = link['href']
                this_link['start'] = 0
                this_link['end'] = 0
                this_page['linked_spans'].append(this_link)
            pages.append(this_page)
    with open(out_path, 'w') as out_f:
        out_f.write(json.dumps(pages, indent=4))
    return doc_count

def extract_links(dump_prefix, out, encoding):
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
        doc_count += extract_from_one_file(wiki, encoding, os.path.join(out, "%d.json" % count))
        count += 1
        sys.stdout.write("\b[%10d / %10d] Files, %10d Articles Processed\r" % (count, len(all_files), doc_count))
        sys.stdout.flush()
    sys.stdout.write("\n")
    sys.stdout.flush()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract links from downloaded wiki pages')
    parser.add_argument('--dump', type=str, required=True,
                        help='prefix to the dumped pages, e.g., trwiki_with_links')
    parser.add_argument('--out', type=str, required=True, help='json file to write the link info in. eg. trwiki-20170420.json')
    args = parser.parse_args()
    args = vars(args)
    extract_links(dump_prefix=args["dump"], out=args["out"], encoding="utf-8")
