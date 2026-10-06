"""Build a self-contained Colab notebook from the checked study source."""
from pathlib import Path
import base64, hashlib, io, zipfile
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'experiment.py', 'download_data.py', 'manifest.json', 'requirements.txt',
    'PROTOCOL.md', 'DATA_NOTICE.md', 'tests/test_experiment.py',
    'stage2/STAGE2_PROTOCOL.md', 'stage2/study_config.json',
    'stage2/protocol_lock.json', 'stage2/run_stage2.py',
    'stage2/report_stage2.py', 'stage2/audit_results.py', 'stage2/tests/test_stage2.py',
    'stage2/NOVELTY_AUDIT.md', 'stage2/README_STAGE2.md',
]
payload = io.BytesIO()
with zipfile.ZipFile(payload, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in FILES:
        archive.write(ROOT / name, name)
raw = payload.getvalue()
encoded = base64.b64encode(raw).decode()
digest = hashlib.sha256(raw).hexdigest()

nb = nbf.v4.new_notebook()
md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
nb.cells = [
    md('''# Full sepsis alert-calibration study — reproducible CPU workflow

This notebook reproduces an independent public-data study of patient-level false-alert calibration across hospitals A and B in PhysioNet Challenge 2019. **It does not use CAPMI.** All 3,000 pilot records are excluded from stage-2 fitting, calibration, and evaluation; their public raw files are downloaded only to screen exact duplicates.

The fixed plan includes both transfer directions, three model variants, local calibration budgets of 100/250/500 completed admissions with 20 fixed samples, and observation-duration analyses. Read the embedded protocol and novelty audit before interpreting results. This is retrospective research, not a validated clinical system or an established novel algorithm.

**Use:** upload this `.ipynb` to [Google Colab](https://colab.research.google.com/), choose a CPU runtime, then run the cells in order. No Google Drive connection is required. The study downloads 40,336 small public files and can take substantial CPU/network time. A Colab disconnect can erase temporary files: download the output archive when finished. A saved output archive contains raw data and fitted models, but rebuilding the feature cache is required to resume a fresh runtime. This notebook has no fabricated execution outputs; the supplied results archive contains the actual completed local run.'''),
    code('''from pathlib import Path
import base64, hashlib, io, os, subprocess, sys, zipfile

# Change this to a persistent location before running if desired.
ROOT = Path('/content/Sepsis_Stage2_20260929') if Path('/content').exists() else Path.cwd() / 'Sepsis_Stage2_20260929'
ROOT.mkdir(parents=True, exist_ok=True)
'''+f"PAYLOAD = {encoded!r}\nEXPECTED_SHA256 = {digest!r}\n"+'''
raw = base64.b64decode(PAYLOAD)
assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    for info in archive.infolist():
        destination = (ROOT / info.filename).resolve()
        if not destination.is_relative_to(ROOT.resolve()):
            raise RuntimeError('Unsafe archive path')
        data = archive.read(info)
        if destination.exists() and destination.read_bytes() != data:
            raise RuntimeError(f'Existing source differs: {destination}. Preserve that run and choose a new ROOT.')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
print('Study folder:', ROOT)
print((ROOT / 'stage2/STAGE2_PROTOCOL.md').read_text())'''),
    md('''## Install the pinned environment and check the implementation

Dependencies are installed into the study folder to avoid relying on Colab's changing preinstalled versions. Commands run in new Python processes with that environment. Completed model/cache signatures also include Python and package versions; a version mismatch must not be bypassed.'''),
    code('''PACKAGES = ROOT / '.packages'
subprocess.run([sys.executable, '-m', 'pip', 'install', '--target', str(PACKAGES),
                '-r', str(ROOT / 'requirements.txt')], check=True)
ENV = os.environ.copy()
ENV['PYTHONPATH'] = os.pathsep.join([str(PACKAGES), str(ROOT)])

def run(*args):
    subprocess.run([sys.executable, '-u', *args], cwd=ROOT, env=ENV, check=True)

run('-m', 'pytest', '-q', 'tests', 'stage2/tests')'''),
    md('''## Download the public records

The downloader skips existing valid files and retries missing files. Re-run this cell after a download interruption. Records are used under the dataset's CC BY 4.0 license; see `DATA_NOTICE.md`. Do not upload private patient data to this notebook.'''),
    code("run('download_data.py')\nrun('download_data.py', '--full')"),
    md('''## Run the prespecified study

This creates the feature cache, fits six models, then evaluates every policy. It reuses completed compatible checkpoints. Do not tune parameters after reading these test results and describe a rerun as an unseen test. The original lock is a local pre-test specification, **not a public preregistration**.'''),
    code("run('stage2/run_stage2.py', '--stage', 'all')\nrun('stage2/audit_results.py')\nrun('stage2/report_stage2.py')"),
    md('''## Read the actual results

Patient false-alert rate means the fraction of nonseptic admissions with at least one alert. `window6_sensitivity` allows any alert in the six-hour pre-onset window; `first6_sensitivity` requires the first alert to fall in that window. Earlier first alerts are reported separately. These different endpoints must not be conflated.'''),
    code('''import json
completion = json.loads((ROOT / 'stage2/results/completed.json').read_text())
assert completion['status'] == 'STAGE2_COMPLETED_RETROSPECTIVE_RESEARCH_ONLY'
print(json.dumps(completion, indent=2))
from IPython.display import Markdown, Image, display
display(Markdown((ROOT / 'stage2/Stage2_Findings.md').read_text()))
display(Image(filename=str(ROOT / 'stage2/results/transfer_comparison.png')))
display(Image(filename=str(ROOT / 'stage2/results/calibration_budgets.png')))'''),
    md('''## Download a reusable results archive

The archive includes public raw records, source, locked plan, fitted models, results, and figures. It omits rebuildable feature arrays and installed dependencies. Keep this file after the runtime ends. A completed run supports a research assessment; it does not imply journal acceptance or clinical benefit.'''),
    code('''output = ROOT.parent / 'Sepsis_Stage2_Colab_Results.zip'
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in {'.packages', '__pycache__', 'cache', 'literature', '.pytest_cache'} for part in rel.parts):
            continue
        archive.write(path, Path('Sepsis_Alert_Calibration') / rel)
print(output, 'bytes:', output.stat().st_size)
try:
    from google.colab import files
except ImportError:
    from IPython.display import FileLink
    display(FileLink(str(output)))
else:
    files.download(str(output))'''),
]
nb.metadata = {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
               'language_info': {'name': 'python', 'version': '3.12'},
               'colab': {'name': 'Sepsis_Stage2.ipynb', 'provenance': []}}
nbf.validate(nb)
target = ROOT.parent / 'Sepsis_Stage2.ipynb'
nbf.write(nb, target)
print(target, target.stat().st_size)
