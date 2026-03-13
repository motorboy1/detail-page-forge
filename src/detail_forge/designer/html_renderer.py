"""HTML/CSS renderer — 4 distinct template sets based on D1000 principles.

Modes:
  standard  — warm professional (default red theme)
  dark      — luxury dark (#28 metallic, #50 blueprint)
  minimal   — extreme whitespace (#3 minimal)
  trendy    — gradient blobs + mixed fonts (#36 mesh, #33 stroke)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from detail_forge.copywriter.generator import SectionCopy
from detail_forge.designer.design_tokens import DesignTokenSet


@dataclass
class RenderedSection:
    section_index: int = 0
    section_type: str = ""
    html: str = ""
    css: str = ""
    copy: SectionCopy | None = None


@dataclass
class RenderedPage:
    sections: list[RenderedSection] = field(default_factory=list)
    global_css: str = ""

    def to_full_html(self, product_name: str = "") -> str:
        sec_html = "\n".join(s.html for s in self.sections)
        sec_css = "\n".join(s.css for s in self.sections)
        return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{product_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Playfair+Display:wght@400;700;900&family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
<style>{self.global_css}\n{sec_css}</style>
</head><body><div class="dp">{sec_html}</div></body></html>"""


def _detect_mode(p: set[int]) -> str:
    if 28 in p or (50 in p and 3 not in p):
        return "dark"
    if 3 in p and 28 not in p and 36 not in p:
        return "minimal"
    if 36 in p or (33 in p and 22 in p) or (38 in p and 29 in p):
        return "trendy"
    if 47 in p:
        return "vintage"
    return "standard"


def _bg(photos, idx=0, seed=200):
    if photos and idx < len(photos):
        return photos[idx]
    return f"https://picsum.photos/seed/{seed + idx * 41}/1200/600"


def _img(photos, idx=0, seed=100):
    if photos and idx < len(photos):
        return f'<img src="{photos[idx]}" alt="product" class="pi">'
    return f'<img src="https://picsum.photos/seed/{seed + idx * 37}/600/400" alt="product" class="pi">'


def _split_body(body, n=4):
    parts = [s.strip().rstrip('.') for s in body.replace('\u3002', '.').split('.') if len(s.strip()) > 5][:n]
    while len(parts) < max(n, 2):
        parts.append(body[:60] if body else "Premium")
    return parts


# ═══════════════════════════════════════════════════════════════
# HERO VARIANTS
# ═══════════════════════════════════════════════════════════════

def _hero_standard(c, name, photos, m):
    bg = _bg(photos, 0, 300)
    return f'''<section class="hero-s" style="background-image:url('{bg}')">
  <div class="hs-ov"></div>
  <div class="hs-in">
    <span class="hs-badge">{name}</span>
    <h1 class="hs-h1">{c.headline}</h1>
    <div class="hs-line"></div>
    <p class="hs-sub">{c.subheadline}</p>
    <p class="hs-body">{c.body}</p>
    {f'<a class="hs-cta" href="#">{c.cta_text}</a>' if c.cta_text else ''}
  </div>
</section>''', '''.hero-s { position:relative; min-height:540px; padding:0!important; background-size:cover; background-position:center; display:flex; align-items:center; }
.hs-ov { position:absolute; inset:0; background:linear-gradient(135deg,rgba(10,10,30,.85),rgba(15,52,96,.75)); }
.hs-in { position:relative; z-index:1; padding:80px 60px; max-width:560px; }
.hs-badge { display:inline-block; padding:6px 20px; border-radius:30px; font-size:11px; font-weight:700; letter-spacing:3px; text-transform:uppercase; background:rgba(231,76,60,.15); color:#e74c3c; border:1px solid rgba(231,76,60,.25); margin-bottom:24px; }
.hs-h1 { font-size:44px; font-weight:900; color:#fff; line-height:1.2; margin-bottom:20px; word-break:keep-all; text-shadow:0 2px 20px rgba(0,0,0,.3); }
.hs-line { width:60px; height:3px; background:linear-gradient(90deg,#e74c3c,#f39c12); margin-bottom:20px; border-radius:2px; }
.hs-sub { font-size:18px; color:rgba(255,255,255,.8); font-weight:300; line-height:1.6; margin-bottom:16px; }
.hs-body { font-size:14px; color:rgba(255,255,255,.45); line-height:1.9; margin-bottom:32px; }
.hs-cta { display:inline-block; background:linear-gradient(135deg,#e74c3c,#c0392b); color:#fff; padding:16px 44px; border-radius:50px; font-size:16px; font-weight:700; text-decoration:none; box-shadow:0 8px 24px rgba(231,76,60,.35); letter-spacing:1px; }
@media(max-width:600px){ .hs-in { padding:60px 24px; } .hs-h1 { font-size:32px; } }'''


def _hero_dark(c, name, photos, m):
    img = _img(photos, 0, 300)
    return f'''<section class="hero-d">
  <div class="hd-in">
    <div class="hd-label">{name}</div>
    <h1 class="hd-h1">{c.headline}</h1>
    <div class="hd-gold-line"></div>
    <p class="hd-sub">{c.subheadline}</p>
    <div class="hd-img-wrap">{img}</div>
    <p class="hd-body">{c.body}</p>
    {f'<a class="hd-cta" href="#">{c.cta_text}</a>' if c.cta_text else ''}
  </div>
</section>''', '''.hero-d { background:linear-gradient(180deg,#08080f 0%,#12121f 50%,#0a0a14 100%); padding:100px 40px!important; text-align:center; }
.hd-in { max-width:640px; margin:0 auto; }
.hd-label { font-size:11px; font-weight:700; letter-spacing:6px; text-transform:uppercase; color:#d4af37; margin-bottom:32px; }
.hd-h1 { font-size:52px; font-weight:900; line-height:1.1; margin-bottom:24px; word-break:keep-all; background:linear-gradient(135deg,#888,#f8f8f8,#aaa,#e8e8e8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hd-gold-line { width:80px; height:2px; background:linear-gradient(90deg,transparent,#d4af37,transparent); margin:0 auto 24px; }
.hd-sub { font-size:16px; color:rgba(255,255,255,.45); font-weight:300; margin-bottom:40px; letter-spacing:1px; }
.hd-img-wrap { margin:0 auto 40px; max-width:400px; }
.hd-img-wrap .pi { border-radius:12px; box-shadow:0 20px 60px rgba(0,0,0,.6); }
.hd-body { font-size:14px; color:rgba(255,255,255,.3); line-height:1.9; margin-bottom:40px; }
.hd-cta { display:inline-block; background:linear-gradient(135deg,#d4af37,#b8942a); color:#080808; padding:16px 48px; border-radius:4px; font-size:14px; font-weight:800; text-decoration:none; letter-spacing:3px; text-transform:uppercase; box-shadow:0 8px 32px rgba(212,175,55,.3); }
@media(max-width:600px){ .hd-h1 { font-size:36px; } }'''


