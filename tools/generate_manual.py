"""Build the embedded manual and its self-contained offline HTML from shared catalogs."""
import argparse
import copy
import html
import json
from pathlib import Path
import re
import shutil
import textwrap
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {"chat": ROOT / "assets/screenshots/chat-preview.png", "connection": ROOT / "assets/screenshots/connection-preview.png"}
TYPES = {"paragraph", "heading", "note", "code", "example", "steps", "bullets", "flow", "image", "table", "related"}
def fold(text):
    return "".join(c for c in unicodedata.normalize("NFD", text).lower() if not unicodedata.combining(c))
def load_books(root=ROOT):
    books = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((root / "docs/manual").glob("*.json"))]
    if not books or not any(b.get("code") == "en" for b in books):
        raise ValueError("An English manual is required")
    canonical = next(b for b in books if b["code"] == "en")
    canonical_shape = [(c["id"], [b["type"] for b in c["blocks"]]) for c in canonical["chapters"]]
    codes = set()
    for book in books:
        code = book["code"]
        if not re.fullmatch("[a-z]{2}(?:-[a-z0-9]+)?", code) or code in codes:
            raise ValueError("Invalid or duplicate manual language")
        codes.add(code)
        if book.get("schema") != 1 or not book.get("name") or set(book["ui"]) != set(canonical["ui"]):
            raise ValueError("Invalid manual metadata or UI catalog")
        if not all(isinstance(v, str) and v.strip() for v in book["ui"].values()):
            raise ValueError("Missing manual UI translation")
        if [(c["id"], [b["type"] for b in c["blocks"]]) for c in book["chapters"]] != canonical_shape:
            raise ValueError("Manual chapters or blocks differ between languages")
        ids = [c["id"] for c in book["chapters"]]
        if len(ids) != len(set(ids)) or not all(re.fullmatch("[a-z][a-z0-9-]*", i) for i in ids):
            raise ValueError("Invalid or duplicate chapter IDs")
        for chapter in book["chapters"]:
            if not chapter["title"].strip() or not chapter["blocks"]:
                raise ValueError("Empty manual chapter")
            for block in chapter["blocks"]:
                kind = block["type"]
                if kind not in TYPES:
                    raise ValueError("Unknown manual block")
                if kind in {"paragraph", "heading", "note", "code", "example"} and not block.get("text", "").strip():
                    raise ValueError("Empty manual block")
                if kind in {"steps", "bullets", "flow"}:
                    if not block.get("items") or not all(isinstance(t, str) and t.strip() for t in block["items"]):
                        raise ValueError("Empty manual list or diagram")
                if kind == "image" and (block.get("asset") not in ASSETS or not block.get("caption")):
                    raise ValueError("Unknown manual illustration")
                if kind == "table" and (not block["headers"] or not block["rows"] or any(len(r) != len(block["headers"]) for r in block["rows"])):
                    raise ValueError("Invalid manual table")
                if kind == "related" and not all(target in ids for target in block["chapters"]):
                    raise ValueError("Broken manual chapter link")
    return books

