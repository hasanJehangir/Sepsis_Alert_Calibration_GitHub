"""Package completed study outputs without transient caches or third-party full text."""
from pathlib import Path
import hashlib, json, zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'stage2/results'
EXCLUDED = {'cache', '__pycache__', '.pytest_cache', 'literature'}

def main():
    completion = json.loads((OUT / 'completed.json').read_text())
    assert completion['status'] == 'STAGE2_COMPLETED_RETROSPECTIVE_RESEARCH_ONLY'
    data = sorted((ROOT / 'data').rglob('*.psv'))
    assert len(data) == 40336, len(data)
    files = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED for part in rel.parts):
            continue
        files.append((path, Path(ROOT.name) / rel))
    notebook = ROOT.parent / 'Sepsis_Stage2.ipynb'
    files.append((notebook, Path(notebook.name)))
    inventory = [{'path': str(name), 'bytes': path.stat().st_size,
                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                 for path, name in files]
    target = ROOT.parent / 'Sepsis_Stage2_Results.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path, name in files:
            archive.write(path, name)
        archive.writestr('ARCHIVE_INVENTORY.json', json.dumps(inventory, indent=2))
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
    receipt = {'archive': str(target), 'bytes': target.stat().st_size,
               'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
               'files': len(files), 'public_records': len(data),
               'completed_at_utc': completion['completed_at_utc']}
    (ROOT.parent / 'stage2_archive_receipt.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
