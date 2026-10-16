import requests
from pathlib import Path
import quopri, re, textwrap
import os, sys, subprocess
import json

from parser import CcelTextExtractor

def get_filename(title, ext):
    return os.path.join("build", title.replace(" ", "_") + ext)
    

def get_text(title, link):
    filename = get_filename(title, ".html")
    file_path = Path(filename)

    if not file_path.is_file():
        out = requests.get(link, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })
        if not out.ok:
            print(out.text)
            exit(1)

        # 1. Use out.content (raw bytes) instead of out.text
        raw_bytes = out.content
        
        # 2. Decode the Quoted-Printable format directly from the raw bytes
        decoded_bytes = quopri.decodestring(raw_bytes)
        
        # 3. Correctly decode the result into UTF-8 text
        content = decoded_bytes.decode("utf-8", errors="ignore")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

    else:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

    return re.sub(r"=\r?\n", "", content) # Clean up soft line breaks (=\n)

    
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("missing input filename")
        exit(1)

    os.makedirs("build", exist_ok=True)

    with open(sys.argv[1], "r") as f:
        cfg = json.load(f)

    text = ""
        
    chapters = []
    for chapter in cfg["chapters"]:
        if "link" in chapter:
            decoded_html = get_text(chapter["title"], chapter["link"])
        else:
            decoded_html = get_text(cfg["title"], cfg["link"])

        if "content" in chapter: 
            content = chapter["content"]
        else:
            parser = CcelTextExtractor(**(cfg | chapter))
            parser.feed(decoded_html)
            content = parser.get_clean_text()

        if chapter.get("style", "") == "fullpage":
            chapters.append(textwrap.dedent(f"""
            \\def\\worktitle{{{chapter["title"]}}}
            \\def\\workauthor{{{chapter.get("author", cfg["author"])}}}
            \\fullpagechapter{{{chapter["title"]}}}{{{chapter.get("subtitle", "")}}}{{{chapter.get("author", "")}}}

            {{{content}}}
            """))
        else:
            chapters.append(textwrap.dedent(f"""
            \\def\\worktitle{{{chapter.get("header", chapter["title"])}}}
            \\def\\workauthor{{{chapter.get("author", cfg["author"])}}}
            \\chapter{{{chapter["title"]}}}
            
            """) + content)
    
    with open("template.tex", "r") as f:
        template = f.read()

    sources = list(set([l["link"] for l in [cfg, *cfg["chapters"]] if "link" in l]))

    text = (template. 
        replace("{{title}}", cfg["title"]).
        replace("{{author}}", cfg.get("author", "")).
        replace("{{translator}}", cfg["translator"]).
        replace("{{editor}}", str(cfg["editor"])).
        replace("{{year_published}}", str(cfg["year_published"])).
        replace("{{publisher_info}}", cfg["publisher_info"]).
        replace("{{margins}}", cfg["margins"]).
        replace("{{sources}}", " \\\\\n".join(sources)).
        replace("{{content}}", f"{{{"}\n{".join(chapters)}}}")
    )

    texfile = get_filename(cfg["title"], ".tex")
    with open(texfile, "w") as f:
        f.write(text)
        
    result = subprocess.run(
        ['xelatex', '-interaction=nonstopmode', os.path.basename(texfile)],
        capture_output=True,
        text=True,
        cwd="build"
    )

    # run it again for the table of contents to populate
    result = subprocess.run(
        ['xelatex', '-interaction=nonstopmode', os.path.basename(texfile)],
        capture_output=True,
        text=True,
        cwd="build"
    )
    

