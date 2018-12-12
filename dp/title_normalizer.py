import sys
import logging

from utils.misc_utils import load_id2title, load_redirects
import utils.constants as K

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)
__author__ = 'Shyam'


class TitleNormalizer:
    def __init__(self, lang="en", redirect_map=None, t2id=None, id2t=None, redirect_set=None):
        if t2id is None:
            id2t, t2id, redirect_set = load_id2title('data/{}wiki/idmap/{}wiki-20170520.id2t'.format(lang,lang))
        if redirect_map is None:
            redirect_map = load_redirects('data/{}wiki/idmap/{}wiki-20170520.r2t'.format(lang,lang))
        self.null_counts = 0
        self.call_counts = 0
        self.lang = lang
        self.redirect_map = redirect_map
        self.title2id, self.id2title, self.redirect_set = t2id, id2t, redirect_set
        self.lower2upper = {title.lower():title for title in self.title2id}
        for redirect in self.redirect_map:
            self.lower2upper[redirect.lower()] = self.redirect_map[redirect]

    def normalize(self, title):
        """

        """
        # TODO disambiguation pages should ideally go to NULLTITLE
        self.call_counts += 1
        # Check this first, because now tid can contains tids for titles that are redirect pages.
        if title in self.redirect_map:
            return self.redirect_map[title]

        if title in self.title2id:
            return title

        title_tokens = title.split('_')
        title = "_".join([t.capitalize() for t in title_tokens])

        if title in self.redirect_map:
            return self.redirect_map[title]

        if title in self.title2id:
            return title

        self.null_counts += 1
        return K.NULL_TITLE

    def __del__(self):
        logging.info("dying ... title nrm saw %d/%d nulls/calls", self.null_counts, self.call_counts)

    def lower2upper(self,title):
        if title not in self.lower2upper:
            return K.NULL_TITLE
        return self.lower2upper[title]


"""
TODO
test for normalization
anna_Kurnikova
nasa
2_Ronnies
ActresseS
AN.O.VA.
annova
cyanide
"""

if __name__ == '__main__':
    title_normalizer = TitleNormalizer(lang=sys.argv[1])
    try:
        while True:
            surface = input("enter title:")
            nrm = title_normalizer.normalize(surface)
            logging.info("normalized title %s",nrm)
    except KeyboardInterrupt:
        print('interrupted!')