def _hero_minimal(c, name, photos, m):
    return f'''<section class="hero-m">
  <div class="hm-in">
    <div class="hm-space"></div>
    <h1 class="hm-h1">{c.headline}</h1>
    <div class="hm-thin-line"></div>
    <p class="hm-sub">{c.subheadline}</p>
    <div class="hm-spacer"></div>
    {f'<a class="hm-cta" href="#">{c.cta_text}</a>' if c.cta_text else ''}
  </div>
</section>''', '''.hero-m { background:#fff; padding:0!important; min-height:600px; display:flex; align-items:center; }
.hm-in { width:100%; padding:120px 80px; }
.hm-space { height:60px; }
.hm-h1 { font-size:64px; font-weight:900; color:#111; line-height:1.08; margin-bottom:32px; word-break:keep-all; letter-spacing:-3px; }
.hm-thin-line { width:40px; height:1px; background:#111; margin-bottom:24px; }
.hm-sub { font-size:15px; color:#999; font-weight:300; line-height:1.8; max-width:380px; letter-spacing:.5px; }
.hm-spacer { height:48px; }
.hm-cta { display:inline-block; background:none; color:#111; padding:14px 0; font-size:13px; font-weight:700; text-decoration:none; letter-spacing:3px; text-transform:uppercase; border-bottom:2px solid #111; }
@media(max-width:600px){ .hm-in { padding:80px 28px; } .hm-h1 { font-size:40px; } }'''


def _hero_trendy(c, name, photos, m):
    return f'''<section class="hero-t">
  <div class="ht-blob ht-b1"></div>
  <div class="ht-blob ht-b2"></div>
  <div class="ht-blob ht-b3"></div>
  <div class="ht-blob ht-b4"></div>
  <div class="ht-star ht-s1">★</div>
  <div class="ht-star ht-s2">✦</div>
  <div class="ht-star ht-s3">★</div>
  <div class="ht-in">
    <p class="ht-over">{name} ®</p>
    <h1 class="ht-h1">{c.headline}</h1>
    <p class="ht-sub">{c.subheadline}</p>
    {f'<a class="ht-cta" href="#">{c.cta_text} →</a>' if c.cta_text else ''}
  </div>
</section>''', '''.hero-t { position:relative; background:#0a0a12; padding:120px 40px!important; text-align:center; overflow:hidden; min-height:560px; display:flex; align-items:center; justify-content:center; }
.ht-blob { position:absolute; border-radius:50%; filter:blur(60px); }
.ht-b1 { width:400px; height:400px; top:-100px; left:-80px; background:rgba(147,51,234,.35); }
.ht-b2 { width:350px; height:350px; bottom:-60px; right:-60px; background:rgba(59,130,246,.3); }
.ht-b3 { width:300px; height:300px; top:40%; left:50%; transform:translate(-50%,-50%); background:rgba(236,72,153,.2); }
.ht-b4 { width:200px; height:200px; top:20px; right:20%; background:rgba(16,185,129,.15); }
.ht-star { position:absolute; color:rgba(255,255,255,.08); z-index:1; }
.ht-s1 { font-size:48px; top:30px; right:40px; }
.ht-s2 { font-size:24px; bottom:50px; left:60px; }
.ht-s3 { font-size:32px; top:50%; right:15%; }
.ht-in { position:relative; z-index:2; max-width:700px; }
.ht-over { font-size:12px; font-weight:600; letter-spacing:5px; text-transform:uppercase; color:rgba(255,255,255,.35); margin-bottom:28px; font-family:'Space Grotesk',sans-serif; }
.ht-h1 { font-family:'Playfair Display',serif; font-size:72px; font-weight:900; line-height:1.05; margin-bottom:24px; word-break:keep-all; -webkit-text-stroke:2px rgba(255,255,255,.8); -webkit-text-fill-color:transparent; }
.ht-sub { font-size:16px; color:rgba(255,255,255,.4); font-weight:300; margin-bottom:48px; font-family:'Space Grotesk',sans-serif; }
.ht-cta { display:inline-block; background:linear-gradient(135deg,rgba(147,51,234,.8),rgba(59,130,246,.8)); color:#fff; padding:16px 40px; border-radius:50px; font-size:14px; font-weight:600; text-decoration:none; letter-spacing:1px; font-family:'Space Grotesk',sans-serif; box-shadow:0 8px 32px rgba(147,51,234,.3); }
@media(max-width:600px){ .ht-h1 { font-size:44px; -webkit-text-stroke:1.5px rgba(255,255,255,.8); } .ht-in { padding:0 12px; } }'''


# ═══════════════════════════════════════════════════════════════
# FEATURES VARIANTS
# ═══════════════════════════════════════════════════════════════