CSS = """
:root{color-scheme:dark;--bg:#101719;--panel:#172226;--ink:#eaf4f3;--muted:#adbfbe;--accent:#40d6c9;--line:#304349}
*{box-sizing:border-box}html{scroll-padding-top:24px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,"Segoe UI",sans-serif}a{color:var(--accent)}button,input{font:inherit}button{cursor:pointer}button,input{border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);padding:9px 13px}input{width:100%}input:focus,a:focus,button:focus{outline:2px solid var(--accent);outline-offset:3px}[hidden]{display:none!important}
.layout{display:grid;grid-template-columns:270px minmax(0,1fr);max-width:1480px;margin:auto}aside{position:sticky;top:0;height:100vh;padding:24px 20px;background:var(--panel);overflow:auto;border-right:1px solid var(--line)}.brand{display:flex;align-items:center;gap:12px;font-weight:700;line-height:1.25}.brand img{width:44px;height:44px}.languages{margin:20px 0 12px;display:flex;gap:16px}.search{display:block;margin:14px 0 4px}.hint,figcaption,footer,.muted{color:var(--muted);font-size:.9rem}nav ol{padding-left:22px}nav li{margin:9px 0}nav a{text-decoration:none}nav a:hover{text-decoration:underline}main{padding:40px clamp(22px,5vw,75px);min-width:0}header{margin-bottom:38px;border-bottom:1px solid var(--line);padding-bottom:26px}.eyebrow{color:var(--accent);font-weight:650;letter-spacing:.04em}h1{font-size:clamp(2rem,4vw,3rem);line-height:1.18;margin:12px 0}h2{font-size:1.65rem;line-height:1.3;margin-top:0}h3{font-size:1.15rem;margin-top:25px}section{margin:0 0 48px;padding:30px 0 0;border-top:1px solid var(--line)}p{margin:14px 0}li{margin:8px 0}figure{margin:24px 0}figure img{display:block;max-width:100%;height:auto;border:1px solid var(--line);border-radius:10px;background:#171e20}figcaption{margin-top:9px}.diagram img{width:640px}.note{border-left:4px solid var(--accent);padding:14px 18px;background:var(--panel);border-radius:0 8px 8px 0}.code{position:relative}pre{padding:20px;border:1px solid var(--line);border-radius:10px;overflow-x:auto;background:#0b1114;line-height:1.6}code{font:14px/1.6 Consolas,monospace;white-space:pre}.copy{margin-top:0;font-size:.85rem}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;margin:18px 0;font-size:.94rem}th,td{border:1px solid var(--line);padding:12px 14px;text-align:left;vertical-align:top}th{background:var(--panel)}td:first-child{font-weight:600;min-width:145px}.related{display:flex;flex-wrap:wrap;gap:8px;margin-top:24px}.related a{padding:5px 12px;background:var(--panel);border-radius:6px;text-decoration:none}footer{padding-top:28px;border-top:1px solid var(--line)}.empty{border:1px solid var(--line);padding:20px;border-radius:10px}
@media(max-width:850px){.layout{display:block}aside{position:relative;height:auto;border-right:0;border-bottom:1px solid var(--line)}nav ol{columns:2;font-size:.9rem}.brand img{width:36px;height:36px}main{padding-top:28px}td:first-child{min-width:120px}}
@media(max-width:480px){nav ol{columns:1}main{padding:24px 16px}pre{padding:12px}table{font-size:.85rem}th,td{padding:8px}}
@media print{:root{color-scheme:light;--bg:#fff;--panel:#f2f5f5;--ink:#121719;--muted:#404f52;--accent:#086b63;--line:#b7c5c7}body{font-size:11pt}.layout{display:block;max-width:none}aside,.no-print,.copy,.related{display:none!important}main{padding:0}section{break-before:auto;display:block!important}figure,.note,tr{break-inside:avoid}img{max-height:650px;object-fit:contain}pre{white-space:pre-wrap;background:#f4f6f6}code{white-space:pre-wrap}a{color:#086b63;text-decoration:none}.empty{display:none}}
"""
JS = """
const query=document.getElementById('search');
const fold=t=>t.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase();
const sections=[...document.querySelectorAll('main section')];
const links=[...document.querySelectorAll('nav a')];
function filter(){
 const q=fold(query.value.trim());let shown=0;
 for(const section of sections){section.hidden=!fold(section.textContent).includes(q);if(!section.hidden)shown++;}
 for(const link of links)link.parentElement.hidden=document.getElementById(link.hash.slice(1)).hidden;
 document.getElementById('empty').hidden=shown!==0;
}
query.addEventListener('input',filter);
const initial=new URLSearchParams(location.search).get('q');if(initial){query.value=initial.slice(0,255);filter();}
document.addEventListener('click',async event=>{
 const language=event.target.closest('a[lang]');if(language){language.href=language.getAttribute('href').split('#')[0]+location.hash;return;}
 const copy=event.target.closest('button[data-copy]');
 if(copy){const text=document.getElementById(copy.dataset.copy).textContent;try{await navigator.clipboard.writeText(text);}catch{const range=document.createRange();range.selectNodeContents(document.getElementById(copy.dataset.copy));const sel=getSelection();sel.removeAllRanges();sel.addRange(range);document.execCommand('copy');}return;}
 const link=event.target.closest('a[href^="#"]');
 if(link){const target=document.getElementById(link.hash.slice(1));if(target?.hidden){query.value='';filter();}}
});
document.getElementById('print').addEventListener('click',()=>window.print());
window.addEventListener('beforeprint',()=>{for(const s of sections)s.hidden=false;});
window.addEventListener('afterprint',filter);
"""
def svg_flow(block):
    labels = block["items"]
    height = len(labels)*100 + 30
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="{height}" viewBox="0 0 640 {height}" role="img" aria-label="{html.escape(block["title"], quote=True)}">',
             '<rect width="100%" height="100%" fill="#101719"/>']
    for index, label in enumerate(labels):
        y = index*100 + 14
        parts.append(f'<rect x="20" y="{y}" width="600" height="72" rx="12" fill="#172c31" stroke="#40d6c9" stroke-width="2"/>')
        wrapped=textwrap.wrap(label, width=52, break_long_words=False)
        first=y+42-(len(wrapped)-1)*11
        for line_index,line in enumerate(wrapped):
            parts.append(f'<text x="320" y="{first+line_index*22}" text-anchor="middle" fill="#eaf4f3" font-family="Segoe UI, sans-serif" font-size="18">{html.escape(line)}</text>')
        if index+1<len(labels) and block.get("layout") != "choices":
            parts.append(f'<path d="M320 {y+74} v20 m-7 -7 7 7 7 -7" fill="none" stroke="#40d6c9" stroke-width="2"/>')
    return "".join(parts)+"</svg>"

