"""Package retained results and build a Colab entry point; no experiment selection."""
from pathlib import Path
import datetime, hashlib, json, tempfile, zipfile
import nbformat

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parent
WORKSPACE = ROOT.parent
ARCHIVE = WORKSPACE / 'Sepsis_Stage3_Research_Package.zip'
NOTEBOOK = WORKSPACE / 'Sepsis_Stage3_Colab.ipynb'
PREFIX = ROOT.name

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

selected = {}
def include(path):
    selected[path.relative_to(ROOT).as_posix()] = path

for name in ['requirements.txt', 'DATA_NOTICE.md']:
    include(ROOT / name)
for path in STAGE.rglob('*'):
    if not path.is_file() or '__pycache__' in path.parts or '.pytest_cache' in path.parts:
        continue
    if path.suffix in ['.py', '.md', '.json', '.csv', '.gz', '.png', '.pdf', '.tex', '.txt']:
        include(path)
for path in (ROOT / 'stage2/results').iterdir():
    if path.suffix in ['.csv', '.npz', '.json', '.png']:
        include(path)
for name in ['STAGE2_PROTOCOL.md', 'study_config.json', 'protocol_lock.json',
             'Stage2_Findings.md', 'NOVELTY_AUDIT.md']:
    include(ROOT / 'stage2' / name)
include(ROOT / 'stage2/cache/hours.npy')
manifest = {'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'scope': 'Frozen-input stage-three reproduction; original locked results retained',
            'external_validation_completed': False,
            'stage3_followup_is_exploratory': True,
            'files': {name: {'bytes': path.stat().st_size, 'sha256': sha(path)}
                      for name, path in sorted(selected.items())}}