def _feat_standard(c, name, photos, m):
    parts = _split_body(c.body, 4)
    icons = ['✨', '✔️', '⚡', '⭐']
    colors = ['#e74c3c','#3498db','#27ae60','#9b59b6']
    cards = ""
    for j, part in enumerate(parts):
        col = colors[j%4]
        cards += f'<div class="fs-card"><div class="fs-icon" style="background:{col}12;border:2px solid {col}25"><span>{icons[j%4]}</span></div><h3 class="fs-num" style="color:{col}">0{j+1}</h3><p class="fs-txt">{part}</p></div>'
    return f'''<section class="feat-s"><div class="fs-in">
    <p class="fs-over">FEATURES</p><h2 class="fs-h2">{c.headline}</h2><p class="fs-sub">{c.subheadline}</p>
    <div class="fs-grid">{cards}</div></div></section>''', '''.feat-s { background:#fafafa; }
.fs-in { max-width:780px; margin:0 auto; }
.fs-over { font-size:11px; font-weight:700; letter-spacing:4px; color:#e74c3c; text-align:center; margin-bottom:10px; }
.fs-h2 { font-size:30px; font-weight:900; color:#111; text-align:center; margin-bottom:10px; word-break:keep-all; line-height:1.35; }
.fs-sub { font-size:15px; color:#999; text-align:center; margin-bottom:48px; }
.fs-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
.fs-card { background:#fff; border-radius:16px; padding:32px 24px; border:1px solid #f0f0f0; box-shadow:0 2px 8px rgba(0,0,0,.03); transition:all .3s; }
.fs-card:hover { transform:translateY(-4px); box-shadow:0 12px 32px rgba(0,0,0,.08); }
.fs-icon { width:56px; height:56px; border-radius:16px; display:flex; align-items:center; justify-content:center; margin-bottom:16px; font-size:24px; }
.fs-num { font-size:13px; font-weight:800; margin-bottom:8px; letter-spacing:1px; }
.fs-txt { font-size:14px; color:#666; line-height:1.8; word-break:keep-all; }
@media(max-width:600px){ .fs-grid { grid-template-columns:1fr; } }'''


def _feat_dark(c, name, photos, m):
    parts = _split_body(c.body, 4)
    rows = ""
    for j, part in enumerate(parts):
        rows += f'<div class="fd-row"><div class="fd-num">0{j+1}</div><div class="fd-line"></div><div class="fd-txt">{part}</div></div>'
    return f'''<section class="feat-d"><div class="fd-in">
    <div class="fd-label">FEATURES</div>
    <h2 class="fd-h2">{c.headline}</h2>
    <div class="fd-sep"></div>
    <div class="fd-list">{rows}</div></div></section>''', '''.feat-d { background:#0c0c16; padding:80px 44px!important; }
.fd-in { max-width:640px; margin:0 auto; }
.fd-label { font-size:10px; font-weight:700; letter-spacing:6px; color:#d4af37; margin-bottom:20px; }
.fd-h2 { font-size:32px; font-weight:900; margin-bottom:16px; word-break:keep-all; background:linear-gradient(135deg,#999,#f0f0f0,#aaa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.fd-sep { width:60px; height:1px; background:linear-gradient(90deg,#d4af37,transparent); margin-bottom:48px; }
.fd-list { display:flex; flex-direction:column; gap:0; }
.fd-row { display:flex; align-items:center; gap:24px; padding:24px 0; border-bottom:1px solid rgba(212,175,55,.1); }
.fd-num { font-size:28px; font-weight:900; color:#d4af37; min-width:48px; font-family:'Space Grotesk',sans-serif; }
.fd-line { width:1px; height:32px; background:rgba(212,175,55,.2); }
.fd-txt { font-size:15px; color:rgba(255,255,255,.55); line-height:1.7; word-break:keep-all; }'''


def _feat_minimal(c, name, photos, m):
    parts = _split_body(c.body, 4)
    items = ""
    for j, part in enumerate(parts):
        items += f'<div class="fm-item"><span class="fm-n">{j+1}</span><p class="fm-p">{part}</p></div>'
    return f'''<section class="feat-m"><div class="fm-in">
    <h2 class="fm-h2">{c.headline}</h2>
    <div class="fm-list">{items}</div></div></section>''', '''.feat-m { background:#fff; padding:100px 80px!important; }
.fm-in { max-width:520px; }
.fm-h2 { font-size:36px; font-weight:900; color:#111; margin-bottom:60px; line-height:1.2; letter-spacing:-1.5px; word-break:keep-all; }
.fm-list { display:flex; flex-direction:column; gap:0; }
.fm-item { display:flex; gap:20px; padding:28px 0; border-top:1px solid #eee; }
.fm-n { font-size:11px; font-weight:700; color:#bbb; min-width:20px; padding-top:3px; }
.fm-p { font-size:15px; color:#555; line-height:1.9; word-break:keep-all; }
@media(max-width:600px){ .feat-m { padding:60px 28px!important; } .fm-h2 { font-size:28px; } }'''


def _feat_trendy(c, name, photos, m):
    parts = _split_body(c.body, 3)
    cards = ""
    bgs = ['rgba(147,51,234,.12)','rgba(59,130,246,.12)','rgba(236,72,153,.12)']
    borders = ['rgba(147,51,234,.3)','rgba(59,130,246,.3)','rgba(236,72,153,.3)']
    for j, part in enumerate(parts):
        cards += f'<div class="ft-card" style="background:{bgs[j%3]};border-color:{borders[j%3]}"><div class="ft-tag">#{j+1:02d} ✦</div><p class="ft-p">{part}</p></div>'
    return f'''<section class="feat-t"><div class="ft-in">
    <p class="ft-over">FEATURES ™</p>
    <h2 class="ft-h2">{c.headline}</h2>
    <div class="ft-cards">{cards}</div></div></section>''', '''.feat-t { background:#0a0a12; padding:80px 40px!important; }
.ft-in { max-width:720px; margin:0 auto; text-align:center; }
.ft-over { font-size:11px; letter-spacing:5px; color:rgba(255,255,255,.25); margin-bottom:16px; font-family:'Space Grotesk',sans-serif; }
.ft-h2 { font-family:'Playfair Display',serif; font-size:42px; font-weight:900; margin-bottom:48px; -webkit-text-stroke:1.5px rgba(255,255,255,.7); -webkit-text-fill-color:transparent; word-break:keep-all; }
.ft-cards { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }
.ft-card { border:1px solid; border-radius:20px; padding:32px 20px; text-align:left; backdrop-filter:blur(8px); }
.ft-tag { font-size:11px; font-weight:700; color:rgba(255,255,255,.4); margin-bottom:16px; font-family:'Space Grotesk',sans-serif; letter-spacing:2px; }
.ft-p { font-size:14px; color:rgba(255,255,255,.6); line-height:1.8; word-break:keep-all; }
@media(max-width:600px){ .ft-cards { grid-template-columns:1fr; } .ft-h2 { font-size:30px; } }'''