def build_html(book, books, output, version):
    escape = html.escape
    ids={c["id"]:c["title"] for c in book["chapters"]}
    ui=book["ui"];body=[]
    for chapter in book["chapters"]:
        blocks=[f'<section id="{chapter["id"]}"><h2>{escape(chapter["title"])}</h2>']
        for index,block in enumerate(chapter["blocks"]):
            kind=block["type"]
            if kind=="paragraph": blocks.append("<p>"+escape(block["text"])+"</p>")
            elif kind=="heading": blocks.append("<h3>"+escape(block["text"])+"</h3>")
            elif kind=="note": blocks.append('<p class="note">'+escape(block["text"])+"</p>")
            elif kind in {"steps","bullets"}:
                tag="ol" if kind=="steps" else "ul"
                blocks.append(f"<{tag}>"+ "".join("<li>"+escape(t)+"</li>" for t in block["items"])+f"</{tag}>")
            elif kind in {"code","example"}:
                identifier=f'code-{chapter["id"]}-{index}'
                blocks.append(f'<div class="code"><pre><code id="{identifier}">{escape(block["text"])}</code></pre><button class="copy" data-copy="{identifier}">{escape(ui["copy"])}</button></div>')
            elif kind=="image":
                path=f'assets/{block["asset"]}.png'
                blocks.append(f'<figure><a href="{path}" target="_blank" rel="noopener"><img src="{path}" alt="{escape(block["caption"],quote=True)}" loading="lazy"></a><figcaption>{escape(block["caption"])}</figcaption></figure>')
            elif kind=="flow":
                name=f'flow-{book["code"]}-{chapter["id"]}-{index}.svg'
                (output/"assets"/name).write_text(svg_flow(block),encoding="utf-8")
                blocks.append(f'<figure class="diagram"><a href="assets/{name}" target="_blank" rel="noopener"><img src="assets/{name}" alt="{escape(block["title"]+": "+" → ".join(block["items"]),quote=True)}" loading="lazy"></a><figcaption>{escape(ui["diagram"]+": "+block["title"])}</figcaption></figure>')
            elif kind=="table":
                blocks.append('<div class="table-wrap"><table><thead><tr>'+"".join("<th>"+escape(t)+"</th>" for t in block["headers"])+"</tr></thead><tbody>"+
                    "".join("<tr>"+"".join("<td>"+escape(t)+"</td>" for t in row)+"</tr>" for row in block["rows"])+"</tbody></table></div>")
            elif kind=="related":
                blocks.append('<div class="related">'+"".join(f'<a href="#{i}">{escape(ids[i])}</a>' for i in block["chapters"])+"</div>")
        body.append("".join(blocks)+"</section>")
    languages="".join(f'<a href="index.{b["code"]}.html" lang="{b["code"]}">{escape(b["name"])}</a>' for b in books)
    navigation="".join(f'<li><a href="#{i}">{escape(t)}</a></li>' for i,t in ids.items())
    result=f'''<!doctype html>
<html lang="{book["code"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(ui["title"])}</title><style>{CSS}</style></head>
<body><div class="layout"><aside><div class="brand"><img src="assets/logo.png" alt=""><span>CyRSAssistant<br><small>{escape(version)}</small></span></div><div class="languages">{languages}</div><label class="search" for="search">{escape(ui["search"])}</label><input type="search" id="search" maxlength="255" aria-describedby="search-hint"><p class="hint" id="search-hint">{escape(ui["search_hint"])}</p><h2 id="contents">{escape(ui["contents"])}</h2><nav aria-label="{escape(ui["contents"])}"><ol>{navigation}</ol></nav></aside>
<main><header><div class="eyebrow">CyRSAssistant</div><h1>{escape(ui["title"])}</h1><p>{escape(ui["subtitle"])}</p><p class="muted">{escape(ui["version"].format(version=version))}</p><button id="print" class="no-print">{escape(ui["print"])}</button></header><p class="empty" id="empty" hidden>{escape(ui["empty"])}</p>{"".join(body)}<footer>CyRSAssistant · Cyberalien · {escape(version)}</footer></main></div><script>{JS}</script></body></html>'''
    (output/f'index.{book["code"]}.html').write_text(result,encoding="utf-8",newline="\n")
    return result

