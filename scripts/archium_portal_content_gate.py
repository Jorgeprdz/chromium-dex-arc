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


def packed_paths(entry, extension):
    # Resources may be flattened/renamed by aapt2; never infer a ZIP entry
    # from the original source filename.
    paths = re.findall(r"res/[a-zA-Z0-9_./-]+\." + re.escape(extension)
                       + r"\b", entry)
    return sorted(set(paths))


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
            portal.png_pixels(data) for path, data in desired.items()
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
            extensions = ["png"] if alias in ICON_ENTRIES else ["xml"]
            found = [p for ext in extensions for p in packed_paths(entry, ext)]
            if not found:
                raise ValueError("Resource table has no packaged path for " + alias)
            for path in found:
                if path not in names:
                    raise ValueError("Compiled resource points to missing ZIP entry: " + path)
                if alias in ICON_ENTRIES:
                    try:
                        pixels = portal.png_pixels(archive.read(path))
                    except Exception as exc:
                        raise ValueError("Invalid compiled Portal PNG: " + path) from exc
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
                            if label not in compiled or not re.search(
                                    r"@0x0*" + format(ids.get(layer, resource_entry(aapt_dump, layer)[0]), "x")
                                    + r"\b", compiled, flags=re.I):
                                raise ValueError("Wrong adaptive icon layer for " + label)
                    elif ("M 177 760" not in compiled
                          or "scaleX" not in compiled or "scaleY" not in compiled):
                        raise ValueError("Themed glyph content/safe zone was replaced: " + path)
    return {
        "status": "PASS",
        "scope": "aapt2 compiled alias chain + decoded RGBA PNG content + vector identity",
        "layers": list(ICON_ENTRIES),
        "aliases": list(XML_ENTRIES),
        "limit": "Launcher masks, appearance and interaction still require physical device",
    }
