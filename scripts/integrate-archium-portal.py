#!/usr/bin/env python3
"""Install Archium Portal in Chromium's existing launcher resource slots.

No new package, manifest icon alias, resource target or GN source list is needed:
chrome_base_module_resources already owns these exact mipmap and drawable names.
This is deliberately a binary overlay outside the UTF-8-only Chromium patch.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REVISION = "cfd94726b7b5fb48aedcc32662f2f3fbdbadec35"
ICON_ROOT = ROOT / "assets/branding/archium"
BASE = "chrome/android/java/res_chromium_base"
# These are pinned Git blob IDs from the user-approved Portal commit.
SOURCE_BLOBS = {
    "archium-dark-48.png": "a55dbdf135f0701c2d62231dafc81e9b9ba98c58",
    "archium-dark-64.png": "564ddcb2517f46b4472668a63caeb3de0c0a23af",
    "archium-dark-128.png": "dd08cf3495ed9f8d43686ff0ed3dc88088fa6b16",
    "archium-dark-192.png": "2d9352d82545e54815bc52680c1748c9d833d85f",
    "archium-adaptive-foreground-432.png": "d5dcb024720fdc40da5cd18e1bb23b7590885f04",
    "archium-adaptive-foreground-512.png": "49c312f420c4ffaf253ad9caa42ab66e7e42456e",
    "archium-adaptive-background-432.png": "a9e2c0a9a7af2d6db1febaaf6ccc1e486a491303",
    "archium-adaptive-background-512.png": "1939222624e0da72216080bc1e8f5fb58c340f23",
    "archium-monochrome-light.svg": "3914ec740d25201707d718d32d1e587f1f6a8483",
}
DENSITIES = {
    "mdpi": ("archium-dark-48.png", "archium-adaptive-foreground-432.png",
             "archium-adaptive-background-432.png"),
    "hdpi": ("archium-dark-64.png", "archium-adaptive-foreground-432.png",
             "archium-adaptive-background-432.png"),
    "xhdpi": ("archium-dark-128.png", "archium-adaptive-foreground-432.png",
              "archium-adaptive-background-432.png"),
    "xxhdpi": ("archium-dark-128.png", "archium-adaptive-foreground-512.png",
               "archium-adaptive-background-512.png"),
    "xxxhdpi": ("archium-dark-192.png", "archium-adaptive-foreground-512.png",
                "archium-adaptive-background-512.png"),
}
APP_XML = """<?xml version="1.0" encoding="utf-8"?>
<!-- Archium Portal. Both default and round launchers resolve to these same layers. -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/layered_app_icon_background"/>
    <foreground android:drawable="@mipmap/layered_app_icon"/>
    <monochrome android:drawable="@drawable/themed_app_icon"/>