# ═══════════════════════════════════════════════════════════════
# BENEFITS / TESTIMONIALS / SPECS / GUARANTEE / SOCIAL — themed
# ═══════════════════════════════════════════════════════════════

def _render_benefits(c, name, photos, m):
    img = _img(photos, 1 if len(photos)>1 else 0, 400)
    mode = m.get("mode","standard")
    if mode == "dark":
        return f'''<section class="bn-d"><div class="bnd-wrap">
        <div class="bnd-img">{img}</div>
        <div class="bnd-txt"><div class="bnd-label">BENEFITS</div>
        <h2 class="bnd-h2">{c.headline}</h2><div class="bnd-line"></div>
        <p class="bnd-sub">{c.subheadline}</p><p class="bnd-body">{c.body}</p></div>
        </div></section>''', '''.bn-d { background:#0c0c16; padding:80px 44px!important; }
.bnd-wrap { display:flex; align-items:center; gap:60px; max-width:780px; margin:0 auto; }
.bnd-img { flex:0 0 300px; } .bnd-img .pi { border-radius:8px; box-shadow:0 20px 60px rgba(0,0,0,.5); }
.bnd-txt { flex:1; } .bnd-label { font-size:10px; letter-spacing:6px; color:#d4af37; margin-bottom:16px; font-weight:700; }
.bnd-h2 { font-size:28px; font-weight:900; margin-bottom:12px; background:linear-gradient(135deg,#ccc,#fff,#bbb); -webkit-background-clip:text; -webkit-text-fill-color:transparent; word-break:keep-all; }
.bnd-line { width:40px; height:1px; background:#d4af37; margin-bottom:16px; }
.bnd-sub { font-size:15px; color:rgba(255,255,255,.45); margin-bottom:12px; line-height:1.6; }
.bnd-body { font-size:14px; color:rgba(255,255,255,.3); line-height:1.9; }
@media(max-width:600px){ .bnd-wrap { flex-direction:column; gap:28px; } .bnd-img { flex:none; width:100%; } }'''
    elif mode == "minimal":
        return f'''<section class="bn-m"><div class="bnm-in">
        <h2 class="bnm-h2">{c.headline}</h2>
        <p class="bnm-body">{c.body}</p></div></section>''', '''.bn-m { background:#fff; padding:100px 80px!important; }
.bnm-in { max-width:480px; }
.bnm-h2 { font-size:32px; font-weight:900; color:#111; margin-bottom:24px; letter-spacing:-1px; line-height:1.2; word-break:keep-all; }
.bnm-body { font-size:15px; color:#888; line-height:2.2; word-break:keep-all; }
@media(max-width:600px){ .bn-m { padding:60px 28px!important; } }'''
    elif mode == "vintage":
        return f'''<section class="bn-v"><div class="bnv-in">
        <div class="bnv-orn">— ✦ —</div>
        <h2 class="bnv-h2">{c.headline}</h2>
        <div class="bnv-deco">◆</div>
        <p class="bnv-body">{c.body}</p>
        <div class="bnv-orn">— ✦ —</div></div></section>''', '''.bn-v {{ background:#FFF8E7; padding:80px 44px!important; }}
.bnv-in {{ max-width:520px; margin:0 auto; text-align:center; }}
.bnv-orn {{ font-size:16px; color:#C4956A; letter-spacing:10px; margin-bottom:24px; font-family:serif; }}
.bnv-h2 {{ font-family:'Playfair Display',serif; font-size:30px; font-weight:900; color:#3E2723; margin-bottom:16px; word-break:keep-all; }}
.bnv-deco {{ color:#D4AF37; font-size:10px; margin-bottom:20px; }}
.bnv-body {{ font-size:15px; color:#6D5D4B; line-height:2.2; word-break:keep-all; }}'''
    else:
        return f'''<section class="bn-s"><div class="bns-wrap">
        <div class="bns-img">{img}<div class="bns-badge">PREMIUM</div></div>
        <div class="bns-txt"><p class="bns-over">BENEFITS</p>
        <h2 class="bns-h2">{c.headline}</h2><div class="bns-line"></div>
        <p class="bns-sub">{c.subheadline}</p><p class="bns-body">{c.body}</p></div>
        </div></section>''', '''.bn-s { background:#fff; }
.bns-wrap { display:flex; align-items:center; gap:50px; max-width:780px; margin:0 auto; }
.bns-img { flex:0 0 320px; position:relative; } .bns-img .pi { width:100%; border-radius:20px; box-shadow:0 16px 40px rgba(0,0,0,.1); }
.bns-badge { position:absolute; top:-10px; right:-10px; background:linear-gradient(135deg,#e74c3c,#c0392b); color:#fff; padding:8px 18px; border-radius:20px; font-size:11px; font-weight:800; letter-spacing:2px; }
.bns-txt { flex:1; } .bns-over { font-size:11px; font-weight:700; letter-spacing:4px; color:#e74c3c; margin-bottom:8px; }
.bns-h2 { font-size:28px; font-weight:900; color:#111; margin-bottom:14px; line-height:1.3; word-break:keep-all; }
.bns-line { width:40px; height:3px; background:#e74c3c; border-radius:2px; margin-bottom:16px; }
.bns-sub { font-size:16px; color:#555; margin-bottom:14px; line-height:1.6; font-weight:500; }
.bns-body { font-size:14px; color:#888; line-height:1.9; }
@media(max-width:600px){ .bns-wrap { flex-direction:column; gap:28px; } .bns-img { flex:none; width:100%; } }'''


