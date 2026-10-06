"""Build a self-contained public-data external-evaluation package and notebook."""
from pathlib import Path
import hashlib,json,zipfile
import nbformat

S=Path(__file__).resolve().parent
ROOT=S.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
    chosen=set()
    for pattern in ['*.py','*.md','*.txt','*.csv']:
        chosen.update(S.glob(pattern))
    for name in ['config.json','external_lock.json','external_amended_lock.json','download_receipt.json','amended_download_receipt.json']:
        chosen.add(S/name)
    for folder in ['data','results','results_amended','review','figures','tests']:
        chosen.update(p for p in (S/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts)
    chosen.add(S/'reference/Sepsis_Calibration_Manuscript_Draft.pdf')
    chosen.add(ROOT/'experiment.py')
    chosen.add(ROOT/'stage3/run_followup.py');chosen.add(ROOT/'stage3/config.json')
    for name in ['policy_metrics.csv','paired_policy_differences.csv','invariance_audit.csv','cross_hospital_local10.csv','completed.json']:
        chosen.add(ROOT/'stage3/results'/name)
    for name in ['main_metrics.csv','completed.json']:
        chosen.add(ROOT/'stage2/results'/name)
    chosen.update((ROOT/'stage2/results').glob('*_model.joblib'))
    chosen.update((ROOT/'stage2/results').glob('*_model_info.json'))
    for p in chosen:assert p.is_file(),str(p)
    records={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(chosen)}
    manifest={'scope':'external public-demo evaluation; both original and exploratory amended runs','files':records,'human_review_completed':False,'verified_hospital_patient_independence':False}
    (S/'package_manifest.json').write_text(json.dumps(manifest,indent=2))
    archive=ROOT.parent/'Sepsis_Stage4_External_Review_Package.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(chosen):z.write(p,str(Path('Sepsis_Alert_Calibration')/p.relative_to(ROOT)))
        z.write(S/'package_manifest.json','Sepsis_Alert_Calibration/stage4/package_manifest.json')
    digest=sha(archive)
    notebook=nbformat.v4.new_notebook(cells=[
      nbformat.v4.new_markdown_cell('''# Reproduce the external eICU-demo evaluation

Upload `Sepsis_Stage4_External_Review_Package.zip` downloaded with this notebook. The original and post-test amended runs are preserved; the wrapper reruns each in an isolated copy and compares all results.

**Results were weak; actual human review and verified cross-resource independence are pending.** No CAPMI material is used. This is research code, not a bedside application. The notebook was validated locally, not executed in a signed-in Colab session. Python 3.12 is the verified environment.'''),
      nbformat.v4.new_code_cell('''from google.colab import files
from pathlib import Path
import hashlib, zipfile, json, subprocess, sys

uploaded = files.upload()
name = "Sepsis_Stage4_External_Review_Package.zip"
if name not in uploaded:
    raise ValueError("Upload the ZIP with that exact filename.")
archive = Path('/content') / name
archive.write_bytes(uploaded[name])
del uploaded
EXPECTED_SHA256 = "'''+digest+'''"
assert hashlib.sha256(archive.read_bytes()).hexdigest() == EXPECTED_SHA256, "Archive checksum differs."
destination = Path('/content/sepsis_stage4')
destination.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
    for member in z.infolist():
        target = (destination / member.filename).resolve()
        if not target.is_relative_to(destination.resolve()):
            raise ValueError('Unsafe archive path')
    z.extractall(destination)
project = destination / 'Sepsis_Alert_Calibration'
print('Verified and extracted:', project)
print('Python:', sys.version)'''),
      nbformat.v4.new_code_cell('''subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r',
                str(project / 'stage4/requirements_stage4.txt')], check=True)
print('Pinned dependencies installed. Subsequent computations run in fresh Python processes.')'''),
      nbformat.v4.new_code_cell('''subprocess.run([sys.executable, 'stage4/run_reproduction.py'], cwd=project, check=True)
record = json.loads((project / 'stage4/reproduction/verification.json').read_text())
print(record['status'])
print('Exact numerical checks:', len(record['comparisons']))
print('Human review completed:', record['human_review_completed'])
print('Verified cohort independence:', record['verified_hospital_patient_independence'])'''),
      nbformat.v4.new_code_cell('''files.download(str(project / 'stage4/reproduction/verification.json'))
files.download(str(project / 'stage4/External_Validation_Report.md'))
files.download(str(project / 'stage4/Human_Review_Packet.md'))'''),
      nbformat.v4.new_markdown_cell('''## Actual human review

Give the report, unchanged manuscript and packet to a sepsis/critical-care clinician and a human methods reviewer. The 57 case aids are pre-onset predictor timelines, not complete diagnostic charts. Reviewer fields are blank. Return the actual review comments before treating human review as complete.

The public data are ODbL 1.0; preserve attribution and applicable database share-alike terms. See the package README and DATA_ATTRIBUTION.md.''')
    ],metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}})
    nbformat.validate(notebook)
    for i,cell in enumerate(notebook.cells):
        if cell.cell_type=='code':compile(cell.source,f'cell_{i}','exec')
    nbpath=ROOT.parent/'Sepsis_Stage4_Colab.ipynb';nbformat.write(notebook,nbpath)
    info={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':digest,'files':len(records)+1,'notebook':str(nbpath),'notebook_sha256':sha(nbpath),'notebook_validated':True,'colab_session_executed':False}
    (ROOT.parent/'stage4_release.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))

if __name__=='__main__':run()