</adaptive-icon>
"""


# The Portal masters are immutable: launcher-safe APK variants are generated in
# memory, never re-exported into the 29 PNG / 7 SVG approved source files.
# The implementation deliberately needs only Python's standard library on GN
# build workers (no optional Pillow/CairoSVG dependency).
from functools import lru_cache
import binascii
import zlib


def png_pixels(blob, *, allow_rgb=False):
    """Decode non-interlaced RGB8/RGBA8 PNGs to RGBA for pixel comparison.

    Approved source assets must be RGBA8. The packaged version may be
    losslessly crunched to RGB8 by Android aapt2 if fully opaque.
    """
    if len(blob) < 33 or blob[:8] != b"\\x89PNG\\r\\n\\x1a\\n" or blob[12:16] != b"IHDR":
        raise ValueError("Invalid packaged PNG signature")
    width, height = struct.unpack_from(">II", blob, 16)
    if not 16 <= width <= 1024 or height != width:
        raise ValueError("Invalid PNG canvas dimensions")
    color = blob[25]
    if color not in ((2, 6) if allow_rgb else (6,)):
        raise ValueError("Unapproved packaged PNG color format")
    bpp = 4 if color == 6 else 3
    chunks = []
    pos = 8
    while pos + 12 <= len(blob):
        n = struct.unpack_from(">I", blob, pos)[0]
        tag = blob[pos + 4:pos + 8]
        body = blob[pos + 8:pos + 8 + n]
        if len(body) != n or pos + 12 + n > len(blob):
            raise ValueError("Truncated Portal PNG chunk")
        if binascii.crc32(tag + body) & 0xffffffff != struct.unpack_from(">I", blob, pos + 8 + n)[0]:
            raise ValueError("Portal PNG CRC mismatch")
        if tag == b"IHDR":
            if body[8:] != bytes([8, color, 0, 0, 0]):
                raise ValueError("Only non-interlaced PNG RGBA8 or RGB8 is allowed")
        if tag == b"IDAT":
            chunks.append(body)
        pos += 12 + n
        if tag == b"IEND":
            break
    if not chunks:
        raise ValueError("Missing Portal PNG pixels")
    stride = bpp * width
    limit = (stride + 1) * width
    decoder = zlib.decompressobj()
    decompressed = decoder.decompress(b"".join(chunks), limit + 1)
    if decoder.unconsumed_tail or not decoder.eof or len(decompressed) != limit:
        raise ValueError("Wrong Portal PNG pixel buffer length")
    result = bytearray(width * stride)
    previous = bytes(stride)
    for y in range(width):
        offset = y * (stride + 1)
        filt = decompressed[offset]
        line = bytearray(decompressed[offset + 1:offset + 1 + stride])
        if filt not in range(5):
            raise ValueError("Invalid Portal PNG filter")
        for i in range(stride):
            left = line[i - bpp] if i >= bpp else 0
            above = previous[i]
            upper_left = previous[i - bpp] if i >= bpp else 0
            if filt == 1:
                line[i] = (line[i] + left) & 255
            elif filt == 2:
                line[i] = (line[i] + above) & 255
            elif filt == 3:
                line[i] = (line[i] + (left + above) // 2) & 255
            elif filt == 4:
                predictor = left + above - upper_left
                distances = (abs(predictor - left), abs(predictor - above),
                             abs(predictor - upper_left))
                selected = (left, above, upper_left)[distances.index(min(distances))]
                line[i] = (line[i] + selected) & 255
        result[y * stride:(y + 1) * stride] = line
        previous = line
    if bpp == 3:
        converted = bytearray(width * width * 4)
        for index in range(width * width):
            converted[index * 4:index * 4 + 3] = result[index * 3:index * 3 + 3]
            converted[index * 4 + 3] = 255
        return width, bytes(converted)
    return width, bytes(result)


def encode_rgba_png(width, pixels):
    if len(pixels) != width * width * 4:
        raise ValueError("PNG pixel count mismatch")
    def chunk(name, content):
        return (struct.pack(">I", len(content)) + name + content
                + struct.pack(">I", binascii.crc32(name + content) & 0xffffffff))
    rows = b"".join(b"\x00" + pixels[y * width * 4:(y + 1) * width * 4]
                    for y in range(width))
    ihdr = struct.pack(">IIBBBBB", width, width, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


@lru_cache(maxsize=16)
def safe_foreground(source):
    """Centre-scale Portal glyph inside the circular Android adaptive safe zone."""
    width, pixels = png_pixels(source)
    scale = 0.75
    output = bytearray(len(pixels))
    for y in range(width):
        sy = int((y + 0.5 - width / 2) / scale + width / 2)
        if not 0 <= sy < width:
            continue
        for x in range(width):
            sx = int((x + 0.5 - width / 2) / scale + width / 2)
            if 0 <= sx < width:
                dest = 4 * (y * width + x)
                start = 4 * (sy * width + sx)
                output[dest:dest + 4] = pixels[start:start + 4]
    return encode_rgba_png(width, bytes(output))


@lru_cache(maxsize=16)
def opaque_background(source):
    """Preserve approved artwork over an opaque Portal base; no mask holes."""
    width, pixels = png_pixels(source)
    output = bytearray(pixels)
    base = (23, 21, 35)  # Portal #171523, as approved in SVG background.
    for offset in range(0, len(output), 4):
        alpha = output[offset + 3]
        for channel in range(3):
            output[offset + channel] = (
                output[offset + channel] * alpha + base[channel] * (255 - alpha) + 127
            ) // 255
        output[offset + 3] = 255
    return encode_rgba_png(width, bytes(output))


def assert_adaptive_safe_zone(png):
    size, rgba = png_pixels(png)
    # Circle inscribed in Android's guaranteed central 66dp of a 108dp icon;
    # allow 0 alpha outside, not merely visually negligible pixels.
    radius_sq = (size * 33 / 108) ** 2
    for y in range(size):
        for x in range(size):
            if rgba[(y * size + x) * 4 + 3] and (
                (x + 0.5 - size / 2) ** 2 + (y + 0.5 - size / 2) ** 2
            ) > radius_sq:
                raise ValueError("Portal foreground exceeds Android adaptive safe circle")

def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def png_size(data):
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Invalid PNG signature/header")
    width, height = struct.unpack(">II", data[16:24])
    if not 16 <= width <= 1024 or width != height:
        raise ValueError("Portal icons must be square PNGs in the approved size range")
    if data[25] != 6:  # RGBA: transparency for the adaptive foreground.
        raise ValueError("Portal artwork must preserve RGBA transparency")
    return width


def approved_assets():
    files = {}
    for name, expected_blob in SOURCE_BLOBS.items():
        data = (ICON_ROOT / name).read_bytes()
        if git_blob(data) != expected_blob:
            raise ValueError("Unapproved or corrupted Portal asset: " + name)
        if name.endswith(".png"):
            actual = png_size(data)
            desired = int(name.removesuffix(".png").rsplit("-", 1)[-1])
            if actual != desired:
                raise ValueError("Portal PNG dimensions changed: " + name)
        files[name] = data
    return files


def make_themed_vector(svg):
    namespace = {"s": "http://www.w3.org/2000/svg"}
    root = ET.fromstring(svg)
    paths = [node.attrib["d"] for node in root.findall(".//s:path", namespace)
             if node.get("fill") == "#FFFFFF"]
    if len(paths) != 1 or not paths[0].strip().startswith("M 177 760"):
        raise ValueError("Approved Archium monochrome outline was not found")
    path = re.sub(r"\s+", " ", paths[0]).strip()
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="108dp" android:height="108dp"\n'
        '    android:viewportWidth="1024" android:viewportHeight="1024">\n'
        '    <group android:translateX="179.2" android:translateY="179.2"\n'
        '        android:scaleX="0.65" android:scaleY="0.65">\n'
        f'        <path android:fillColor="#000000" android:pathData="{path}"/>\n'
        '    </group>\n'
        '</vector>\n'
    ).encode("utf-8")


def expected_resources():
    assets = approved_assets()
    resources = {}
    for density, (flat, foreground, background) in DENSITIES.items():
        prefix = f"{BASE}/mipmap-{density}"
        resources[f"{prefix}/app_icon.png"] = assets[flat]
        resources[f"{prefix}/layered_app_icon.png"] = safe_foreground(assets[foreground])
        resources[f"{prefix}/layered_app_icon_background.png"] = opaque_background(assets[background])
    # The original AndroidManifest.xml already references these official Chromium
    # drawable aliases. Do not modify the manifest or the app ID.
    resources["chrome/android/java/res_base/drawable/ic_launcher.xml"] = APP_XML.encode()
    resources["chrome/android/java/res_base/drawable/ic_launcher_round.xml"] = APP_XML.encode()
    resources[f"{BASE}/drawable/themed_app_icon.xml"] = make_themed_vector(
        assets["archium-monochrome-light.svg"])
    return resources


def safe_target(checkout, relative):
    target = checkout / relative
    if any((checkout / Path(*Path(relative).parts[:i])).is_symlink()
           for i in range(1, len(Path(relative).parts) + 1)):
        raise ValueError("Refusing symlink resource: " + relative)
    if not target.is_file() or not target.resolve().is_relative_to(checkout):
        raise ValueError("Missing/unsafe Chromium launcher resource: " + relative)
    return target


def overlay(checkout, *, check=False, verify=False):
    checkout = Path(checkout).resolve()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(checkout), *args],
                                       stderr=subprocess.STDOUT)
    if Path(os.fsdecode(git("rev-parse", "--show-toplevel")).strip()).resolve() != checkout:
        raise ValueError("Not a Chromium checkout root")
    if git("rev-parse", "HEAD").decode().strip() != REVISION:
        raise ValueError("Launcher overlay requires pinned Chromium revision")
    resources = expected_resources()
    previous = {}
    for relative, desired in resources.items():
        path = safe_target(checkout, relative)
        original = git("show", REVISION + ":" + relative)
        actual = path.read_bytes()
        if actual not in (original, desired):
            raise ValueError("Unrecognized checkout resource; preserving it: " + relative)
        if verify and actual != desired:
            raise ValueError("Archium Portal not installed: " + relative)
        previous[relative] = actual
    if not check and not verify:
        changed = []
        try:
            for relative, desired in resources.items():
                path = checkout / relative
                if previous[relative] == desired:
                    continue
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".archium-icon-",
                                                 delete=False) as staging:
                    staging.write(desired)
                    tmp = Path(staging.name)
                try:
                    os.chmod(tmp, path.stat().st_mode & 0o777)
                    os.replace(tmp, path)
                finally:
                    if tmp.exists():
                        tmp.unlink()
                changed.append(relative)
        except BaseException:
            for relative in reversed(changed):
                (checkout / relative).write_bytes(previous[relative])
            raise
        overlay(checkout, verify=True)
    print("ARCHIUM_PORTAL_RESOURCES=" + ("VERIFIED" if verify else "PREFLIGHT" if check else "INSTALLED")
          + f" paths={len(resources)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    overlay(args.checkout, check=args.check, verify=args.verify)


if __name__ == "__main__":
    main()
