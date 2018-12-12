from __future__ import print_function
import argparse
import logging
import sys

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)
import gzip
from dp.create_redirect2title import load_id2title


def read_frid2en(filename, target_lang, encoding):
    """
    page id in fr wikipedia --> target_lang (usually en) wikipedia title
    """
    logging.info("Reading lang links %s", filename)
    id2en = {}
    all_lang_map = []
    if filename.endswith(".gz"):
        f = gzip.open(filename, "rt", encoding=encoding, errors="ignore")
    else:
        f = open(filename, "r", errors='ignore')
    for line in f:
        if "INSERT INTO" not in line:
            continue
        # (150055,'en','Idanha-a-Nova'),(5954745,'en','Idanre')
        start = line.index("(")
        line = line[start + 1:]
        parts = line.split("),(")
        # [ (150055,'en','Idanha-a-Nova' , 5954745,'en','Idanre')]
        for t in parts:
            ts = t.split(",'")
            # [(150055, en', Idanha-a-Nova']
            if len(ts) < 3: continue
            fr_page_id, lang, en_title = ts[0], ts[1], ts[2]
            lang = lang[:len(lang) - 1]  # strip the extra '
            en_title = en_title[:len(en_title) - 1]  # strip the extra '
            en_title = en_title.replace(" ", "_")
            if "\\" in en_title:
                en_title = en_title.replace("\\", "")
            # en_title = str(en_title,"utf-8")
            # en_title = en_title.encode(encoding).decode("utf-8")
            all_lang_map.append((fr_page_id, lang, en_title))
            if lang == target_lang:
                id2en[fr_page_id] = en_title
    return id2en, all_lang_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a page id to title map.')
    parser.add_argument('--langlinks', type=str, required=True, help='path to *-langlinks.sql.gz.')
    parser.add_argument('--frid2t', type=str, required=True, help='path to id 2 title map for fr.')
    # parser.add_argument('--encoding', type=str, required=True, help='utf-8 or ISO-8859-1.')
    parser.add_argument('--out', type=str, required=True, help='file to write fr title --> en title map.')
    parser.add_argument('--debug', action="store_true", help='tsv file to write the redirect-->title map in.')
    args = parser.parse_args()
    args = vars(args)

    langlinks_file = args["langlinks"]
    if "enwiki-" in langlinks_file:
        logging.info("not doing langlinks for english")
        sys.exit(0)
    frid2title_path = args["frid2t"]
    encoding = "utf-8"  # args["encoding"]
    try:
        frid2en, all_lang_map = read_frid2en(filename=langlinks_file, target_lang="en", encoding=encoding)
        with open(args["out"] + ".all_langs", "w") as out:
            for fr_page_id, lang, en_title in all_lang_map:
                if en_title.lower().startswith("user:") or en_title.lower().startswith(
                        "template:") or en_title.lower().startswith("wikipedia:") or en_title.lower().startswith(
                        "category:"):
                    continue
                buf = "%s\t%s\t%s\n" % (fr_page_id, lang, en_title)
                out.write(buf)

    except UnicodeDecodeError as e:
        print(str(e))
        print("ERROR:TRY ENCODING=ISO-8859-1")
        sys.exit(0)
    frid2t, frt2id, _ = load_id2title(frid2title_path)
    missed_pids = 0
    with open(args["out"], "w") as out:
        for pid in frid2en:
            en_title = frid2en[pid]
            if pid not in frid2t:
                missed_pids += 1
                if en_title.lower().startswith("user:") or en_title.lower().startswith(
                        "template:") or en_title.lower().startswith("wikipedia:") or en_title.lower().startswith(
                        "category:"):
                    pass
                else:
                    pass
                    # logging.info("#%d missed fr_id %s linking to en page %s",missed_pids, pid, en_title)
                continue
            fr_title = frid2t[pid]
            out.write(fr_title + "\t" + en_title + "\n")