def _render_testimonials(c, name, photos, m):
    sents = [s.strip() for s in c.body.replace('\u3002','.').split('.') if len(s.strip())>5][:3]
    if not sents:
        sents = [c.body]
    mode = m.get("mode","standard")
    avs = ['\U0001f468\u200d\U0001f4bc','\U0001f469\u200d\U0001f373','\U0001f9d1\u200d\U0001f4bb']
    nms = ['김민준','이수진','박지영']
    bg = '#0c0c16' if mode=='dark' else '#f8f6f3' if mode!='minimal' else '#fff'
    tc = 'rgba(255,255,255,.5)' if mode=='dark' else '#555'
    nc = 'rgba(255,255,255,.3)' if mode=='dark' else '#999'
    cb = 'rgba(255,255,255,.03)' if mode=='dark' else '#fff'
    bb = 'rgba(255,255,255,.06)' if mode=='dark' else '#eee'
    h2c = '#fff' if mode=='dark' else '#111'
    h2sub = 'rgba(255,255,255,.35)' if mode=='dark' else '#999'
    cards = ""
    for j, s in enumerate(sents):
        cards += f'<div class="rv-c" style="background:{cb};border-color:{bb}"><div class="rv-st">{"★"*5}</div><p class="rv-t" style="color:{tc}">"{s}"</p><div class="rv-a"><span class="rv-av">{avs[j%3]}</span><span class="rv-nm" style="color:{nc}">{nms[j%3]} · 인증구매자</span></div></div>'
    pad = '100px 80px' if mode=='minimal' else '80px 44px' if mode=='dark' else '70px 44px'
    return f'''<section class="rv-sec" style="background:{bg};padding:{pad}!important"><div class="rv-in">
    <h2 class="rv-h2" style="color:{h2c}">{c.headline}</h2><p class="rv-sub" style="color:{h2sub}">{c.subheadline}</p>
    <div class="rv-grid">{cards}</div></div></section>''', '''.rv-in { max-width:780px; margin:0 auto; }
.rv-h2 { font-size:30px; font-weight:900; text-align:center; margin-bottom:10px; word-break:keep-all; }
.rv-sub { font-size:15px; text-align:center; margin-bottom:48px; }
.rv-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:18px; }
.rv-c { border-radius:16px; padding:28px 22px; border:1px solid; transition:all .3s; }
.rv-c:hover { transform:translateY(-3px); }
.rv-st { color:#f39c12; font-size:14px; margin-bottom:12px; letter-spacing:2px; }
.rv-t { font-size:14px; line-height:1.8; margin-bottom:16px; word-break:keep-all; font-style:italic; }
.rv-a { display:flex; align-items:center; gap:8px; }
.rv-av { font-size:24px; } .rv-nm { font-size:12px; font-weight:500; }'''


def _render_specs(c, name, photos, m):
    specs = _split_body(c.body, 5)
    img = _img(photos, 2 if len(photos)>2 else 0, 500)
    mode = m.get("mode","standard")
    rows = ""
    nc = '#4fc3f7' if mode=='trendy' else '#d4af37' if mode=='dark' else '#e74c3c'
    for j, spec in enumerate(specs):
        rows += f'<div class="sp-r"><span class="sp-n" style="color:{nc}">0{j+1}</span><span class="sp-v">{spec}</span></div>'

    bg = '#0a1628' if mode=='trendy' else '#0c0c16' if mode=='dark' else '#0a0a1e'
    extra = ''
    if mode == 'trendy':
        extra = 'background-image:linear-gradient(rgba(79,195,247,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(79,195,247,.04) 1px,transparent 1px);background-size:20px 20px;'
    return f'''<section class="sp-sec" style="background:{bg};{extra}"><div class="sp-wrap">
    <div class="sp-info"><h2 class="sp-h2">{c.headline}</h2><p class="sp-sub">{c.subheadline}</p>
    <div class="sp-list">{rows}</div></div>
    <div class="sp-vis">{img}</div></div></section>''', '''.sp-sec { padding:70px 44px!important; position:relative; }
.sp-wrap { display:flex; align-items:center; gap:50px; max-width:780px; margin:0 auto; }
.sp-info { flex:1; } .sp-h2 { font-size:28px; font-weight:900; color:#fff; margin-bottom:8px; word-break:keep-all; }
.sp-sub { font-size:14px; color:rgba(255,255,255,.35); margin-bottom:28px; }
.sp-list { display:flex; flex-direction:column; }
.sp-r { display:flex; align-items:center; gap:16px; padding:14px 0; border-bottom:1px solid rgba(255,255,255,.07); }
.sp-n { font-size:12px; font-weight:800; min-width:28px; } .sp-v { font-size:14px; color:rgba(255,255,255,.65); line-height:1.6; word-break:keep-all; }
.sp-vis { flex:0 0 260px; } .sp-vis .pi { width:100%; border-radius:16px; box-shadow:0 16px 40px rgba(0,0,0,.4); }
@media(max-width:600px){ .sp-wrap { flex-direction:column; gap:28px; } .sp-vis { flex:none; width:100%; } }'''


