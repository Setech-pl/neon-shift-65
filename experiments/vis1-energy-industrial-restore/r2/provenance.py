"""Bounded visual-history evidence; no historical builds or engine reruns."""
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT/'docs/checkpoints/vis1-energy-industrial-restore/r2'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    out = DOCS/'history'; out.mkdir(exist_ok=True)
    commits = ('51fefc0','11406cf','dea2fe5','62df88e','e7d87ed',
               'a7e2bbb','591dbf9','75ef080','4da3d73','5354212','d0be2b7','9dab436')
    chronology = [dict(commit=git('rev-parse',c).strip(),
        metadata=git('show','--no-patch','--format=%aI%n%cI%n%an <%ae>%n%B',c).strip())
        for c in commits]
    references = {}
    for prefix in ('build/renderer-qualification',
        'experiments/art2-four-area-themes','experiments/art2-neon-palettes',
        'experiments/art3-contextual-decoration',
        'experiments/eng1-action-semantics-and-campaign-memory-v5',
        'experiments/eng2-capture-publication-feasibility',
        'experiments/eng3-observed-input-3pal'):
        f = ROOT/prefix/'reference/prototype_assets.c'
        text = f.read_text()
        arrays = {n:bytes(map(int,re.findall(r'\d+',v))) for n,v in
            re.findall(r'const unsigned char (\w+)\[\] = \{(.*?)\};',text,re.S)}
        references[str(f.relative_to(ROOT))] = dict(sha256=digest(f.read_bytes()),
            arrays={n:dict(bytes=len(arrays[n]),sha256=digest(arrays[n]))
                    for n in ('scene_maps','gameplay_common')})
    assert len({v['sha256'] for v in references.values()}) == 1
    # Track the exact source blocks which affect the disputed visual changes.
    def read(name):return (ROOT/name).read_text()
    def block(t,start,end):return t[t.index(start):t.index(end)]
    snippets = {
        'a2-floor-wall':block(read('experiments/renderer-qualification/compile.py'),'def floors():','def device('),
        'a3-floor-wall':block(git('show','dea2fe5:experiments/renderer-a3/compile.py'),'def floors():','def device('),
        'a3-design':git('show','dea2fe5:docs/checkpoints/renderer-a3/design.md'),
        'a4-container':block(git('show','62df88e:experiments/renderer-a4/artwork.py'),'CONTAINER=','\ndef container_pixels')
            if 'CONTAINER=' in git('show','62df88e:experiments/renderer-a4/artwork.py')
            else git('show','62df88e:experiments/renderer-a4/artwork.py').split('# 8 logical pixels')[1],
        'art2-areas':git('show','e7d87ed:experiments/art2-four-area-themes/areas.json'),
        'art21-areas':git('show','a7e2bbb:experiments/art2-neon-palettes/areas.json'),
        'art3-decoration':git('show','591dbf9:experiments/art3-contextual-decoration/decoration.py'),
        'art3-design':git('show','591dbf9:docs/checkpoints/art3-contextual-decoration/design.md'),
    }
    for name,content in snippets.items():
        (out/(name+'.txt')).write_text(content.rstrip()+'\n')
    diff = ''.join(difflib.unified_diff(
        snippets['a2-floor-wall'].splitlines(True),snippets['a3-floor-wall'].splitlines(True),
        fromfile='frozen A2 compile.py',tofile='dea2fe5 A3 compile.py'))
    (out/'a2-to-a3-floor-wall.json').write_text(json.dumps(dict(
        format='Unmodified unified diff, JSON-escaped to preserve context whitespace',
        diff=diff),indent=2)+'\n')
    lineage = {}
    for name in ('decoration.py','artwork.py','themes.py','areas.json'):
        lineage[name] = {prefix:digest((ROOT/'experiments'/prefix/name).read_bytes())
            for prefix in ('art3-contextual-decoration','eng1-action-semantics-and-campaign-memory-v5',
                           'eng2-capture-publication-feasibility','eng3-observed-input-3pal')}
        if name != 'artwork.py':
            assert len(set(lineage[name].values())) == 1, (name,'different source')
    artwork_normalized = {}
    footer_references = {}
    for prefix in lineage['artwork.py']:
        text = read('experiments/'+prefix+'/artwork.py')
        pattern = r'experiments/[^\x27]+/reference/void-loader.json'
        ref = re.search(pattern,text)[0]
        footer_references[ref] = digest((ROOT/ref).read_bytes())
        artwork_normalized[prefix] = digest(re.sub(pattern,'PINNED/reference/void-loader.json',text).encode())
    assert len(set(artwork_normalized.values())) == len(set(footer_references.values())) == 1
    # Source compiler changes concern ENG code/path; compare the relevant
    # floor/wall definitions independently rather than assuming full identity.
    definitions = {}
    for prefix in ('art3-contextual-decoration','eng1-action-semantics-and-campaign-memory-v5',
                   'eng2-capture-publication-feasibility','eng3-observed-input-3pal'):
        definitions[prefix] = digest(block(read('experiments/'+prefix+'/compile.py'),
                                          'def cool(','def split(').encode())
    assert len(set(definitions.values())) == 1
    vocabulary = {c:git('rev-parse',c+':tools/scenes.py').strip()
                  for c in ('11406cf','dea2fe5','5354212','9dab436')}
    assert len(set(vocabulary.values())) == 1
    status_sources = {
        'A3':'docs/checkpoints/renderer-a3/owner-smoke.md',
        'A4':'docs/checkpoints/renderer-a4/report.md',
        'ART2':'docs/checkpoints/art2-four-area-themes/report.md',
        'ART2.1':'docs/checkpoints/art2-neon-palettes/report.md',
        'ART3':'docs/checkpoints/art3-contextual-decoration/checkpoint.json',
        'baseline':'docs/checkpoints/visual-baseline/index.md',
        'VIS1':'docs/checkpoints/vis1-energy-industrial-restore/report.md'}
    result = dict(method='Existing VIS1 findings + bounded source/history inspection; no historical builds',
        chronology=chronology,reference_copies=references,ART3_to_ENG3_source_identity=lineage,
        artwork_identity_except_pinned_path=artwork_normalized,footer_reference_identity=footer_references,
        floor_wall_device_definition_SHA256=definitions,industrial_vocabulary_git_blobs=vocabulary,
        owner_status_sources={k:dict(path=v,sha256=digest((ROOT/v).read_bytes())) for k,v in status_sources.items()},
        limits=['Full owner PNG not assigned to a source commit',
                'Pending/NOT_RUN is not proof that the owner never viewed a build',
                'CAMP1 absence in this checkout is not evidence of lost work',
                'Git author metadata does not identify the human/agent who decided each pixel change'])
    (out/'history.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS bounded provenance, reference identity and ART3→ENG3 visual source identity')


if __name__ == '__main__':
    main()
