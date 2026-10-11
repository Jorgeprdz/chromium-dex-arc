#!/usr/bin/env python3
"""Verify packaged launcher pixels and vector/alias links, not just resource names.

Uses aapt2's *compiled* resource table to find actual ZIP entries; comparing
source PNG filenames alone would accept an unrelated image under a correct alias.
No device/visual claim is made here.
"""
import importlib.util
from pathlib import Path
import re
import zipfile
import io
import json
import struct
import xml.etree.ElementTree as ET


def portal_module():
    path = Path(__file__).resolve().with_name("integrate-archium-portal.py")
    spec = importlib.util.spec_from_file_location("archium_portal_source", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ICON_ENTRIES = ("mipmap/app_icon", "mipmap/layered_app_icon",
                "mipmap/layered_app_icon_background")
XML_ENTRIES = ("drawable/ic_launcher", "drawable/ic_launcher_round",
               "drawable/themed_app_icon")


def resource_entry(dump, name):
    """Return exact resource entry and stable ID from aapt2 resources dump."""
    sections = re.split(r"(?m)(?=^\s*(?:spec )?resource\s+0x[0-9a-fA-F]+\s+)", dump)
    entries = []
    pat = re.compile(r"^\s*(?:spec )?resource\s+0x([0-9a-fA-F]+)\s+"
                     r"(?:[^\s:]+:)?" + re.escape(name) + r"(?:\s|$)", re.M)
    for section in sections:
        match = pat.search(section)
        if match:
            entries.append((int(match.group(1), 16), section))
    if not entries:
        raise ValueError("Missing compiled Portal resource alias: " + name)
    ids = {id_ for id_, _ in entries}
    if len(ids) != 1:
        raise ValueError("Ambiguous Portal resource alias: " + name)
    return next(iter(ids)), "\n".join(s for _, s in entries)


def packed_paths(entry, extension=None):
    # Resources may be flattened/renamed by aapt2; never infer a ZIP entry
    # from the original source filename.
    paths = re.findall(r"res/[a-zA-Z0-9_./+-]+", entry)
    if extension is not None:
        paths = [p for p in paths if p.endswith('.' + extension)]
    return sorted(set(paths))


def packaged_pixels(portal, blob):
    if blob[:4] == b'RIFF' and blob[8:12] == b'WEBP':
        # Official Chromium losslessly converts launcher PNGs to WebP and
        # strips image extensions. Decode actual bytes, never infer format.
        from PIL import Image
        with Image.open(io.BytesIO(blob)) as source:
            width, height = source.size
            if source.format != 'WEBP' or getattr(source, 'n_frames', 1) != 1 \
                    or height != width or not 16 <= width <= 1024:
                raise ValueError('Invalid packaged Portal WebP')
            return width, source.convert('RGBA').tobytes()
    return portal.png_pixels(blob, allow_rgb=True)


def visible_pixels(pixels):
    """Canonicalize RGB only when alpha is exactly zero.

    Chromium's lossless cwebp command omits -exact and may discard hidden RGB.
    Every alpha byte and every RGB byte at nonzero alpha remains exact.
    """
    width, rgba = pixels
    canonical = bytearray(rgba)
    for index in range(0, len(canonical), 4):
        if canonical[index + 3] == 0:
            canonical[index:index + 3] = b'\0\0\0'
    return width, bytes(canonical)


def verify_themed_vector(compiled, source):
    """Match the complete compiled vector and transform to the approved XML."""
    android = '{http://schemas.android.com/apk/res/android}'
    # Stable Android framework IDs, confirmed by genuine SDK37 AAPT2 output.
    # Chromium strips XML namespaces; names alone cannot establish ownership.
    framework_ids = {
        'height': 0x01010155, 'width': 0x01010159,
        'viewportWidth': 0x01010402, 'viewportHeight': 0x01010403,
        'scaleX': 0x01010324, 'scaleY': 0x01010325,
        'translateX': 0x0101045a, 'translateY': 0x0101045b,
        'fillColor': 0x01010404, 'pathData': 0x01010405,
    }
    expected = []
    def visit(node, parent=None):
        expected.append((node.tag, parent, {
            key.removeprefix(android): value for key, value in node.attrib.items()}))
        for child in node:
            visit(child, node.tag)
    visit(ET.fromstring(source))
    actual, stack = [], []
    for line in compiled.splitlines():
        element = re.match(r'^(\s*)E:\s*([\w-]+)\b', line)
        if element:
            depth, tag = len(element[1]), element[2]
            while stack and depth <= stack[-1][0]:
                stack.pop()
            attrs = {}
            actual.append((tag, stack[-1][1] if stack else None, attrs))
            stack.append((depth, tag, attrs))
            continue
        if re.match(r'^\s*A:', line):
            attribute = re.match(r'^\s*A:\s*(\S+)\(0x([0-9a-fA-F]{1,8})\)=(.*)$', line)
            if attribute is None:
                raise ValueError('Themed glyph has an unexpected attribute format: ' + line.strip()[:160])
            name, id_hex, value = attribute.groups()
            if not stack or (':' in name and not name.startswith((
                    'android:', 'http://schemas.android.com/apk/res/android:'))):
                raise ValueError('Themed glyph has an unexpected attribute: ' + name)
            name = name.rsplit(':', 1)[-1]
            if framework_ids.get(name) != int(id_hex, 16):
                raise ValueError('Themed glyph has an unexpected Android attribute ID: '
                                 + name + '(0x' + id_hex + ')')
            if name in stack[-1][2]:
                raise ValueError('Themed glyph has a duplicate attribute')
            stack[-1][2][name] = value.strip()
    def canonical(name, value, compiled_value=False):
        if name == 'pathData':
            if compiled_value:
                value = json.JSONDecoder().raw_decode(value)[0]
            return re.sub(r'\s+', ' ', value).strip()
        if name == 'fillColor':
            if not re.fullmatch(r'#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?', value):
                raise ValueError('Unexpected fill color')
            return int(value[1:], 16) | (0xff000000 if len(value) == 7 else 0)
        number = re.fullmatch(r'(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)(dp)?', value)
        if number is None:
            raise ValueError('Unexpected vector numeric value')
        return struct.pack('!f', float(number[1])), number[2]
    try:
        if len(actual) != len(expected):
            raise ValueError('Element count differs')
        for (tag, parent, attrs), (want_tag, want_parent, want) in zip(actual, expected):
            if (tag, parent, attrs.keys()) != (want_tag, want_parent, want.keys()):
                raise ValueError('Vector structure/attributes differ')
            if any(canonical(name, attrs[name], True) != canonical(name, want[name]) for name in want):
                raise ValueError('Vector content/transform differs')
    except (ValueError, TypeError, struct.error, OverflowError) as error:
        raise ValueError('Themed glyph content/safe zone was replaced') from error


def check_content(apk, aapt_dump, xmltree):
    """Fail closed for unrelated Portal images aliased under correct names.

    xmltree: callback taking an archive entry path and returning aapt2 dump
    xmltree text for that *compiled* resource.
    """
    portal = portal_module()
    desired = portal.expected_resources()
    expected = {}
    for name in ICON_ENTRIES:
        leaf = name.split("/", 1)[1] + ".png"
        expected[name] = {
            visible_pixels(portal.png_pixels(data)) for path, data in desired.items()
            if path.endswith("/" + leaf)
        }
        if not expected[name]:
            raise ValueError("No approved Portal layer for " + name)

    with zipfile.ZipFile(apk) as archive:
        names = set(archive.namelist())
        ids = {}
        for alias in ICON_ENTRIES + XML_ENTRIES:
            id_, entry = resource_entry(aapt_dump, alias)
            ids[alias] = id_
            extensions = [None] if alias in ICON_ENTRIES else ["xml"]
            found = [p for ext in extensions for p in packed_paths(entry, ext)]
            if not found:
                raise ValueError("Resource table has no packaged path for " + alias)
            for path in found:
                if path not in names:
                    raise ValueError("Compiled resource points to missing ZIP entry: " + path)
                if alias in ICON_ENTRIES:
                    try:
                        pixels = visible_pixels(packaged_pixels(portal, archive.read(path)))
                    except Exception as exc:
                        raise ValueError("Invalid compiled Portal image: " + path) from exc
                    if pixels not in expected[alias]:
                        raise ValueError("Wrong Portal pixels under " + alias + ": " + path)
            if alias in XML_ENTRIES:
                # The aapt2 resource table may select multiple configurations.
                # Inspect all of them; never accept a poisoned night-mode alias.
                for path in found:
                    compiled = xmltree(path)
                    if alias != "drawable/themed_app_icon":
                        if "adaptive-icon" not in compiled:
                            raise ValueError("Launcher icon is not adaptive: " + path)
                        for layer, label in (
                                ("mipmap/layered_app_icon", "foreground"),
                                ("mipmap/layered_app_icon_background", "background"),
                                ("drawable/themed_app_icon", "monochrome")):
                            # Validate ID *inside its specific element*, not
                            # simply present anywhere in the XML document.
                            block = re.search(
                                r"(?ms)^\s*E:\s*" + label
                                + r"\b(.*?)(?=^\s*E:|\Z)", compiled)
                            resource_id = ids.get(layer)
                            if resource_id is None:
                                resource_id = resource_entry(aapt_dump, layer)[0]
                            if block is None or not re.search(
                                    r"@0x0*" + format(resource_id, "x") + r"\b",
                                    block.group(1), flags=re.I):
                                raise ValueError("Wrong adaptive icon layer for " + label)
                    else:
                        try:
                            verify_themed_vector(compiled, desired[
                                f'{portal.BASE}/drawable/themed_app_icon.xml'])
                        except ValueError as error:
                            raise ValueError(str(error) + ' in compiled resource ' + path) from error
    return {
        "status": "PASS",
        "scope": "aapt2 compiled alias chain + exact alpha/visible RGB PNG-WebP content + vector identity",
        "layers": list(ICON_ENTRIES),
        "aliases": list(XML_ENTRIES),
        "limit": "Launcher masks, appearance and interaction still require physical device",
    }