def _render_cta(c, name, photos, m):
    mode = m.get("mode","standard")
    if mode == "dark":
        return f'''<section class="cta-d"><div class="ctd-border"><div class="ctd-in">
        <h2 class="ctd-h2">{c.headline}</h2><div class="ctd-line"></div>
        <p class="ctd-sub">{c.subheadline}</p><p class="ctd-body">{c.body}</p>
        <a href="#" class="ctd-btn">{c.cta_text or "구매하기"}</a>
        </div></div></section>''', '''.cta-d { background:#08080f; padding:80px 44px!important; }
.ctd-border { border:1px solid rgba(212,175,55,.2); padding:60px 40px; max-width:600px; margin:0 auto; text-align:center; }
.ctd-h2 { font-size:36px; font-weight:900; margin-bottom:16px; background:linear-gradient(135deg,#aaa,#fff,#bbb); -webkit-background-clip:text; -webkit-text-fill-color:transparent; word-break:keep-all; }
.ctd-line { width:60px; height:1px; background:linear-gradient(90deg,transparent,#d4af37,transparent); margin:0 auto 20px; }
.ctd-sub { font-size:15px; color:rgba(255,255,255,.4); margin-bottom:12px; }
.ctd-body { font-size:14px; color:rgba(255,255,255,.25); line-height:1.8; margin-bottom:36px; }
.ctd-btn { display:inline-block; background:linear-gradient(135deg,#d4af37,#b8942a); color:#080808; padding:16px 52px; font-size:14px; font-weight:800; letter-spacing:3px; text-transform:uppercase; text-decoration:none; }'''
    elif mode == "trendy":
        return f'''<section class="cta-t"><div class="ctt-blob ctt-b1"></div><div class="ctt-blob ctt-b2"></div>
        <div class="ctt-in">
        <h2 class="ctt-h2">{c.headline}</h2><p class="ctt-sub">{c.subheadline}</p>
        <a href="#" class="ctt-btn">{c.cta_text or "구매하기"} →</a>
        </div></section>''', '''.cta-t { position:relative; background:#0a0a12; padding:100px 40px!important; text-align:center; overflow:hidden; }
.ctt-blob { position:absolute; border-radius:50%; filter:blur(50px); }
.ctt-b1 { width:300px; height:300px; top:-50px; left:10%; background:rgba(99,102,241,.4); }
.ctt-b2 { width:350px; height:350px; bottom:-80px; right:5%; background:rgba(168,85,247,.3); }
.ctt-in { position:relative; z-index:1; max-width:500px; margin:0 auto; }
.ctt-h2 { font-family:'Playfair Display',serif; font-size:48px; font-weight:900; margin-bottom:16px; -webkit-text-stroke:1.5px rgba(255,255,255,.8); -webkit-text-fill-color:transparent; word-break:keep-all; }
.ctt-sub { font-size:15px; color:rgba(255,255,255,.4); margin-bottom:40px; font-family:'Space Grotesk',sans-serif; }
.ctt-btn { display:inline-block; background:linear-gradient(135deg,rgba(147,51,234,.8),rgba(59,130,246,.8)); color:#fff; padding:16px 44px; border-radius:50px; font-size:14px; font-weight:600; text-decoration:none; font-family:'Space Grotesk',sans-serif; }'''
    elif mode == "minimal":
        return f'''<section class="cta-m"><div class="ctm-in">
        <h2 class="ctm-h2">{c.headline}</h2>
        <a href="#" class="ctm-btn">{c.cta_text or "구매하기"}</a>
        </div></section>''', '''.cta-m { background:#111; padding:100px 80px!important; }
.ctm-in { max-width:500px; }
.ctm-h2 { font-size:40px; font-weight:900; color:#fff; margin-bottom:40px; line-height:1.2; letter-spacing:-2px; word-break:keep-all; }
.ctm-btn { display:inline-block; color:#fff; font-size:13px; font-weight:700; letter-spacing:3px; text-transform:uppercase; text-decoration:none; border-bottom:2px solid #fff; padding-bottom:8px; }
@media(max-width:600px){ .cta-m { padding:60px 28px!important; } .ctm-h2 { font-size:28px; } }'''
    elif mode == "vintage":
        return f'''<section class="cta-v"><div class="ctv-border"><div class="ctv-in">
        <div class="ctv-orn">— ✦ —</div>
        <h2 class="ctv-h2">{c.headline}</h2>
        <p class="ctv-sub">{c.subheadline}</p>
        <a href="#" class="ctv-btn">{c.cta_text or "구매하기"}</a>
        <div class="ctv-orn">— ✦ —</div></div></div></section>''', '''.cta-v {{ background:#3E2723; padding:80px 44px!important; }}
.ctv-border {{ border:2px solid #D4AF37; padding:60px 40px; max-width:600px; margin:0 auto; text-align:center; position:relative; }}
.ctv-border::before {{ content:""; position:absolute; inset:6px; border:1px solid rgba(212,175,55,.3); }}
.ctv-orn {{ font-size:16px; color:#D4AF37; letter-spacing:10px; margin-bottom:24px; font-family:serif; }}
.ctv-h2 {{ font-family:'Playfair Display',serif; font-size:38px; font-weight:900; color:#FFF8E7; margin-bottom:16px; word-break:keep-all; }}
.ctv-sub {{ font-size:15px; color:rgba(255,248,231,.5); margin-bottom:32px; }}
.ctv-btn {{ display:inline-block; background:none; color:#D4AF37; padding:14px 44px; font-size:13px; font-weight:700; text-decoration:none; letter-spacing:4px; text-transform:uppercase; border:2px solid #D4AF37; margin-bottom:24px; }}'''
    else:
        bg = _bg(photos, 0, 600)
        return f'''<section class="cta-s" style="background-image:url('{bg}')">
        <div class="cts-ov"></div><div class="cts-in">
        <h2 class="cts-h2">{c.headline}</h2><p class="cts-sub">{c.subheadline}</p><p class="cts-body">{c.body}</p>
        <a href="#" class="cts-btn">{c.cta_text or "구매하기"}</a>
        </div></section>''', '''.cta-s { position:relative; padding:0!important; background-size:cover; background-position:center; }
.cts-ov { position:absolute; inset:0; background:linear-gradient(135deg,rgba(231,76,60,.88),rgba(192,57,43,.92)); }
.cts-in { position:relative; z-index:1; padding:80px 40px; text-align:center; }
.cts-h2 { font-size:36px; font-weight:900; color:#fff; margin-bottom:12px; word-break:keep-all; }
.cts-sub { font-size:17px; color:rgba(255,255,255,.85); margin-bottom:10px; }
.cts-body { font-size:14px; color:rgba(255,255,255,.55); line-height:1.7; max-width:460px; margin:0 auto 32px; }
.cts-btn { display:inline-block; background:#fff; color:#e74c3c; padding:18px 52px; border-radius:50px; font-size:17px; font-weight:800; text-decoration:none; box-shadow:0 8px 24px rgba(0,0,0,.2); }
@media(max-width:600px){ .cts-in { padding:60px 24px; } .cts-h2 { font-size:28px; } }'''


