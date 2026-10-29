"""Real published RecyclerView runtime for the isolated footer lifecycle probe.

AAR class jars are unmodified. R constants are generated from each AAR's own R.txt;
there is no app resource linking in this Config.NONE Robolectric probe.
"""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile

ARTIFACTS = [
    ('androidx.core.ktx', 'androidx/core/core-ktx/1.13.0/core-ktx-1.13.0.aar', '59c54e6129e9261c6d810f8eea4a6ee2f4994d8162b1cd9fc88c9c84c92accfc'),
    ('androidx.recyclerview', 'androidx/recyclerview/recyclerview/1.4.0/recyclerview-1.4.0.aar', '0f32ccaffcda74c3f87f0b4cfe6ae78e8aa4eb3ad7dda4f2edf06eedc947a5cf'),
    ('androidx.core', 'androidx/core/core/1.13.0/core-1.13.0.aar', '1b96c8eb10c4b40283fdd6e9aa74ffff05fae4f15d54f61ba69d517fcd144695'),
    ('androidx.customview', 'androidx/customview/customview/1.0.0/customview-1.0.0.aar', '20e5b8f6526a34595a604f56718da81167c0b40a7a94a57daa355663f2594df2'),
    ('androidx.customview.poolingcontainer', 'androidx/customview/customview-poolingcontainer/1.0.0/customview-poolingcontainer-1.0.0.aar', '3584102fc49bf399c56e3b7be4bfe12000c46112320cd8cf85cc0a8f93f3e752'),
    ('', 'androidx/collection/collection-jvm/1.4.2/collection-jvm-1.4.2.jar', '984ce9bd780055eafb8a105aca3f514686bf7b1b6272ec7c645a98ce40fc7db4'),
    ('', 'org/jetbrains/kotlin/kotlin-stdlib/1.9.24/kotlin-stdlib-1.9.24.jar', '858b902696da9cf585ab9d98ffc1c2712269828354dfe9107e3711b084a36468'),
]


def prepare(work):
    """Return class jars and generated R sources; downloads are hash checked and cached."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    jars, sources = [], []
    resource_id = 0x7f010000
    for package, path, expected in ARTIFACTS:
        artifact = work / path.rsplit('/', 1)[1]
        if not artifact.exists() or hashlib.sha256(artifact.read_bytes()).hexdigest() != expected:
            base = 'https://repo.maven.apache.org/maven2/' if path.startswith('org/') else 'https://dl.google.com/dl/android/maven2/'
            with urllib.request.urlopen(base + path, timeout=30) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('Footer AndroidX artifact checksum mismatch: ' + path)
            artifact.write_bytes(data)
        if not package:
            jars.append(artifact)
            continue
        archive = zipfile.ZipFile(io.BytesIO(artifact.read_bytes()))
        jar = artifact.with_suffix('.jar')
        jar.write_bytes(archive.read('classes.jar'))
        jars.append(jar)
        groups = {}
        for line in archive.read('R.txt').decode().splitlines():
            kind, group, name, value = line.split(' ', 3)
            if group != 'styleable':
                resource_id += 1
                value = hex(resource_id)
            groups.setdefault(group, []).append(f'public static final {kind} {name} = {value};')
        source = work / package.replace('.', '/') / 'R.java'
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('package ' + package + '; public final class R {' + ''.join(
            'public static final class ' + group + '{' + ''.join(fields) + '}'
            for group, fields in groups.items()) + '}')
        sources.append(source)
    return jars, sources
