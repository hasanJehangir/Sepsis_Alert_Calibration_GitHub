"""Create a self-contained Colab notebook from the verified pilot sources."""
from pathlib import Path
import base64, hashlib, io, json, zipfile
import nbformat as nbf

ROOT=Path(__file__).resolve().parent

def main():
    files=['download_data.py','experiment.py','plot_results.py','requirements.txt',
           'PROTOCOL.md','README.md','DATA_NOTICE.md','Project_Brief.md',
           'manifest.json','tests/test_experiment.py']
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name in files:archive.writestr(name,(ROOT/name).read_bytes())
    payload=buffer.getvalue();encoded=base64.b64encode(payload).decode()
    expected=hashlib.sha256(payload).hexdigest()
    notebook=nbf.v4.new_notebook()
    md=nbf.v4.new_markdown_cell;code=nbf.v4.new_code_cell
    notebook.cells=[
        md('''# Patient-level false-alert calibration for cross-hospital sepsis warning

**Independent research pilot for Hasan Jehangir · 29 September 2026**

This notebook reproduces a completed development experiment on 3,000 public PhysioNet records. It contains no CAPMI material. It is **not a finished paper, a clinical tool, or a confirmatory study**.

Use a **CPU runtime** and run the cells in order. No GPU, paid API, login to PhysioNet, or Drive connection is needed. The source code and deterministic split manifest are embedded below; the patient files are fetched from the official public dataset. Network speed controls most of the runtime.

**Verified locally:** 2,936 eligible patients, six methodological tests passed, and exact reproduction of the first pilot's thresholds and counts. The notebook structure is validated; it has not been run inside your Colab account.'''),
        md('''## 1. Restore the project source

This extracts the embedded, hash-checked source package into `Sepsis_Alert_Pilot_20260929`. It contains readable Python files, the protocol, data attribution, tests, and the fixed filename manifest. Existing source files with different contents cause an error so your edits are preserved. For a clean run, choose a new folder name.

The protocol is a restored development document written after the initial pilot findings were known. It is not a public preregistration.'''),
        code('''from pathlib import Path, PurePosixPath
import base64, hashlib, io, json, os, subprocess, sys, zipfile

BASE = Path('/content') if Path('/content').exists() else Path.cwd()
ROOT = BASE / 'Sepsis_Alert_Pilot_20260929'
ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ZIP_BASE64 = '''+repr(encoded)+'''
source_bytes = base64.b64decode(SOURCE_ZIP_BASE64)
assert hashlib.sha256(source_bytes).hexdigest() == '''+repr(expected)+'''
with zipfile.ZipFile(io.BytesIO(source_bytes)) as archive:
    for entry in archive.infolist():
        relative = PurePosixPath(entry.filename)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unexpected archive path')
        path = ROOT.joinpath(*relative.parts)
        content = archive.read(entry)
        if path.exists() and path.read_bytes() != content:
            raise RuntimeError(f'{path.name} differs from the packaged version. Use a new project folder.')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
print('Project:', ROOT)
print('Source files:', ', '.join(p.name for p in ROOT.glob('*.py')))
print('Protocol SHA-256:', hashlib.sha256((ROOT / 'PROTOCOL.md').read_bytes()).hexdigest())'''),
        md('''## 2. Install isolated CPU dependencies

Packages are installed in the project folder and used by new Python subprocesses. The notebook kernel's existing NumPy/Pandas imports do not need to be replaced. This may take several minutes on a fresh runtime.'''),
        code('''PACKAGES = ROOT / '.packages'
subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '--upgrade',
                '--target', str(PACKAGES), '-r', str(ROOT / 'requirements.txt')], check=True)
ENV = os.environ.copy()
ENV['PYTHONPATH'] = str(PACKAGES) + os.pathsep + str(ROOT)
ENV['MPLBACKEND'] = 'Agg'

def run_script(*arguments):
    process = subprocess.Popen([sys.executable, '-u', *arguments], cwd=ROOT,
                               env=ENV, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end='')
    if process.wait() != 0:
        raise RuntimeError(f'Command failed: {arguments}')

print('Dependencies installed. Experiment subprocesses use:', PACKAGES)'''),
        md('''## 3. Run the methodological checks

Checks cover causal features, rank calibration, tied scores, patient versus hourly metrics, pilot isolation, and the dataset's already-shifted six-hour labels.'''),
        code("run_script('-m', 'pytest', '-q', 'tests')"),
        md('''## 4. Download only the fixed 3,000-record pilot

Data: [PhysioNet/CinC Challenge 2019 v1.0.0](https://physionet.org/content/challenge-2019/1.0.0/), [DOI](https://doi.org/10.13026/v64v-d857), CC BY 4.0. Full citations are in `DATA_NOTICE.md`.

The remaining 37,336 filenames are reserved and are not downloaded or opened by this default workflow. Rerunning the downloader resumes successfully downloaded pilot files.'''),
        code("run_script('download_data.py')"),
        md('''## 5. Fit the fixed model and evaluate the three threshold policies

The model is fit only on hospital-A training patients. Source hourly and source patient thresholds use only A calibration patients; local patient calibration uses disjoint B calibration patients. Evaluation labels are not used for fitting or threshold selection. No model tuning is performed.

This reruns the development experiment and replaces files in `results/`. It is not an independent replication or the final reserved-data study.'''),
        code("run_script('experiment.py')\nrun_script('plot_results.py')"),
        md('''## 6. Inspect the measured results

Patient false-alert rate counts nonseptic patients with **any** eligible alert. Window sensitivity counts septic patients with **any** alert in the six hours before reconstructed onset. Timely-first-alert sensitivity requires the **first** eligible alert to fall in that window.

Hourly and patient calibration target different events. The reduction in patient false alerts is not a free improvement in discrimination; sensitivity and timing must be reported alongside it.'''),
        code('''from IPython.display import display, Markdown, Image
result = json.loads((ROOT / 'results' / 'pilot_results.json').read_text())
print('Included:', result['included_records'], '| Excluded:', result['excluded_records'])
print('Reserved records never loaded:', result['reserved_records_never_loaded'])
header = chr(10).join(['| Hospital | Policy | Patient false alerts | Window sensitivity | Timely first alert |', '|---|---|---:|---:|---:|', ''])
table = header
for row in result['results']:
    table += f"| {row['site']} | {row['policy']} | {row['patient_false_alert_rate']:.1%} ({row['false_alerted_patients']}/{row['nonseptic_patients']}) | {row['six_hour_window_sensitivity']:.1%} | {row['timely_first_alert_sensitivity']:.1%} |" + chr(10)
display(Markdown(table))
display(Image(filename=str(ROOT / 'results' / 'pilot_comparison.png')))
print('Full results:', ROOT / 'results' / 'pilot_results.json')'''),
        md('''## 7. Recorded reference result and interpretation

In the verified 29 September 2026 run, hospital-B patient false alerts were **490/1,136 (43.1%)**, **151/1,136 (13.3%)**, and **148/1,136 (13.0%)** under source-hourly, source-patient, and local-patient calibration. Window detections were **30/40**, **23/40**, and **23/40**. Timely first alerts were **2/40 for all three**.

These reference numbers are recorded development results, not outputs generated by this notebook unless you execute it. Small floating-point differences can arise across environments. Investigate material differences; do not edit outputs to force a match.

The findings do not establish useful clinical warning timing or a clear local-adaptation advantage. The patient conformal guarantee requires exchangeable calibration/test units and is marginal over those draws; it is not a blanket 10% bound after hospital transfer.

Before writing a final paper, implement and lock the larger two-direction study, local budgets, baseline comparisons, duration policies, and uncertainty analysis described in `PROTOCOL.md`. Novelty remains provisional. No journal acceptance or two-to-three-month publication promise is made.'''),
        md('''## 8. Download this run's outputs (optional)

This creates a compact archive of the run outputs and source, excluding the dependency directory and raw patient files. The patient data remain reproducible from the fixed manifest.'''),
        code('''OUTPUT = BASE / 'Sepsis_Pilot_Run_Outputs.zip'
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0] in {'.packages', 'data', '.pytest_cache', '__pycache__'} or '__pycache__' in relative.parts:
            continue
        archive.write(path, str(relative))
print('Saved:', OUTPUT)
try:
    from google.colab import files
    files.download(str(OUTPUT))
except ImportError:
    print('Outside Colab: download the archive from the notebook file browser.')''')
    ]
    notebook.metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},
                       'language_info':{'name':'python','version':'3.12'},
                       'colab':{'name':'Sepsis_Alert_Project.ipynb','provenance':[]}}
    nbf.validate(notebook)
    for i,cell in enumerate(notebook.cells):
        if cell.cell_type=='code':compile(cell.source,f'cell_{i}','exec')
    path=ROOT.parent/'Sepsis_Alert_Project.ipynb'
    nbf.write(notebook,path)
    print(path, path.stat().st_size, 'bytes; schema and all code cells validated')

if __name__=='__main__':main()
