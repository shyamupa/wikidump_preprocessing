Wikipedia Dump Processing
------------
Script for processing wikipedia dumps (in any language) and extracting useful metadata (inter-language links, how often a string refers to a wikipage etc.) from it.

Install the requirements, modify the makefile appropriately, and run. 

Description
------------
This repository contains scripts to perform the following preprocessing steps.

1. Download the relevant files from the wikipedia dump (target `dumps` in `makefile`). Specifically, it downloads

````
*-pages-articles.xml.bz2
*-page.sql.gz
*-pagelinks.sql.gz
*-redirect.sql.gz
*-categorylinks.sql.gz
*-langlinks.sql.gz
````

2. Extract text with hyperlinks from the \*pages-articles.xml.bz2 file (target `text` in `makefile`), using the [wikiextractor](https://github.com/attardi/wikiextractor).

### Wikipedia Page ID to Page Title Map
Creates Wikipedia page id to page title map using \*page.sql.gz (target `id2title` in `makefile`). The result is saved in ${OUTDIR}/${lang}wiki/idmap/${lang}wiki-data.id2t

Every Wikipedia page is associated with a unique page id. 
For instance, the page [Barack_Obama](https://en.wikipedia.org/wiki/Barack_Obama) in the English Wikipedia has the page id 534366. 
You can verify this by visiting https://en.wikipedia.org/?curid=534366 or visiting the page information link on the Tools panel on the left on the Wikipedia page. 
This page id serves as the canonical identifier of the page, and is used in other dump files (e.g., enwiki-\*-redirect.sql.gz etc.) to refer to the page. 

The output map is a tsv file that looks like this (example from Turkish wiki dump for 20181020):

10	Cengiz_Han	0
16	Film_(anlam_ayrımı)	0
22	Mustafa_Suphi	0
24	Linux	0
25	MHP	1

Each line represents an entry for one page, where the first field is the page id, the second field is the page title, and the third field is a boolean indicating whether the page is redirection.

### Wikipedia Page Redirects to Page Title Map
Redirects map using \*redirect.sql.gz (target `redirects` in `makefile`). 

Redirects tell you that the wikipedia link [POTUS44](https://en.wikipedia.org/wiki/POTUS44) redirects to the page [Barack_Obama](https://en.wikipedia.org/wiki/Barack_Obama) in the English Wikipedia.

5. Create a inter-language link mapping from Wikipedia titles to English Wikipedia titles using \*langlinks.sql.gz (target `langlinks` in `makefile`). Inter-language links indicate that the page [Barack_Obama](https://en.wikipedia.org/wiki/Barack_Obama) in English Wikipedia is for the same entity as the page [बराक_ओबामा](https://hi.wikipedia.org/wiki/%E0%A4%AC%E0%A4%B0%E0%A4%BE%E0%A4%95_%E0%A4%93%E0%A4%AC%E0%A4%BE%E0%A4%AE%E0%A4%BE) in Hindi Wikipedia.

6. Compute hyperlink counts (how many hyperlinks point to a certain title) for wikipedia titles (target `countsmap` in `makefile`). This is basically inlink counts for each title.

7. Compute probability indices using which we can compute the probability for a string (e.g., Berlin) referring a Wikipedia title (e.g., Berlin_(Band)) (target `probmap` in `makefile`).

Requirements
-----------------
You need python >=3.5. Also install the following two packages.

````python
pip3 install bs4
pip3 install hanziconv # (for chinese traditional to simplified conversion)
````

Running
-------
For ease of use, we provide a `makefile` that specifies targets to automatically run all processing scripts. To use the makefile, you need to

1. Download/Clone [wikiextractor](https://github.com/attardi/wikiextractor). Modify path `WIKIEXTRACTOR` in makefile to point to it.

2. Create a download directory for wikipedia dumps (say `/path/to/dumpdir`) and set `DUMPDIR` accordingly. The wikipedia dumps will be downloaded under `DUMPDIR` (for instance the Turkish Wikipedia dumps will be downloaded under `DUMPDIR/trwiki/`)

**For Cogcomp Internal Use**: 
Wikipedia dumps are already available under `/shared/corpora/wikipedia_dumps`, so simply set the `DUMPDIR` to `/shared/corpora/wikipedia_dumps`. For instance, the Turkish wikipedia resources are in `/shared/corpora/wikipedia_dumps/trwiki`.

3. Specify a `OUTDIR`. This is the directory where the resources will be generated (eg. `path/to/my/resources/trwiki` for Turkish Wikipedia). To keep the code generic, you may want to use the `lang` variable to define the `OUTDIR` (e.g., `path/to/my/resources/${lang}wiki`).

4. Modify the `DATE` variable to identify the timestamp of the Wikipedia dump to download. Make sure that this link works `https://dumps.wikimedia.org/${lang}wiki/${DATE}/`.

5. Make sure `PYTHONBIN` points to the correct python binary.

6. Run the command `lang=CODE make all`, where `CODE` is the two-letter language code used by Wikipedia to identify the language (eg. `tr` for Turkish, `es` for Spanish etc.). This should perform all the preprocessing steps above by following the build dependencies specified in the makefile.

Sanity Check
------

After `lang=CODE make all` completes successfully (takes ~18 mins on single-core machine for Turkish Wikipedia), you should have files with following line counts (for 20180720 dump of Turkish Wikipedia),

````
222367  idmap/fr2entitles   
559553  idmap/trwiki-20180720.id2t
247338  idmap/trwiki-20180720.r2t
559552  trwiki-20180720.counts
2941652 surface_links
936100  probmap/trwiki-20180720.p2t2prob
936100  probmap/trwiki-20180720.t2p2prob
1426771 probmap/trwiki-20180720.t2w2prob
745829  probmap/trwiki-20180720.tnr.p2t2prob
745829  probmap/trwiki-20180720.tnr.t2p2prob
1273216 probmap/trwiki-20180720.tnr.t2w2prob
1273216 probmap/trwiki-20180720.tnr.w2t2prob
1426771 probmap/trwiki-20180720.w2t2prob
````

Citation
------

If you use this code, please cite

```
@inproceedings{UGR18,
  author = {Upadhyay, Shyam and Gupta, Nitish and Roth, Dan},
  title = {Joint Multilingual Supervision for Cross-lingual Entity Linking},
  booktitle = {EMNLP},
  year = {2018}
}
```
