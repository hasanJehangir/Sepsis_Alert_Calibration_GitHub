"""Audit presentation inputs and reported numerical claims without changing results."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT=Path(__file__).resolve().parent
D=ROOT/'results'
checks=[]
def check(name, condition, details=None):
    checks.append({'check':name,'passed':bool(condition),'details':details})

main=pd.read_csv(D/'main_metrics.csv')
pol=pd.read_csv(D/'cross_hospital_local10.csv')
ext=pd.read_csv(D/'all_external_policy_metrics.csv')
disc=pd.read_csv(D/'discrimination.csv')
edisc=pd.read_csv(D/'all_external_discrimination.csv')
cohort=pd.read_csv(D/'cohort_counts.csv')
check('Challenge cohort total',cohort.patients.sum()==36658)
check('Challenge test cases and admissions',
      cohort.query("role == 'test'").sepsis.sum()==414 and
      cohort.query("role == 'test'").patients.sum()==7309)
check('Preserved complete policy comparisons',
      len(pd.read_csv(D/'policy_metrics.csv'))==660 and len(ext)==360 and len(edisc)==24)

for name,frame in [('Challenge primary',main),('Policy follow-up',pol),('External',ext)]:
    for endpoint,denom in [('patient_false_alert_rate','nonseptic_patients'),
                           ('window6_sensitivity','septic_patients'),
                           ('first6_sensitivity','septic_patients')]:
        nn=frame[denom].to_numpy(); kk=frame[endpoint+'_count'].to_numpy()
        valid=nn>0
        check(name+' '+endpoint+' count/rate consistency',
              np.all((kk>=0)&(kk<=nn)) and
              np.allclose(frame.loc[valid,endpoint],kk[valid]/nn[valid],atol=1e-12))
        low=np.zeros(len(frame));high=np.ones(len(frame))
        mask=(kk>0)&valid; low[mask]=beta.ppf(.025,kk[mask],nn[mask]-kk[mask]+1)
        mask=(kk<nn)&valid;high[mask]=beta.ppf(.975,kk[mask]+1,nn[mask]-kk[mask])
        check(name+' '+endpoint+' exact 95% intervals',
              np.allclose(frame.loc[valid,endpoint+'_ci_low'],low[valid],atol=1e-10) and
              np.allclose(frame.loc[valid,endpoint+'_ci_high'],high[valid],atol=1e-10))
    check(name+' first-window count cannot exceed any-window count',
          (frame.first6_sensitivity_count<=frame.window6_sensitivity_count).all())

sel=main.query("model == 'hgb' and cap == 'natural' and transfer == True")
expected={('A','source_hourly'):(794,86,15),('A','source_patient'):(261,66,8),
          ('A','target_patient_all'):(362,69,8),('B','source_hourly'):(2064,216,27),
          ('B','source_patient'):(1066,153,19),('B','target_patient_all'):(380,94,20)}
for (source,policy),counts in expected.items():
    r=sel.query('source == @source and policy == @policy').iloc[0]
    found=tuple(int(r[x+'_count']) for x in ['patient_false_alert_rate','window6_sensitivity','first6_sensitivity'])
    check(f'Main transport {source} {policy}',found==counts,{'counts':found})

for source,expected_counts in [('A',[4093,362,1298,962,5145]),('B',[1736,380,737,615,2915])]:
    hf=pol.query("model == 'hgb' and source == @source")
    policies=['hourly','single','silence4','silence6','three_of_five']
    rows=[hf.query('policy == @p').iloc[0] for p in policies]
    check('Emission counts '+source,[int(r.nonseptic_alerts) for r in rows]==expected_counts)
    check('Suppression preserves exposure and first timing '+source,
          all(r.patient_false_alert_rate_count==rows[0].patient_false_alert_rate_count and
              r.first6_sensitivity_count==rows[0].first6_sensitivity_count for r in rows[1:4]))
    check('Single any-window equals first-window '+source,
          rows[1].window6_sensitivity_count==rows[1].first6_sensitivity_count)
    red=100*(1-rows[2].nonseptic_alerts/rows[0].nonseptic_alerts)
    check('Reported four-hour reduction '+source,round(red,1)==(68.3 if source=='A' else 57.5))

expected_ext={('Initial','A','source_patient'):(122,3,0),
              ('Initial','A','local_patient'):(42,1,1),
              ('Initial','B','source_patient'):(122,4,1),
              ('Initial','B','local_patient'):(37,0,0),
              ('Amended exploratory','A','source_patient'):(128,5,2),
              ('Amended exploratory','A','local_patient'):(47,0,0),
              ('Amended exploratory','B','source_patient'):(131,6,3),
              ('Amended exploratory','B','local_patient'):(38,1,1)}
for (run,source,condition),counts in expected_ext.items():
    r=ext.query("model == 'hgb' and input_variant == 'native_numeric' and policy == 'hourly' and run == @run and source == @source and condition == @condition").iloc[0]
    found=tuple(int(r[x+'_count']) for x in ['patient_false_alert_rate','window6_sensitivity','first6_sensitivity'])
    check(f'External {run}/{source}/{condition}',found==counts and r.nonseptic_patients==444 and r.septic_patients==17)

check('All external test-hour denominators',
      (edisc.test_hours==19645).all() and np.allclose(edisc.hourly_positive_prevalence,102/19645))
check('Reported native external AUROC ranges',
      [(round(f.hourly_auroc.min(),3),round(f.hourly_auroc.max(),3))
       for _,f in edisc.query("input_variant == 'native_numeric'").groupby('run',sort=False)]
      ==[(.456,.627),(.476,.644)])

pair=pd.read_csv(D/'paired_differences.csv')
expected_pairs={'false_alert':(-20.0,-21.4,-18.6),'window6':(-22.7,-28.1,-17.7),'first6':(.4,-3.8,4.6)}
for endpoint,expected in expected_pairs.items():
    r=pair.query("source == 'B' and model == 'hgb' and transfer == True and cap == 'natural' and comparison == 'local_minus_source_patient' and endpoint == @endpoint").iloc[0]
    actual=tuple(round(100*r[x],1) for x in ['difference','ci_low','ci_high'])
    check('Paired local minus source numerical result '+endpoint,actual==expected,{'percentage_points':actual})
check('Manuscript uses directly rounded paired false-alert difference, not difference of rounded rates',
      '$-20.0$ percentage points' in (ROOT/'Sepsis_Alert_Transport_Manuscript.tex').read_text())

ledger=json.loads((ROOT/'Reference_Verification.json').read_text())
bib=(ROOT/'references.bib').read_text()
keys=set(re.findall(r'@\w+\{([^,]+)',bib))
cited=set()
for f in [ROOT/'Sepsis_Alert_Transport_Manuscript.tex',ROOT/'Supplementary_Material.tex',*list((ROOT/'tables').glob('*.tex'))]:
    for c in re.findall(r'\\cite\{([^}]+)\}',f.read_text()): cited.update(c.split(','))
check('All 21 bibliography entries verified',len(ledger)==21 and len(keys)==21 and all(r['status']=='verified' for r in ledger))
check('No missing or unused bibliography entries',keys==cited,{'unresolved':sorted(cited-keys),'unused':sorted(keys-cited)})
check('Twenty distinct DOI entries plus one proceedings reference',len(set(r['doi'].lower() for r in ledger if 'doi' in r))==20)
manifest=json.loads((ROOT/'result_provenance.json').read_text())
check('Frozen result file identities',all(hashlib.sha256((D/n).read_bytes()).hexdigest()==m['sha256'] for n,m in manifest.items()))
for name in ['Sepsis_Alert_Transport_Manuscript','Supplementary_Material']:
    log=(ROOT/(name+'.log')).read_text(errors='replace')
    check(name+' compile has no unresolved citations/references, fatal or overflow errors',
          not re.search(r'undefined|Overfull|Fatal error|^!',log,re.M))
report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL',
        'checks_count':len(checks),'checks':checks,
        'scope':'Presentation/numerical consistency audit; not independent model validation, clinical adjudication, or formal human peer review.'}
(ROOT/'Manuscript_Audit.json').write_text(json.dumps(report,indent=2))
print(report['status'],report['checks_count'],'checks')
for c in checks:
    if not c['passed']: print('FAILED',c['check'],c['details'])
if report['status']!='PASS':raise SystemExit(1)
