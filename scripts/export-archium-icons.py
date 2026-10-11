#!/usr/bin/env python3
"""Deterministic Archium Portal app-icon exporter. Requires CairoSVG.

Usage: python scripts/export-archium-icons.py
Output: assets/branding/archium/ (SVG masters and size-specific PNGs)
"""
from pathlib import Path
import argparse
import cairosvg

CANVAS = 1024
ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'branding' / 'archium'

# Archium's distinct arched A (not a Chromium-derived glyph).
ARCH = '''M 177 760
 C 213 643, 302 387, 392 285
 C 450 219, 500 214, 539 226
 C 632 254, 703 445, 788 670
 L 829 772
 Q 838 804, 800 805
 L 696 805
 Q 669 805, 658 775
 L 606 616
 C 579 530, 548 465, 499 461
 C 430 456, 388 589, 355 754
 Q 343 805, 306 805
 L 205 805
 Q 165 805, 177 760 Z'''

DEFS = '''<defs>
 <linearGradient id="tile" x1=".05" x2=".90" y1="0" y2="1">
  <stop offset="0" stop-color="#322743"/>
  <stop offset=".50" stop-color="#171523"/>
  <stop offset="1" stop-color="#0E0E18"/>
 </linearGradient>
 <radialGradient id="glow" cx=".28" cy=".06" r="1">
  <stop stop-color="#AA75CD" stop-opacity=".32"/>
  <stop offset=".75" stop-color="#211629" stop-opacity="0"/>
 </radialGradient>
 <linearGradient id="arch" x1=".02" y1=".80" x2=".90" y2=".18">
  <stop offset="0" stop-color="#A883FF"/>
  <stop offset=".38" stop-color="#CBABFF"/>
  <stop offset=".64" stop-color="#E2C6F5"/>
  <stop offset="1" stop-color="#FFDBBF"/>
 </linearGradient>
 <linearGradient id="facet" x1=".03" y1="1" x2=".75" y2=".05">
  <stop offset="0" stop-color="#9B78FC"/>
  <stop offset=".48" stop-color="#6B51EA"/>
  <stop offset="1" stop-color="#3B3099"/>
 </linearGradient>
 <linearGradient id="mono" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FFFFFF"/><stop offset="1" stop-color="#DADBE5"/></linearGradient>
 <linearGradient id="shadow" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#B5A0FF" stop-opacity=".8"/><stop offset="1" stop-color="#6C58D5" stop-opacity=".15"/></linearGradient>
 <clipPath id="archClip"><path d="''' + ARCH + '''"/></clipPath>
</defs>'''

# Architecture: a dark/light floating tile, pure mark, or Android 108dp-safe foreground.
def svg(variant):
    light = variant == 'light'
    mono = variant.startswith('monochrome')
    is_bg = variant.startswith('adaptive-background')
    transparent = variant in ('symbol', 'adaptive-foreground', 'monochrome-light', 'monochrome-dark')
    background = ''
    if not transparent:
        if light:
            background = '''<rect x="22" y="22" width="980" height="980" rx="248" fill="#FFFFFF"/>
<rect x="24" y="24" width="976" height="976" rx="247" fill="none" stroke="#EAE7F2" stroke-width="5"/>'''
        else:
            background = '''<rect x="22" y="22" width="980" height="980" rx="248" fill="url(#tile)"/>
<rect x="22" y="22" width="980" height="980" rx="248" fill="url(#glow)"/>
<rect x="28" y="28" width="968" height="968" rx="242" fill="none" stroke="url(#shadow)" stroke-width="8" opacity=".8"/>'''
    if is_bg:
        mark=''
    elif mono:
        fill = '#FFFFFF' if variant == 'monochrome-light' else '#171523'
        mark = f'<path d="{ARCH}" fill="{fill}"/>'
    else:
        # Gradients and a wrapped inner facet are behind the foreground opening; holes stay transparent.
        mark = f'''<path d="{ARCH}" fill="url(#arch)"/>
<g clip-path="url(#archClip)">
  <path d="M 170 820 C 220 585, 387 443, 496 461 C 591 480, 665 659, 720 827 L 625 839 C 572 626, 539 461, 497 461 C 428 455, 388 591, 355 756 L 324 841 Z" fill="url(#facet)" opacity=".95"/>
  <path d="M 190 730 C 297 464, 422 414, 505 463 C 574 505, 635 613, 676 773" stroke="#F6DFFF" stroke-opacity=".53" stroke-width="11" fill="none"/>
  <path d="M 172 755 C 277 459, 363 273, 445 231" fill="none" stroke="#F8E8FF" stroke-opacity=".26" stroke-width="10"/>
</g>'''
    # Native Android adaptive foreground: content sized down to fit launcher safe region.
    if variant == 'adaptive-foreground':
        mark = f'<g transform="translate(108 108) scale(.79)">{mark}</g>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 1024 1024">
{DEFS}
{background}
{mark}
</svg>\n'''

SIZES = {
    'dark': [16, 32, 48, 64, 128, 192, 256, 512, 1024],
    'light': [128, 256, 512, 1024],
    'monochrome-light': [32, 64, 256, 512],
    'monochrome-dark': [32, 64, 256, 512],
    'symbol': [256, 512, 1024],
    'adaptive-foreground': [432, 512, 1024],
    'adaptive-background': [432, 512],
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=ROOT)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    n = 0
    for variant, sizes in SIZES.items():
        src = svg(variant)
        (args.out / f'archium-{variant}.svg').write_text(src, encoding='utf-8')
        for size in sizes:
            target = args.out / f'archium-{variant}-{size}.png'
            cairosvg.svg2png(bytestring=src.encode('utf-8'), write_to=str(target), output_width=size, output_height=size)
            n += 1
    print(f'Exported {n} PNG files and {len(SIZES)} SVG masters to {args.out}')

if __name__ == '__main__':
    main()
