from bs4 import BeautifulSoup
from processors.abstract_processor import AbstractProcessor


class BasicPageProcessor(AbstractProcessor):
    def __init__(self, wikipath):
        super(BasicPageProcessor, self).__init__(wikipath)

    def process_file(self, f_handle):
        page_content = ""
        new_page = False
        page_id, page_title = None, None
        for line in f_handle:
            if line.startswith("<doc id="):
                new_page = True
                if page_content:
                    self.process_wikicontent(page_content, page_id, page_title)
                page_content = ""
                soup = BeautifulSoup(line, "html.parser")
                doc = soup.find("doc")
                page_id = doc["id"]
                page_title = doc["title"].replace(" ", "_")
            else:
                if new_page:
                    new_page = False
                    continue  # do not add this line as it contains title
                page_content += line
        if page_content:
            self.process_wikicontent(page_content, page_id, page_title)

    def process_wikicontent(self, page_content, page_id, page_title):
        pass
