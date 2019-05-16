COM_COLOR   = "\033[0;34m"
OBJ_COLOR   = "\033[0;36m"
OK_COLOR    = "\033[0;32m"
ERROR_COLOR = "\033[0;31m"
WARN_COLOR  = "\033[0;33m"
NO_COLOR    = "\033[m"

OK_STRING    = "[OK]"
ERROR_STRING = "[ERROR]"
WARN_STRING  = "[WARNING]"
COM_STRING   = "Compiling"

DATE=20190420
lang=tr
window=20
# location where dumps are downloaded
DUMPDIR = "/Users/nicolette/Documents/nlp-wiki/dumpdir"

# good practice to make this different from the dumpdir, to separate
# resources from processed output
OUTDIR = "/Users/nicolette/Documents/nlp-wiki/outdir"
WIKIEXTRACTOR = "/Users/nicolette/Documents/nlp-wiki/wikiextractor/WikiExtractor.py"
ENCODING = utf-8
# path to python3 binary
PYTHONBIN = /Users/nicolette/anaconda2/envs/py3/bin/python
dumps:
	@if [ -f "${DUMPDIR}/${lang}wiki/${lang}wiki-${DATE}-pages-articles.xml.bz2" ]; then \
	echo $(ERROR_COLOR) "dump exists in ${DUMPDIR}!" $(NO_COLOR); \
	else echo $(OK_COLOR) "getting dumps" $(NO_COLOR); \
	./scripts/download_dump.sh ${lang} ${DATE} ${DUMPDIR}; \
	fi
softlinks:
	@mkdir -p ${OUTDIR}; \
	echo $(OK_COLOR) "making softlinks into output folder ${OUTDIR}" $(NO_COLOR); \
	./scripts/make_softlinks.sh ${lang} ${DATE} ${DUMPDIR} ${OUTDIR};

text: dumps
	@if [ -d "${OUTDIR}/${lang}wiki_with_links" ]; then \
	echo $(ERROR_COLOR) "text already extracted!" $(NO_COLOR); \
	else echo $(OK_COLOR) "extracting text to ${OUTDIR}/${lang}wiki_with_links" $(NO_COLOR); \
	${WIKIEXTRACTOR} \
	-o ${OUTDIR}/${lang}wiki_with_links \
	-l -q --filter_disambig_pages \
	${DUMPDIR}/${lang}wiki/${lang}wiki-${DATE}-pages-articles.xml.bz2; \
	fi
id2title: dumps softlinks
	@if [ -f "${OUTDIR}/idmap/${lang}wiki-${DATE}.id2t" ]; then \
	echo $(ERROR_COLOR) "id2title exists!" $(NO_COLOR); \
	else echo $(OK_COLOR) "making id2title" $(NO_COLOR); \
	mkdir -p "${OUTDIR}/idmap/"; \
	${PYTHONBIN} -m dp.create_id2title \
	--wiki ${OUTDIR}/${lang}wiki-${DATE} \
	--out ${OUTDIR}/idmap/${lang}wiki-${DATE}.id2t; \
	fi
redirects: dumps softlinks id2title
	@if [ -e "${OUTDIR}/idmap/${lang}wiki-${DATE}.r2t" ]; then \
	echo $(ERROR_COLOR) "redirects exists!" $(NO_COLOR); \
	else echo $(OK_COLOR) "making redirects" $(NO_COLOR); \
	${PYTHONBIN} -m dp.create_redirect2title \
	--id2t ${OUTDIR}/idmap/${lang}wiki-${DATE}.id2t \
	--wiki ${OUTDIR}/${lang}wiki-${DATE} \
	--out ${OUTDIR}/idmap/${lang}wiki-${DATE}.r2t; \
	fi
hyperlinks: text id2title redirects
	@if [ -d "${OUTDIR}/${lang}link_in_pages" ]; then \
	echo ${ERROR_COLOR} "hyperlink already extracted!" ${NO_COLOR} ; \
	else echo $(OK_COLOR) "extracting links to ${OUTDIR}/${lang}link_in_pages" $(NO_COLOR); \
	mkdir -p ${OUTDIR}/${lang}link_in_pages; \
	${PYTHONBIN} -m dp.extract_link_from_pages --dump ${OUTDIR}/${lang}wiki_with_links/ \
	--out ${OUTDIR}/${lang}link_in_pages \
	--lang ${lang} \
	--id2t ${OUTDIR}/idmap/${lang}wiki-${DATE}.id2t \
	--redirects ${OUTDIR}/idmap/${lang}wiki-${DATE}.r2t; \
	fi
