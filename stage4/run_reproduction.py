"""Rerun both locked evaluations without overwriting recorded provenance."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys,tempfile
import numpy as np
import pandas as pd

S=Path(__file__).resolve().parent
ROOT=S.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run():
    manifest=json.loads((S/'package_manifest.json').read_text())
    files=manifest['files']
    for name,record in files.items():
        p=ROOT/name
        if sha(p)!=record['sha256']:raise RuntimeError('Packaged file changed: '+name)
    output=S/'reproduction';output.mkdir(exist_ok=True)
    comparisons=[]
    with tempfile.TemporaryDirectory(prefix='sepsis-stage4-') as temp:
        for label,driver,folder in [('initial','run_external.py','results'),('amended','run_external_v2.py','results_amended')]:
            copy=Path(temp)/label
            for name in files:
                p=copy/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
            if label=='initial':
                proc=subprocess.run([sys.executable,'-m','pytest','-q','stage4/tests'],cwd=copy,capture_output=True,text=True)
                (output/'tests.log').write_text(proc.stdout+proc.stderr)
                if proc.returncode:raise RuntimeError('Adapter tests failed; see reproduction/tests.log')
                print(proc.stdout,flush=True)
            proc=subprocess.run([sys.executable,'-u','stage4/'+driver],cwd=copy,capture_output=True,text=True)
            (output/(label+'_run.log')).write_text(proc.stdout+proc.stderr)
            if proc.returncode:raise RuntimeError(label+' reproduction failed; see log')
            for name in ['external_policy_metrics.csv','external_discrimination.csv','external_cohort.csv','external_counts.csv','feature_availability.csv','channel_mapping_audit.csv','external_exclusions.csv','label_window_audit.csv','outcome_blind_people_selection.csv']:
                expected=pd.read_csv(S/folder/name);actual=pd.read_csv(copy/'stage4'/folder/name)
                pd.testing.assert_frame_equal(expected,actual,check_exact=True)
                comparisons.append({'run':label,'file':name,'comparison':'exact dataframe match','passed':True})
            for p in sorted((S/folder).glob('*_predictions.npz')):
                expected=np.load(p)['probability'];actual=np.load(copy/'stage4'/folder/p.name)['probability']
                np.testing.assert_array_equal(expected,actual)
                comparisons.append({'run':label,'file':p.name,'comparison':'exact prediction-vector match','passed':True})
            for name in ['external_hours.npy','external_labels.npy','native_numeric_features.npy','mask_ambiguous_units_features.npy']:
                expected=np.load(S/folder/name);actual=np.load(copy/'stage4'/folder/name)
                np.testing.assert_array_equal(expected,actual)
                comparisons.append({'run':label,'file':name,'comparison':'exact array match','passed':True})
            print(label,': numerical tables, 12 prediction vectors and feature arrays reproduced exactly.',flush=True)
    record={'status':'BOTH_EXTERNAL_RUNS_REPRODUCED_EXACTLY','completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'packaged_files_verified':len(files),'comparisons':comparisons,'original_output_files_overwritten':False,'human_review_completed':False,'verified_hospital_patient_independence':False}
    (output/'verification.json').write_text(json.dumps(record,indent=2))
    print('Saved reproduction/verification.json',flush=True)

if __name__=='__main__':run()