def _render_guarantee(c, name, photos, m):
    mode = m.get("mode","standard")
    bg = '#0c0c16' if mode=='dark' else '#fff' if mode=='minimal' else '#f9fafb'
    tc = '#fff' if mode=='dark' else '#111'
    bc = 'rgba(255,255,255,.5)' if mode=='dark' else '#555'
    gc = 'rgba(255,255,255,.04)' if mode=='dark' else '#fff'
    gb = 'rgba(255,255,255,.08)' if mode=='dark' else '#eee'
    ba_bg = 'rgba(255,255,255,.04)' if mode=='dark' else '#fff'
    ba_b = 'rgba(255,255,255,.1)' if mode=='dark' else '#e0e0e0'
    ba_c = 'rgba(255,255,255,.5)' if mode=='dark' else '#555'
    pad = '100px 80px' if mode=='minimal' else '70px 44px'
    shield = '' if mode=='minimal' else '<div style="text-align:center;font-size:48px;margin-bottom:16px">🛡️</div>'
    return f'''<section style="background:{bg};padding:{pad}!important"><div class="gu-in">{shield}
    <h2 class="gu-h2" style="color:{tc}">{c.headline}</h2>
    <div class="gu-box" style="background:{gc};border-color:{gb}"><p class="gu-p" style="color:{bc}">{c.body}</p></div>
    <div class="gu-badges">
    <span class="gu-b" style="background:{ba_bg};border-color:{ba_b};color:{ba_c}">✔ 100% 환불 보증</span>
    <span class="gu-b" style="background:{ba_bg};border-color:{ba_b};color:{ba_c}">✔ 무료 배송</span>
    <span class="gu-b" style="background:{ba_bg};border-color:{ba_b};color:{ba_c}">✔ 정품 인증</span>
    </div></div></section>''', '''.gu-in { max-width:780px; margin:0 auto; text-align:center; }
.gu-h2 { font-size:30px; font-weight:900; text-align:center; margin-bottom:10px; word-break:keep-all; }
.gu-box { border-radius:16px; padding:32px 28px; border:1px solid; margin:24px 0; }
.gu-p { font-size:15px; line-height:2; word-break:keep-all; }
.gu-badges { display:flex; justify-content:center; gap:12px; flex-wrap:wrap; }
.gu-b { border:1px solid; border-radius:30px; padding:8px 20px; font-size:13px; font-weight:500; }'''


def _render_social_proof(c, name, photos, m):
    mode = m.get("mode","standard")
    bg1 = '#08080f' if mode=='dark' else '#0a0a12' if mode=='trendy' else '#0a0a1e'
    bg2 = '#14141f' if mode=='dark' else '#16162a' if mode=='trendy' else '#1a1a3e'
    return f'''<section class="so-sec" style="background:linear-gradient(135deg,{bg1},{bg2})"><div class="so-in">
    <h2 class="so-h2">{c.headline}</h2>
    <div class="so-stats">
    <div class="so-s"><span class="so-n">98%</span><span class="so-l">만족도</span></div>
    <div class="so-d"></div>
    <div class="so-s"><span class="so-n">50K+</span><span class="so-l">누적 판매</span></div>
    <div class="so-d"></div>
    <div class="so-s"><span class="so-n">4.9</span><span class="so-l">★ 평점</span></div>
    </div><p class="so-body">{c.body}</p></div></section>''', '''.so-in { max-width:780px; margin:0 auto; text-align:center; }
.so-h2 { font-size:30px; font-weight:900; color:#fff; margin-bottom:32px; word-break:keep-all; }
.so-stats { display:flex; justify-content:center; margin-bottom:32px; }
.so-s { text-align:center; padding:0 36px; }
.so-n { display:block; font-size:36px; font-weight:900; color:#fff; margin-bottom:4px; }
.so-l { font-size:13px; color:rgba(255,255,255,.35); }
.so-d { width:1px; background:rgba(255,255,255,.08); }
.so-body { font-size:15px; color:rgba(255,255,255,.4); line-height:1.9; max-width:500px; margin:0 auto; word-break:keep-all; }
@media(max-width:600px){ .so-s { padding:0 20px; } .so-n { font-size:28px; } }'''



# ═══════════════════════════════════════════════════════════════
# VINTAGE VARIANTS — sepia tones, ornamental, aged paper feel
# ═══════════════════════════════════════════════════════════════

def _hero_vintage(c, name, photos, m):
    return f'''<section class="hero-v">
  <div class="hv-paper"></div>
  <div class="hv-in">
    <div class="hv-orn-top">— ✦ —</div>
    <div class="hv-brand">{name}</div>
    <h1 class="hv-h1">{c.headline}</h1>
    <div class="hv-rule"><span class="hv-diamond">◆</span></div>
    <p class="hv-sub">{c.subheadline}</p>
    <p class="hv-body">{c.body}</p>
    {f'<a class="hv-cta" href="#">{c.cta_text}</a>' if c.cta_text else ''}
    <div class="hv-orn-bot">— ✦ —</div>
  </div>
</section>''', '''.hero-v { position:relative; background:#FFF8E7; min-height:560px; display:flex; align-items:center; justify-content:center; padding:0!important; }
.hv-paper { position:absolute; inset:0; background:url("data:image/svg+xml,%3Csvg width='100' height='100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%%' height='100%%' filter='url(%23n)' opacity='.03'/%3E%3C/svg%3E"); }
.hv-in { position:relative; z-index:1; text-align:center; padding:80px 60px; max-width:640px; }
.hv-orn-top, .hv-orn-bot { font-size:18px; color:#C4956A; letter-spacing:12px; margin-bottom:28px; font-family:serif; }
.hv-orn-bot { margin-top:40px; margin-bottom:0; }
.hv-brand { font-size:11px; font-weight:700; letter-spacing:8px; text-transform:uppercase; color:#B8860B; border:2px solid #D4AF37; display:inline-block; padding:6px 24px; margin-bottom:32px; }
.hv-h1 { font-family:'Playfair Display',serif; font-size:52px; font-weight:900; color:#3E2723; line-height:1.15; margin-bottom:20px; word-break:keep-all; }
.hv-rule { text-align:center; margin-bottom:24px; }
.hv-diamond { color:#D4AF37; font-size:12px; position:relative; }
.hv-diamond::before, .hv-diamond::after { content:''; position:absolute; top:50%; width:80px; height:1px; background:linear-gradient(90deg,transparent,#D4AF37); }
.hv-diamond::before { right:20px; background:linear-gradient(90deg,#D4AF37,transparent); }
.hv-diamond::after { left:20px; }
.hv-sub { font-family:'Playfair Display',serif; font-size:18px; color:#8B7355; font-style:italic; line-height:1.7; margin-bottom:16px; }
.hv-body { font-size:14px; color:#A0937A; line-height:2; margin-bottom:32px; max-width:420px; margin-left:auto; margin-right:auto; }
.hv-cta { display:inline-block; background:none; color:#3E2723; padding:14px 40px; font-size:13px; font-weight:700; text-decoration:none; letter-spacing:4px; text-transform:uppercase; border:2px solid #3E2723; transition:all .3s; }
.hv-cta:hover { background:#3E2723; color:#FFF8E7; }
@media(max-width:600px){ .hv-in { padding:60px 24px; } .hv-h1 { font-size:36px; } }'''