mid: hyperlinks
	@if [ -d "${OUTDIR}/${lang}mid" ]; then \
	echo $(ERROR_COLOR) "training files already there" $(NO_COLOR); \
	else echo $(OK_COLOR) "extracting training files to $(OUTDIR)/${lang}mid" $(NO_COLOR); \
	mkdir -p $(OUTDIR)/${lang}mid; \
	${PYTHONBIN} -m dp.create_mid --dump ${OUTDIR}/${lang}link_in_pages \
		--out ${OUTDIR}/${lang}mid \
		--lang ${lang} \
		--id2t ${OUTDIR}/idmap/${lang}wiki-${DATE}.id2t \
		--redirects ${OUTDIR}/idmap/${lang}wiki-${DATE}.r2t \
		--window ${window} ; \
	fi
langlinks: dumps id2title redirects
	@if [ -f "${OUTDIR}/idmap/fr2entitles" ]; then \
	echo $(ERROR_COLOR) "fr2entitle exists!" $(NO_COLOR); \
	else echo $(OK_COLOR) "making fr2entitle" $(NO_COLOR); \
	${PYTHONBIN} -m dp.langlinks \
	--langlinks ${DUMPDIR}/${lang}wiki/${lang}wiki-${DATE}-langlinks.sql.gz \
	--frid2t ${OUTDIR}/idmap/${lang}wiki-${DATE}.id2t \
	--out ${OUTDIR}/idmap/fr2entitles; \
	fi
countsmap: id2title redirects text
	@if [ -e "${OUTDIR}/${lang}wiki-${DATE}.counts" ]; then \
	echo $(ERROR_COLOR) "countsmap exists!" $(NO_COLOR); \
	else echo $(OK_COLOR) "making surface to title map and title counts" $(NO_COLOR); \
	${PYTHONBIN} -m dp.count_popular_entities_v2 \
	--wikitext ${OUTDIR}/${lang}wiki_with_links \
	--id2title ${OUTDIR}/idmap/${lang}wiki-${DATE}.id2t \
	--redirects ${OUTDIR}/idmap/${lang}wiki-${DATE}.r2t \
	--contsout ${OUTDIR}/${lang}wiki-${DATE}.counts \
	--linksout ${OUTDIR}/surface_links; \
	fi
probmap: id2title redirects countsmap langlinks
	@if [ -e "${OUTDIR}/probmap/${lang}wiki-${DATE}.p2t2prob" ]; then \
	echo "probmap phrase exists!"; \
	else echo "computing phrase probmap"; \
	mkdir -p "${OUTDIR}/probmap"; \
	${PYTHONBIN} -m dp.compute_probs2 \
	--links ${OUTDIR}/surface_links \
	--id2t ${OUTDIR}/idmap/${lang}wiki-${DATE}.id2t \
	--redirects ${OUTDIR}/idmap/${lang}wiki-${DATE}.r2t \
	--mode phrase \
	--out_prefix ${OUTDIR}/probmap/${lang}wiki-${DATE} \
	--lang ${lang}; \
	fi; \
	if [ -e "${OUTDIR}/probmap/${lang}wiki-${DATE}.w2t2prob" ]; then \
	echo "probmap word exists!"; \
	else echo "computing word probmap"; \
	${PYTHONBIN} -m dp.compute_probs2 \
	--links ${OUTDIR}/surface_links \
	--id2t ${OUTDIR}/idmap/${lang}wiki-${DATE}.id2t \
	--redirects ${OUTDIR}/idmap/${lang}wiki-${DATE}.r2t \
	--mode word \
	--out_prefix ${OUTDIR}/probmap/${lang}wiki-${DATE} \
	--lang ${lang}; \
	fi	
all:	dumps softlinks text id2title redirects hyperlinks langlinks countsmap probmap
	echo "all done"
