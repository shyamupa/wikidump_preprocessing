import os
import logging

"""
Helper function to recursively remove .DS_Store file in directories
"""
def remove_file(dir, name):
    l = os.listdir(dir)
    for entry in l:
        file_name = dir + os.path.sep + entry
        if os.path.isdir(file_name):
            remove_file(file_name, name)
        else:
            if os.path.isfile(file_name) and entry == name:
                print ('removed ' + file_name)
                os.remove(file_name)


class AbstractProcessor(object):
    def __init__(self, wikipath):
        self.wikipath = wikipath

    def setup(self):
        pass

    def run(self):
        # Recursively clean .DS_Store files
        remove_file(self.wikipath, '.DS_Store')
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