def _feat_vintage(c, name, photos, m):
    parts = _split_body(c.body, 4)
    cards = ""
    nums = ["I", "II", "III", "IV"]
    for j, part in enumerate(parts):
        cards += f'<div class="fv-card"><div class="fv-num">{nums[j]}</div><div class="fv-sep-sm">—</div><p class="fv-txt">{part}</p></div>'
    return f'''<section class="feat-v"><div class="fv-in">
    <div class="fv-orn">— ✦ FEATURES ✦ —</div>
    <h2 class="fv-h2">{c.headline}</h2>
    <p class="fv-sub">{c.subheadline}</p>
    <div class="fv-grid">{cards}</div></div></section>''', '''.feat-v { background:#F5EDE0; padding:80px 44px!important; position:relative; }
.feat-v::before, .feat-v::after { content:''; position:absolute; left:44px; right:44px; height:2px; background:linear-gradient(90deg,transparent,#D4AF37 20%,#D4AF37 80%,transparent); }
.feat-v::before { top:0; } .feat-v::after { bottom:0; }
.fv-in { max-width:720px; margin:0 auto; text-align:center; }
.fv-orn { font-size:11px; letter-spacing:6px; color:#C4956A; margin-bottom:20px; font-family:serif; }
.fv-h2 { font-family:'Playfair Display',serif; font-size:34px; font-weight:900; color:#3E2723; margin-bottom:10px; word-break:keep-all; }
.fv-sub { font-size:15px; color:#8B7355; font-style:italic; margin-bottom:48px; }
.fv-grid { display:grid; grid-template-columns:1fr 1fr; gap:24px; }
.fv-card { background:rgba(255,255,255,.6); border:1px solid #E8D5B8; border-radius:4px; padding:32px 24px; text-align:center; }
.fv-num { font-family:'Playfair Display',serif; font-size:24px; font-weight:900; color:#B8860B; margin-bottom:4px; }
.fv-sep-sm { color:#D4AF37; margin-bottom:12px; letter-spacing:4px; }
.fv-txt { font-size:14px; color:#6D5D4B; line-height:1.9; word-break:keep-all; }
@media(max-width:600px){ .fv-grid { grid-template-columns:1fr; } }'''


# ═══════════════════════════════════════════════════════════════
# DISPATCH & RENDERER
# ═══════════════════════════════════════════════════════════════

def _render_hero(c, name, photos, m):
    mode = m.get("mode", "standard")
    if mode == "dark":
        return _hero_dark(c, name, photos, m)
    if mode == "minimal":
        return _hero_minimal(c, name, photos, m)
    if mode == "trendy":
        return _hero_trendy(c, name, photos, m)
    if mode == "vintage":
        return _hero_vintage(c, name, photos, m)
    return _hero_standard(c, name, photos, m)


def _render_features(c, name, photos, m):
    mode = m.get("mode", "standard")
    if mode == "dark":
        return _feat_dark(c, name, photos, m)
    if mode == "minimal":
        return _feat_minimal(c, name, photos, m)
    if mode == "trendy":
        return _feat_trendy(c, name, photos, m)
    if mode == "vintage":
        return _feat_vintage(c, name, photos, m)
    return _feat_standard(c, name, photos, m)


SECTION_RENDERERS = {
    "hero": _render_hero,
    "features": _render_features,
    "benefits": _render_benefits,
    "testimonials": _render_testimonials,
    "specs": _render_specs,
    "cta": _render_cta,
    "guarantee": _render_guarantee,
    "social_proof": _render_social_proof,
}

GLOBAL_CSS = """* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:var(--df-font-body,'Noto Sans KR',-apple-system,sans-serif); background:#f5f5f5; color:var(--df-color-text,#333); -webkit-font-smoothing:antialiased; }
.dp { max-width:860px; margin:0 auto; background:#fff; overflow:hidden; box-shadow:0 0 60px rgba(0,0,0,.1); }
.dp section { padding:70px 44px; }
.dp img { max-width:100%; height:auto; display:block; }
@media(max-width:600px){ .dp section { padding:48px 20px; } }
"""


class HtmlRenderer:
    def __init__(self, provider=None, product_photos=None, selected_principles=None):
        self.provider = provider
        self.product_photos = product_photos or []
        self.principles = set(selected_principles or [])
        self.mode = _detect_mode(self.principles)
        self.meta = {"mode": self.mode, "principles": self.principles}

    def render_section(self, copy, product_name=""):
        renderer = SECTION_RENDERERS.get(copy.section_type, _render_features)
        html, css = renderer(copy, product_name, self.product_photos, self.meta)
        return RenderedSection(section_index=copy.section_index, section_type=copy.section_type, html=html, css=css, copy=copy)

    def render_all(self, sections, product_name="", progress_callback=None):
        page = RenderedPage()
        # Build design token :root block from selected principles and prepend to global CSS
        token_set = DesignTokenSet.from_principles(list(self.principles))
        token_css = token_set.to_css()
        page.global_css = token_css + "\n" + GLOBAL_CSS
        for i, copy in enumerate(sections):
            if progress_callback:
                progress_callback(i, len(sections))
            page.sections.append(self.render_section(copy, product_name))
        return page