manifest_bytes = json.dumps(manifest, indent=2).encode()
readme = (STAGE / 'REPRODUCE.md').read_bytes()
with zipfile.ZipFile(ARCHIVE, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    z.writestr(PREFIX + '/PACKAGE_MANIFEST.json', manifest_bytes)
    z.writestr(PREFIX + '/README.md', readme)
    for name, path in sorted(selected.items()):
        z.write(path, PREFIX + '/' + name)
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
    for name, spec in manifest['files'].items():
        content = z.read(PREFIX + '/' + name)
        assert len(content) == spec['bytes']
        assert hashlib.sha256(content).hexdigest() == spec['sha256']
    # Ensure the package carries every frozen input referenced by the original lock.
    lock = json.loads(z.read(PREFIX + '/stage3/followup_lock.json'))
    for name, digest in lock['inputs'].items():
        assert hashlib.sha256(z.read(PREFIX + '/' + name)).hexdigest() == digest

digest = sha(ARCHIVE)
intro = '''# Sepsis alert-policy follow-up: reproduce completed results

This notebook evaluates **frozen predictions** and needs only a CPU. It does not
train a new model or create external validation. The alert-policy section is
exploratory because the same Stage 2 test records had already been examined.
No CAPMI material is used.

1. Upload the supplied `Sepsis_Stage3_Research_Package.zip` in the next cell.
2. Run the dependency, check, comparison and reporting cells in order.
3. Download the updated CSV tables, figures and completion metadata.

Keep the original package unchanged. The notebook verifies its exact archive
hash and the manifest before running. A new run timestamp is expected;
models, partitions, thresholds and counts should reproduce. Python 3.12 was
used for the original local run. This notebook was validated locally but has
not been executed in a signed-in Colab session.
'''
upload = f'''from google.colab import files
from pathlib import Path
import hashlib, json, zipfile
uploaded = files.upload()
matches = [name for name in uploaded if name.endswith('.zip')]
if len(matches) != 1:
    raise ValueError('Upload exactly the supplied standalone Stage 3 ZIP.')
blob = uploaded[matches[0]]
expected_archive_sha256 = {digest!r}
if hashlib.sha256(blob).hexdigest() != expected_archive_sha256:
    raise ValueError('Archive differs from the supplied package. Use the original ZIP.')
archive = Path('/content/Sepsis_Stage3_Research_Package.zip')
archive.write_bytes(blob)
base = Path('/content/sepsis_stage3_run')
base.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
    for member in z.infolist():
        destination = (base / member.filename).resolve()
        if not destination.is_relative_to(base.resolve()):
            raise ValueError('Unsafe archive path.')
    z.extractall(base)
project = base / {PREFIX!r}
manifest = json.loads((project / 'PACKAGE_MANIFEST.json').read_text())
for name, spec in manifest['files'].items():
    path = project / name
    if path.stat().st_size != spec['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != spec['sha256']:
        raise ValueError('Package input differs: ' + name)
print('Verified', len(manifest['files']), 'files. Project:', project)
'''
install = '''import sys, subprocess
print('Runtime Python:', sys.version)
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r',
                str(project / 'requirements.txt')], check=True)
print('Dependencies installed. Continue to the checks below.')
'''
checks = '''subprocess.run([sys.executable, '-m', 'pytest', '-q', 'stage3/tests'],
               cwd=project, check=True)
'''
run = '''import os
run_env = dict(os.environ)
run_env['MPLCONFIGDIR'] = '/content/sepsis_stage3_matplotlib'
subprocess.run([sys.executable, 'stage3/run_followup.py'], cwd=project,
               env=run_env, check=True)
subprocess.run([sys.executable, 'stage3/report_followup.py'], cwd=project,
               env=run_env, check=True)
completion = json.loads((project / 'stage3/results/completed.json').read_text())
assert completion['policy_rows'] == 660
assert completion['paired_endpoint_rows'] == 144
assert completion['invariance_and_stage2_anchor_checks_passed'] is True
print('Completed:', completion['status'])
'''
preview = '''from IPython.display import display, Image, Markdown
display(Markdown((project / 'stage3/Stage3_Findings.md').read_text()))
display(Image(filename=str(project / 'stage3/results/alert_burden.png')))
display(Image(filename=str(project / 'stage3/results/workload_detection.png')))
'''
download = '''output = Path('/content/Sepsis_Stage3_Colab_Output.zip')
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted((project / 'stage3/results').rglob('*')):
        if path.is_file():
            z.write(path, path.relative_to(project).as_posix())
    z.write(project / 'stage3/Stage3_Findings.md', 'stage3/Stage3_Findings.md')
files.download(str(output))
'''
nb = nbformat.v4.new_notebook()
nb.metadata = {'kernelspec': {'display_name':'Python 3', 'language':'python', 'name':'python3'},
               'language_info': {'name':'python'},
               'colab': {'name': NOTEBOOK.name, 'provenance': []}}
nb.cells = [nbformat.v4.new_markdown_cell(intro), nbformat.v4.new_code_cell(upload),
            nbformat.v4.new_markdown_cell('## Install dependencies'),
            nbformat.v4.new_code_cell(install), nbformat.v4.new_markdown_cell('## Verify rule behavior'),
            nbformat.v4.new_code_cell(checks), nbformat.v4.new_markdown_cell('## Run the frozen-input benchmark'),
            nbformat.v4.new_code_cell(run), nbformat.v4.new_code_cell(preview),
            nbformat.v4.new_markdown_cell('## Save your rerun outputs'),
            nbformat.v4.new_code_cell(download),
            nbformat.v4.new_markdown_cell('''## Next research step

Read `stage3/SUBMISSION_READINESS.md` and `stage3/JOURNAL_CHECK.md` in the package.
The completed manuscript is a draft. A genuinely independent, authorized cohort
is the next research priority. Rerunning these same test records does not supply it.
Authorship, ethics determination and journal ranking/fees must be verified before
a submission decision. Free Q1 publication within 2-3 months is not guaranteed.
''')]
nbformat.validate(nb)
for i, cell in enumerate(nb.cells):
    if cell.cell_type == 'code': compile(cell.source, f'cell_{i}', 'exec')
nbformat.write(nb, NOTEBOOK)
receipt = {'archive': str(ARCHIVE), 'archive_bytes': ARCHIVE.stat().st_size,
           'archive_sha256': digest, 'included_manifest_files': len(selected),
           'archive_crc_and_all_hashes_verified': True,
           'notebook': str(NOTEBOOK), 'notebook_sha256': sha(NOTEBOOK),
           'notebook_schema_and_cells_validated': True,
           'signed_in_colab_execution_performed': False}
(WORKSPACE / 'stage3_delivery_receipt.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt, indent=2))
