---
license: mit
---
## IMSDb to EPub

Scrape and convert movie scripts from https://imsdb.com to EPub files.

The scraping is adapted from https://huggingface.co/datasets/mattismegevand/IMSDb/tree/main.

The EPub creation is largely done via `calibre's` `ebook-convert` CLI-tool, so make sure to have `calibre` installed and linked against your shell.

### WIP

The conversion script was sketched together in roughly 30 minutes...

Hence, the quality of the resulting EPubs varies drastically ranging from perfectly enjoyable over somewhat readable to being utter junk.

A notable portion of the scripts entirely fails to build.

### Usage

First, install the (few) Python requirements with:

```shell
pip install -r requirements.txt
```

Then, install calibre using your preferred way.

To scrape all movie scripts from the website, run the `scrape.py` script:

```shell
python scrape.py
```

This will create a `data_html.jsonl` file within the project's root.

To convert the scraped scripts to EPub files, run the `convert2epub.py` script afterwards:

```shell
python convert2epub.py
```

This script will create two new folders: 
1. `epub` contains the EPub files.
2. `html` contains the html files in two version (before and after preprocessing them for the conversion).

The HTML-files can be helpful, for manually sanity checking.

#### Adding movie posters as covers

By executing the `download_posters.py` script, available posters will be downloaded and saved in the `poster` directory.
The EPub-conversion checks automatically if this directory is available and will use the posters as book cover whenever possible.