def generate(header=None, output=None, root=ROOT):
    books=load_books(root)
    if header:
        lines=['// Generated from docs/manual/*.json. Do not edit.','#pragma once','#include <cstddef>','namespace cyrs::manual_data {',
               'struct Document { const char *code; const char *const *chunks; size_t count; };']
        for index,book in enumerate(books):
            encoded=json.dumps(book,ensure_ascii=False,separators=(",",":"))
            lines.append(f'inline constexpr const char *document_{index}[] = {{')
            for offset in range(0,len(encoded),4096):
                lines.append("    "+json.dumps(encoded[offset:offset+4096],ensure_ascii=False)+",")
            lines.append("};")
        lines.append("inline constexpr Document documents[] = {")
        for index,book in enumerate(books):
            lines.append('    {"'+book["code"]+'", document_'+str(index)+', sizeof(document_'+str(index)+') / sizeof(const char *)},')
        lines.extend(["};","}",""])
        header.parent.mkdir(parents=True,exist_ok=True);header.write_text("\n".join(lines),encoding="utf-8")
    if output:
        output.mkdir(parents=True,exist_ok=True);(output/"assets").mkdir(exist_ok=True)
        version=re.search(r"project\(CyRSAssistant VERSION ([0-9.]+)",(root/"CMakeLists.txt").read_text(encoding="utf-8-sig")).group(1)
        for key,source in ASSETS.items(): shutil.copyfile(root / source.relative_to(ROOT),output/"assets"/(key+".png"))
        shutil.copyfile(root/"assets/cyrsassistant-logo-turquoise.png",output/"assets/logo.png")
        for book in books:
            content=build_html(book,books,output,version)
            if book["code"]=="en":(output/"index.html").write_text(content,encoding="utf-8",newline="\n")
    return books

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--header",type=Path);parser.add_argument("--html",type=Path)
    args=parser.parse_args()
    generate(args.header,args.html)
