#!/usr/bin/env bash

if [ "$#" -ne 4 ]; then 	# number of args
    echo "USAGE: script.sh lang date dumpdir outdir"
    echo "$ME"
    exit
fi

lang=$1
date=$2
DUMPDIR=$3
OUTDIR=$4
ln -fs ${DUMPDIR}/${lang}wiki/${lang}wiki-${date}-pages-articles.xml.bz2 ${OUTDIR}/
ln -fs ${DUMPDIR}/${lang}wiki/${lang}wiki-${date}-page.sql.gz ${OUTDIR}/
ln -fs ${DUMPDIR}/${lang}wiki/${lang}wiki-${date}-pagelinks.sql.gz ${OUTDIR}/
ln -fs ${DUMPDIR}/${lang}wiki/${lang}wiki-${date}-redirect.sql.gz ${OUTDIR}/
ln -fs ${DUMPDIR}/${lang}wiki/${lang}wiki-${date}-categorylinks.sql.gz ${OUTDIR}/
ln -fs ${DUMPDIR}/${lang}wiki/${lang}wiki-${date}-langlinks.sql.gz ${OUTDIR}/
