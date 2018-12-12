#!/usr/bin/env bash

if [ "$#" -ne 3 ]; then 	# number of args
    echo "USAGE: script.sh lang date dumpdir"
    echo "$ME"
    exit
fi

lang=$1
date=$2
DUMPDIR=$3
url=https://dumps.wikimedia.org/${lang}wiki/${date}/${lang}wiki-${date}
echo "Downloading relevant dump files from ${url}"
wget -nc ${url}-pages-articles.xml.bz2 \
     ${url}-page.sql.gz \
     ${url}-pagelinks.sql.gz \
     ${url}-redirect.sql.gz \
     ${url}-categorylinks.sql.gz \
     ${url}-langlinks.sql.gz \
     -P ${DUMPDIR}/${lang}wiki/
