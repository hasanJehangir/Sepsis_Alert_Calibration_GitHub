"""Prepare real case materials; no human assessments are populated."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import run_external as e

S=Path(__file__).resolve().parent
def run():
    out=S/'review';out.mkdir(exist_ok=True)
    cohort=pd.read_csv(S/'results_amended/external_cohort.csv')
    test=cohort[cohort.role=='test'].copy()
    negative=test[~test.septic].copy()
    negative['review_hash']=[hashlib.sha256(f'20261001|review|{i}'.encode()).hexdigest() for i in negative.id]
    # All test cases plus a deterministic, explicitly nonrepresentative audit sample.
    review=pd.concat([test[test.septic],negative.sort_values('review_hash').head(40)],ignore_index=True)
    review['order_hash']=[hashlib.sha256(f'20261001|order|{i}'.encode()).hexdigest() for i in review.id]
    review=review.sort_values('order_hash').reset_index(drop=True)
    review['review_id']=[f'R{i+1:03}' for i in range(len(review))]
    p=pd.read_csv(S/'data/eicu/patient.csv.gz')
    info=review[['review_id','stay_id','record_hours']].merge(p,left_on='stay_id',right_on='patientunitstayid',validate='one_to_one')
    info[['review_id','stay_id','age','gender','unittype','apacheadmissiondx','record_hours']].to_csv(out/'clinical_case_index.csv',index=False)
    review[['review_id','stay_id','septic','onset','role','start','stop']].to_csv(out/'case_reference_key.csv',index=False)
    x=np.load(S/'results_amended/native_numeric_features.npy',mmap_mode='r')
    hours=np.load(S/'results_amended/external_hours.npy')
    rows=[]
    for r in review.itertuples():
        sl=slice(int(r.start),int(r.stop));a=x[sl]
        observed=a[:,38:72].astype(bool)
        d=pd.DataFrame({'review_id':r.review_id,'stay_id':r.stay_id,'score_available_hour':hours[sl]})
        for j,ch in enumerate(e.PHYSIO):
            d[ch+'_observed_in_hour']=np.where(observed[:,j],a[:,j],np.nan)
            d[ch+'_last_available']=a[:,j]
        rows.append(d)
    pd.concat(rows,ignore_index=True).to_csv(out/'case_input_timelines.csv.gz',index=False)
    decisions=info[['review_id','stay_id']].copy()
    for col in ['reviewer_name','review_date','label_compatible','onset_mapping_compatible','unit_mapping_acceptable','availability_assumption_acceptable','comment','decision']:
        decisions[col]=''
    decisions.to_csv(out/'human_case_review_form.csv',index=False)
    record={'status':'PREPARED_FOR_HUMAN_REVIEW_NOT_REVIEWED','people':len(review),'test_cases_included':17,'test_negative_sample':40,'negative_sampling':'smallest SHA256(20261001|review|cohort_id); no selection by model scores','review_fields_populated':False,'clinical_adjudication_completed':False,'human_review_completed':False,'case_material_limit':'Pre-onset predictor timelines only; no full infection/SOFA evidence or source EHR. Not sufficient for clinical sepsis adjudication.'}
    (out/'review_material_status.json').write_text(json.dumps(record,indent=2))
    print('Prepared',len(review),'case packets; human assessments are blank.')

if __name__=='__main__':run()
