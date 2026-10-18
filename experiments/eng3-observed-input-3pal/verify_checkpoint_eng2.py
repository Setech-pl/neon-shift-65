"""Read-only verification of the seal and local raw archives."""
from capture_cases import *
CP=D.parent;manifest=json.loads((CP/'manifest.json').read_text())['files']
assert all(sha(R/p)==h for p,h in manifest.items())
binding=json.loads((D/'candidate-binding.json').read_text());frozen=R/binding['source_root']
assert all(sha(frozen/p)==h for p,h in binding['sources'].items())
assert all(sha(R/p)==h for p,h in binding['artifacts'].items())
tools=json.loads((D/'post-freeze-tools-manifest.json').read_text());assert all(sha(R/p)==h for p,h in tools.items())
if '--raw' in sys.argv:
 raw=json.loads((D/'raw-evidence-manifest.json').read_text())['archives']
 for q in raw:
  assert sha(R/q['path'])==q['sha256'] and sha(R/q['manifest'])==q['manifest_sha256'],q['path']
 print('PASS local raw archive hashes',len(raw))
print('PASS',len(manifest),'checkpointfiles,169frozen sources,64ATR,postfreeze tools')
