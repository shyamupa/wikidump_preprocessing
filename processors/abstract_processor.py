import os
import logging


class AbstractProcessor(object):
    def __init__(self, wikipath):
        self.wikipath = wikipath

    def setup(self):
        pass

    def run(self):
        for dirname in sorted(os.listdir(self.wikipath)):
            dirpath = os.path.join(self.wikipath, dirname)
            logging.info(dirpath)
            for filename in sorted(os.listdir(dirpath)):
                filepath = os.path.join(dirpath, filename)
                f = open(filepath)
                self.process_file(f)
                self.after_file_hook()
            self.after_dir_hook()
        self.finish()
        
    def process_file(self, f_handle):
        pass

    def after_file_hook(self):
        pass

    def after_dir_hook(self):
        pass

    def finish(self):
        pass
