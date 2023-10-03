from io import BytesIO, StringIO
import re
import subprocess
from bs4 import BeautifulSoup
import lxml
from typing import Union
from pathlib import Path
from tempfile import NamedTemporaryFile
import lxml.etree as et
import html2markdown

PREPROCESS_XSLT = """
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- Identity template: it copies everything as is -->
    <xsl:template match="node()|@*">
        <xsl:copy>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="pre">
        <p>
            <xsl:copy>
                <xsl:apply-templates select="node()|@*"/>
            </xsl:copy>
        </p>
    </xsl:template>

</xsl:stylesheet>
""".strip()

class ConversionError(Exception):
    ...

class XSLTError(Exception):
    ...

def sanitize_html(html: str) -> str:
    # Replace spooky newlines
    html = html.strip().replace("\r", "")
    html = re.sub("<script>.+?</script>", "", html, flags=re.DOTALL)
    soup = BeautifulSoup(html, features="html5lib")
    # Replace empty elements with br tags
    for e in soup.find_all():
        if len(e.get_text(strip=True)) == 0:     
            e.replaceWith("<br>")
    html = soup.prettify(formatter=lambda string: string)
    return html

def markdown2html(text: str) -> str:
    with NamedTemporaryFile("w", suffix=".md") as in_file:
        with NamedTemporaryFile("r", suffix=".html") as out_file:
            in_file.write(text)
            in_file.seek(0)
            try:
                _ = subprocess.run([
                    "md-to-html",
                    "--input",
                    in_file.name,
                    "--output",
                    out_file.name
                    ],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                raise ConversionError(e.stderr.decode("utf-8"))
            html = out_file.read()
    return html

def md2html(markdown: str) -> str:
    with NamedTemporaryFile("w", suffix=".md") as in_file:
        with NamedTemporaryFile("r", suffix=".html") as out_file:
            in_file.write(markdown)
            in_file.seek(0)
            try:
                _ = subprocess.run([
                    "pandoc",
                    "-i",
                    in_file.name,
                    "-o",
                    out_file.name
                    ],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                raise ConversionError(e.stderr.decode("utf-8"))
            html = out_file.read()
    return html

# def preprocess_html(html: str) -> str:
#     # Insert div to make paragraphs explicit
#     html = sanitize_html(html)    
    
#     paragraphs = []
#     for p in re.split(r"\n{2,}", html.strip()):
#         if not "".join(p.split()):
#             continue
#         if p.strip() == "<pre>" or p == "</pre>".strip():
#             paragraphs.append(p)
            
#         else:
#             paragraphs.append(f"<p>{p}<p>")
#     html = "\n\n".join(paragraphs)
    
#     # html = html.replace("<pre>", "")
#     # html = html.replace("</pre>", "")
#     # html = html.replace("<html>", "")
#     # html = html.replace("</html>", "")
#     # html = html.replace("<head>", "")
#     # html = html.replace("/head>", "")
#     # html = html.replace("<body>", "")
#     # html = html.replace("</body>", "")
    
#     # try:
#     #     transform = et.XSLT(et.parse(BytesIO(PREPROCESS_XSLT.encode("utf-8"))))
#     #     tree = et.parse(StringIO(html), parser=et.HTMLParser(recover=True))
#     #     transformed_tree = transform(tree)
#     #     html = et.tostring(transformed_tree).decode("utf-8")
#     # except Exception as e:
#     #     raise XSLTError(e)
#     # html = markdown2html(html)
#     return html

def preprocess_html(html: str) -> str:
    html = re.sub("<script>.+</script>", "", html, flags=re.DOTALL)
    html = sanitize_html(html)
    paragraphs = []
    for p in re.split(r"\n{2,}", html.strip()):
        if not "".join(p.split()):
            continue
        if p.strip() == "<pre>" or p == "</pre>".strip():
            paragraphs.append(p)
            
        else:
            paragraphs.append(f"<p>{p}<p>")
    html = "\n\n".join(paragraphs)
    markdown = html2markdown.convert(html)
    html = md2html(markdown)
    return html

def convert(html: str, out_file: Union[str, Path]) -> None:
    out_file = Path(out_file)
    if out_file.suffix != ".epub":
        out_file.rename(out_file.with_suffix(".epub"))

    with NamedTemporaryFile("w", suffix=".html") as src_file:
        src_file.write(html)
        src_file.seek(0)
        try:
            _ = subprocess.run([
                "ebook-convert",
                src_file.name,
                out_file.absolute()
                ],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise ConversionError(e.stderr.decode("utf-8"))

if __name__ == "__main__":
    import json
    from tqdm.auto import tqdm
    import logging
    logger = logging.getLogger()
    
    EPUB_DIR = Path("epub")
    EPUB_DIR.mkdir(exist_ok=True)
    
    HTML_DIR = Path("html")
    HTML_DIR.mkdir(exist_ok=True)
    
    data = [
        json.loads(line)
        for line in Path("data_html.jsonl").read_text().split("\n")
        if line.strip()
    ]
    pbar = tqdm(list(sorted(data, key=lambda s: s.get("title"))))
    for script in pbar:
        title = " ".join(script["title"].split())
        html = script["script"]
        (HTML_DIR / f"BEFORE_{title}.html").write_text(html)
        pbar.set_description(f"Processing {title}")
        try:
            preprocessed_html = preprocess_html(html=html)
            (HTML_DIR / f"{title}.html").write_text(preprocessed_html)
            
            convert(preprocessed_html, out_file=EPUB_DIR / f"{title}.epub")
        except Exception as e:
            logger.exception(e)
