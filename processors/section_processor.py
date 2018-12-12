from collections import Counter

from bs4 import BeautifulSoup
import sys

from processors.abstract_processor import AbstractProcessor
from utils.text_utils import tokenizer

__author__ = 'Shyam'


class SectionProcessor(AbstractProcessor):
    def __init__(self, wikipath, lang):
        super(SectionProcessor, self).__init__(wikipath)
        self.lang = lang
        self.section_cnt = Counter()

    def process_file(self, f_handle):
        page_content = ""
        new_page = False
        page_id, page_title = None, None
        sections = []
        for line in f_handle:
            if line.startswith("<doc id="):
                new_page = True
                if page_content:
                    self.process_wikicontent(page_content, page_id, page_title, sections)
                page_content = ""
                soup = BeautifulSoup(line, "html.parser")
                doc = soup.find("doc")
                page_id = doc["id"]
                page_title = doc["title"].replace(" ", "_")
                sections = []
            else:
                if new_page:
                    new_page = False
                    continue  # do not add this line as it contains title
                if "a href" not in line and len(line.strip()) > 0:
                    tokens = tokenizer(line, lang=self.lang)
                    if len(tokens) < 4:
                        sections.append(line.strip())
                    continue
                page_content += line

    def process_wikicontent(self, page_content, page_id, page_title, sections):
        self.section_cnt.update(sections)
        # print (page_content)

    def finish(self):
        for k in self.section_cnt.most_common():
            print(k)


if __name__ == '__main__':
    p = SectionProcessor(sys.argv[1], lang="en")
    p.run()
