"""Independent direct-crossing audit of all natural-duration main result rows.

Does not call the runner's endpoint/summary functions. Run after completion.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd

STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parent
OUT=STAGE/'results'

def main():
    completed=json.loads((OUT/'completed.json').read_text())
    assert completed['status']=='STAGE2_COMPLETED_RETROSPECTIVE_RESEARCH_ONLY'
    metadata=pd.read_csv(OUT/'cohort.csv')
    manifest=json.loads((ROOT/'manifest.json').read_text())
    pilots={r['site']+'_'+Path(r['name']).stem for r in manifest if r['role']=='pilot'}
    assert not set(metadata.id).intersection(pilots)
    assert metadata.id.is_unique and metadata.source_sha256.is_unique
    expected={r['site']+'_'+Path(r['name']).stem:r['role'] for r in manifest}
    assert all(expected[r.id]==r.role for r in metadata.itertuples())
    hours=np.load(STAGE/'cache/hours.npy',mmap_mode='r')
    metrics=pd.read_csv(OUT/'main_metrics.csv')
    metrics=metrics[metrics.cap=='natural']
    checked=0
    keys={'patient_false_alert_rate_count':'false','window6_sensitivity_count':'window',
          'first6_sensitivity_count':'first','early_first_fraction_count':'early',
          'window12_sensitivity_count':'window12','first12_sensitivity_count':'first12',
          'any_positive_alert_fraction_count':'anypositive'}
    for (source,model),rows in metrics.groupby(['source','model']):
        probabilities=np.load(OUT/f'{source}_{model}_predictions.npz')['probability']
        for site,policies in rows.groupby('test_site'):
            cases=metadata[(metadata.site==site)&(metadata.role=='test')]
            for row in policies.itertuples():
                threshold=np.inf if row.threshold_infinite else row.threshold
                counts={key:0 for key in keys.values()};negative_hours=0;negative_alert_hours=0
                for patient in cases.itertuples():
                    p=probabilities[int(patient.start):int(patient.stop)]
                    h=hours[int(patient.start):int(patient.stop)]
                    crossing=p>threshold
                    alerted=np.flatnonzero(crossing)
                    first=h[alerted[0]] if len(alerted) else None
                    if patient.septic:
                        window=(h>=patient.onset-6)&(h<patient.onset)
                        window12=(h>=patient.onset-12)&(h<patient.onset)
                        counts['window']+=int(np.any(crossing&window))
                        counts['window12']+=int(np.any(crossing&window12))
                        counts['first']+=int(first is not None and patient.onset-6<=first<patient.onset)
                        counts['first12']+=int(first is not None and patient.onset-12<=first<patient.onset)
                        counts['early']+=int(first is not None and first<patient.onset-6)
                        counts['anypositive']+=int(first is not None)
                    else:
                        counts['false']+=int(len(alerted)>0)
                        negative_hours+=len(p);negative_alert_hours+=int(crossing.sum())
                for column,key in keys.items():
                    assert counts[key]==getattr(row,column),(source,model,site,row.policy,column,counts[key],getattr(row,column))
                assert negative_hours==row.negative_hours
                assert negative_alert_hours==row.negative_alert_hours
                checked+=1
    receipt={'status':'PASSED','natural_duration_main_rows_checked':checked,
             'endpoint_count_checks':checked*len(keys),
             'hourly_denominator_and_crossing_checks':checked*2,
             'pilot_overlap':0,'cohort_records':len(metadata),
             'cohort_hashes_unique':True,'manifest_roles_preserved':True,
             'completed_signature':completed['signature'],
             'audit_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'scope':'Direct evaluation from hourly predictions; does not independently validate raw preprocessing, model training, or all capped/budget rows.'}
    (OUT/'independent_audit.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
