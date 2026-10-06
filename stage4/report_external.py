"""Generate transparent external results and a separate arithmetic audit."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from scipy.special import betaincinv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

S=Path(__file__).resolve().parent
F=S/'figures';F.mkdir(exist_ok=True)
R=S/'review';R.mkdir(exist_ok=True)
LABELS={'logistic':'Logistic','hgb':'HGB full','hgb_no_observation_features':'HGB reduced'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def md(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
def interval(row,key):
    n=int(row.nonseptic_patients if key=='patient_false_alert_rate' else row.septic_patients)
    return f"{int(row[key+'_count'])}/{n}; {100*row[key]:.1f}% ({100*row[key+'_ci_low']:.1f}–{100*row[key+'_ci_high']:.1f})"

def audit():
    checks=[]
    keys=['patient_false_alert_rate','window6_sensitivity','first6_sensitivity','early_first_fraction','window12_sensitivity','first12_sensitivity','any_positive_alert_fraction']
    for run in ['results','results_amended']:
        m=pd.read_csv(S/run/'external_policy_metrics.csv')
        assert len(m)==180
        assert not m.duplicated(['source','model','input_variant','condition','policy']).any()
        for key in keys:
            for r in m.to_dict('records'):
                n=int(r['nonseptic_patients'] if key=='patient_false_alert_rate' else r['septic_patients']);k=int(r[key+'_count'])
                assert 0<=k<=n and np.isclose(r[key],k/n,rtol=0,atol=1e-12)
                lo=0. if k==0 else betaincinv(k,n-k+1,.025)
                hi=1. if k==n else betaincinv(k+1,n-k,.975)
                assert np.isclose(r[key+'_ci_low'],lo,rtol=0,atol=1e-12)
                assert np.isclose(r[key+'_ci_high'],hi,rtol=0,atol=1e-12)
            checks.append({'run':run,'check':key+' counts/proportions/exact intervals','rows_checked':len(m),'passed':True})
        for _,g in m.groupby(['source','model','input_variant','condition']):
            h=g[g.policy=='hourly'].iloc[0]
            for policy in ['single','silence4','silence6']:
                p=g[g.policy==policy].iloc[0]
                for key in ['threshold','patient_false_alert_rate_count','first6_sensitivity_count','early_first_fraction_count','any_positive_alert_fraction_count']:
                    assert h[key]==p[key],(run,policy,key)
                assert p.nonseptic_alerts<=h.nonseptic_alerts and p.septic_alerts<=h.septic_alerts
                if policy=='single':assert p.window6_sensitivity_count==p.first6_sensitivity_count
        checks.append({'run':run,'check':'first-alert and admission invariants for single/silence rules','rows_checked':36,'passed':True})
        c=pd.read_csv(S/run/'external_cohort.csv');hours=np.load(S/run/'external_hours.npy');labels=np.load(S/run/'external_labels.npy')
        assert c.person_id.is_unique and len(c)==656
        assert not set(c[c.role=='calibration'].person_id)&set(c[c.role=='test'].person_id)
        for r in c.itertuples():
            h=hours[int(r.start):int(r.stop)];y=labels[int(r.start):int(r.stop)]
            assert h[0]>=6 and np.all(np.diff(h)==1)
            if r.septic:assert np.all(h<r.onset) and y.sum()==6
            else:assert not y.any()
        checks.append({'run':run,'check':'unique people, disjoint roles, contiguous pre-onset scoring','rows_checked':len(c),'passed':True})
    for name in ['external_cohort.csv','external_counts.csv','outcome_blind_people_selection.csv','external_hours.npy','external_labels.npy','external_exclusions.csv','label_window_audit.csv']:
        assert sha(S/'results'/name)==sha(S/'results_amended'/name),name
        checks.append({'run':'both','check':'unchanged '+name,'rows_checked':1,'passed':True})
    for lockname in ['external_lock.json','external_amended_lock.json']:
        lock=json.loads((S/lockname).read_text())
        for rel,digest in lock['inputs'].items():assert sha(S.parent/rel)==digest,rel
        driver='run_external.py' if lockname=='external_lock.json' else 'run_external_v2.py'
        assert sha(S/driver)==lock['runner_sha256']
        checks.append({'run':lockname,'check':'frozen input and runner hashes unchanged','rows_checked':len(lock['inputs']),'passed':True})
    pd.DataFrame(checks).to_csv(R/'external_numerical_audit.csv',index=False)
    return checks

def plots(allmetrics):
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11.2,5.0),layout='constrained')
    colors={'source_patient':'#b45309','local_patient':'#166534'}
    names={'source_patient':'Frozen source patient threshold','local_patient':'External calibration threshold'}
    for ax,key,title in zip(axes,['patient_false_alert_rate','window6_sensitivity'],['Patients with false alerts (444 negatives)','Any alert in 6 h before event (17 cases)']):
        labels=[]
        for i,(run,source) in enumerate([('Initial','A'),('Initial','B'),('Amended exploratory','A'),('Amended exploratory','B')]):
            labels.append(f'{run}\n{source} → eICU demo')
            for cond,shift in [('source_patient',-.13),('local_patient',.13)]:
                r=allmetrics[(allmetrics.run==run)&(allmetrics.source==source)&(allmetrics.model=='hgb')&(allmetrics.input_variant=='native_numeric')&(allmetrics.policy=='hourly')&(allmetrics.condition==cond)].iloc[0]
                v=100*r[key];low=100*r[key+'_ci_low'];high=100*r[key+'_ci_high']
                ax.errorbar(v,i+shift,xerr=[[v-low],[high-v]],fmt='o',color=colors[cond],capsize=3,label=names[cond] if i==0 else None)
        ax.set_yticks(range(4),labels);ax.invert_yaxis();ax.set_xlabel('Percent; exact 95% binomial interval');ax.set_title(title);ax.grid(axis='x',alpha=.15)
        if key=='patient_false_alert_rate':ax.axvline(10,color='#64748b',ls='--',lw=1)
        ax.set_xlim(0,65 if key=='window6_sensitivity' else 40)
    handles,names=axes[1].get_legend_handles_labels()
    fig.legend(handles,names,loc='outside lower center',ncol=2,fontsize=9)
    fig.suptitle('Frozen full HGB models: external transport is weak and uncertain',fontsize=13)
    fig.savefig(F/'external_hgb_results.png',dpi=180);fig.savefig(F/'external_hgb_results.pdf');plt.close(fig)

def run():
    checks=audit()
    allm=pd.concat([pd.read_csv(S/f/'external_policy_metrics.csv').assign(run=r) for f,r in [('results','Initial'),('results_amended','Amended exploratory')]],ignore_index=True)
    alld=pd.concat([pd.read_csv(S/f/'external_discrimination.csv').assign(run=r) for f,r in [('results','Initial'),('results_amended','Amended exploratory')]],ignore_index=True)
    allm.to_csv(S/'all_external_policy_metrics.csv',index=False);alld.to_csv(S/'all_external_discrimination.csv',index=False)
    table=[]
    for r in allm[(allm.model=='hgb')&(allm.input_variant=='native_numeric')&(allm.policy=='hourly')&(allm.condition.isin(['source_patient','local_patient']))].to_dict('records'):
        r=pd.Series(r)
        table.append([r.run,r.source+' → demo','Source patient' if r.condition=='source_patient' else 'Local patient',interval(r,'patient_false_alert_rate'),interval(r,'window6_sensitivity'),interval(r,'first6_sensitivity')])
    anchor=md(['Run','Frozen model','Threshold','False-alert patients: k/n; % (95% CI)','Any alert in 6 h: k/n; % (95% CI)','First alert in 6 h: k/n; % (95% CI)'],table)
    discrimination=[]
    for (r,s,m),g in alld.groupby(['run','source','model'],sort=False):
        n=g[g.input_variant=='native_numeric'].iloc[0];a=g[g.input_variant=='mask_ambiguous_units'].iloc[0]
        discrimination.append([r,s,LABELS[m],f'{n.hourly_auroc:.3f}',f'{a.hourly_auroc:.3f}',f'{n.hourly_average_precision:.4f}',f'{a.hourly_average_precision:.4f}'])
    disc=md(['Run','Source','Model','AUROC native','AUROC masked','AP native','AP masked'],discrimination)
    coverage=[]
    for channel in ['Temp','FiO2']:
        row=[channel]
        for f in ['results','results_amended']:
            a=pd.read_csv(S/f/'feature_availability.csv');r=a[a.channel==channel].iloc[0]
            row.append(f'{int(r.observed_scoring_rows)}/28,045 ({100*r.observed_fraction:.1f}%)')
        coverage.append(row)
    report=f'''# External cohort evaluation and review status

The frozen Challenge-trained models were evaluated on an open eICU demo cohort, with all results retained. **Detection was weak. This is supplementary external evidence, not verified independent-cohort clinical validation. Human review has not occurred.** Neither a clinical benefit nor a high-performing deployable sepsis system is supported.

## Completed work

Six original models were scored without refitting, feature redesign or changing the source thresholds. Two prespecified numeric-unit variants, three threshold conditions and five alert rules produced 180 comparisons in the initial run. A documented post-result measurement amendment produced another 180 comparisons on exactly the same cohort. Neither run replaces the other. CAPMI materials were not accessed or reused. The existing manuscript and locked Challenge results remain unchanged.

The original external protocol was locally locked before reading external outcome values; this is not public preregistration. The amended run was planned after initial test results were inspected and is exploratory. Both locks, input hashes, original outcomes, amendment rationale and code are supplied.

## Cohort and comparability

The source is the openly released [eICU-CRD Demo v2.0.1](https://physionet.org/content/eicu-crd-demo/2.0.1/), with benchmark labels from [YAIB](https://github.com/rvandewater/YAIB), pinned to commit `0d1d39a131a65f453aeb019828394396d6bfd171`. Dataset access and reuse are governed by ODbL 1.0. The public demo is intended to illustrate reproducible processing and does not substitute for validating on the full database.

The benchmark provides 896 eligible stay identifiers. An outcome-blind hash chose one stay per person (677 people), followed by the fixed source eligibility rules (656 people; 21 early/left-censored exclusions). Person hashes assigned 195 people to calibration (8 cases, 187 negatives) and 461 to test (17 cases, 444 negatives), with zero person overlap between those roles. There are 28,045 total scoring hours and 19,645 test hours. All 17 test cases have six positive pre-event scoring hours; hourly prevalence is 102/19,645 = 0.519%.

No record was reseeded or moved to obtain favorable prevalence or performance. Observation ends at the earlier of discharge, the published label grid endpoint and 168 hours. Adults are scored after six complete ICU hours and strictly before reconstructed onset for cases. Early-onset sepsis is outside this estimand. YAIB upstream exclusions, including observation adequacy and hospital selection, can bias the sample.

**Cross-resource hospital/patient independence cannot be verified from deidentified public identifiers.** Calibration and test people are disjoint within this demo, but their hospitals are not held out from one another. The raw checksum-verified release contains 186 hospital surrogate IDs, whereas its overview describes 20 hospitals. Every patient ID joins to the hospital table; this discrepancy remains unresolved. No verified clinical hospital count is claimed.

## Target and measurement differences

YAIB's modified `sep3_alt` target uses an antibiotic-based suspected-infection proxy and a SOFA-change window that differs from the Challenge definition. Imported positive labels span an event-centered ±6-hour window, rather than the Challenge's persistent shifted label. We reconstruct the benchmark event grid from the first positive hour +6 and retain only pre-event scores. Positive blocks were checked for continuity and width. These are operational benchmark labels, **not clinician-adjudicated diagnoses or an independently recalculated Sepsis-3 reference standard**.

Raw eICU measurements were rebuilt causally: no future filling; an event is first used after its complete hourly bin; laboratory corrections use the later result/revision offset. Periodic `sao2` is mapped to peripheral O2Sat, with arterial SaO2 coming separately from laboratory O2 saturation. Noninvasive and invasive blood pressures share source channels. These choices and offset assumptions require clinical review.

Challenge's printed Lactate/Magnesium units conflict with the usual scale of their released numeric values. Both the native-numeric mapping and a prespecified variant masking those two channels are reported. No conversion was selected by test performance. Missing channels are passed through the original training-fitted processing. The reduced HGB removes explicit observation flags/ages and ICU duration; it is not entirely free of missingness information.

The initial adapter omitted nursing-chart temperature and respiratory-chart FiO2. Amendment 01 adds explicit C/F temperatures (C wins a same-time duplicate) and explicitly labeled FiO2 fields, using the later event/entry offset. Directly observed scoring rows changed as follows; these are **measurement frequencies before forward filling**, not patient coverage:

{md(['Channel','Initial','Amended exploratory'],coverage)}

This is a substantive post-test data harmonization amendment. It does not make the amended cohort unseen or confirmatory.

## Patient-level results

The table below reports the original full HGB anchors, using native numeric units, for both sources and both runs. The local patient threshold targets a nominal 10% false-alert probability using maxima from 187 negative calibration people, a finite-sample order statistic and a strict `score > threshold` crossing. This target is not an external-shift guarantee and is not achieved exactly in every test cell. Source patient thresholds are carried over unchanged.

{anchor}

The initial full HGB models alerted 122/444 negative patients with either source threshold. In the amended run this increased to 128/444 and 131/444. Local calibration reduced those amended counts to 47/444 and 38/444, with any alert in the final six hours in 0/17 and 1/17 cases. These observations show a burden/detection trade-off; they do not establish effective sepsis detection. With 17 cases, one detected case is 5.9 percentage points. Zero successes still has an exact upper 95% limit of 19.5%.

![Full HGB external results with exact patient intervals](figures/external_hgb_results.png)

All six models and both input variants are also reported through discrimination measures. AP should be compared with the 0.00519 hourly prevalence. No hour-level confidence interval is supplied because repeated hours are correlated within patients.

{disc}

The complete CSV retains all 360 policy comparisons, including source hourly thresholds, admission single alerts, four/six-hour silencing and the three-of-five rule. Do not choose a model, rule, unit variant or run using these test outcomes and then describe its score as confirmatory. Single alerts and silencing preserve admission-level false-alert and first-alert outcomes at a shared threshold while reducing emitted alerts. Their clinical acceptability is unreviewed.

Exact binomial intervals describe the selected patient counts. They do not adjust for hospital clustering, label error, selection bias, multiplicity or cross-resource overlap. Differences between runs are descriptive, not independent-sample treatment effects. There is no simulated clinical utility claim.

## Automated audit versus human review

The earlier numerical audit recomputed seven patient proportions and exact intervals in 288 Stage 2 and 660 Stage 3 rows, checked 1,254,335 scoring hours and verified 48 fixed hourly anchors. All 17 recorded checks passed. The external audit separately checked proportions/intervals, fixed-threshold policy invariants, person separation, pre-onset scoring, cohort identity across the two runs and frozen source/input hashes: all {len(checks)} recorded checks passed. Eight external adapter tests passed. These checks improve arithmetic and implementation confidence; **they are AI-assisted audits, not an independent human peer review**.

Review status:

{md(['Requirement','Status'],[['Public external scoring','Completed; weak results, limited demo'],['Verified institution/patient nonoverlap','Not established'],['Matching clinical target / adjudication','Not established'],['Clinician review','Pending; no reviewer has signed'],['Statistical human review','Pending; no reviewer has signed'],['Original numerical audit','Passed automated checks'],['Submission readiness','Not ready to claim independent clinical validation']])}

## Next actions for a defensible paper

Give `Human_Review_Packet.md`, this report, the unchanged manuscript and complete results to a critical-care/sepsis clinician and a statistician. Resolve target mapping, source units, chart-time assumptions, early-onset selection, institution independence and what constitutes an actionable first alert. Record their actual comments and decisions.

For stronger independent evidence, obtain authorized access to a genuinely separate institution/resource, such as HiRID or AmsterdamUMCdb. Credentialing and data-use agreements must be completed by the researcher. Fix mappings and target before examining that cohort's outcomes, then repeat the frozen transport and calibration evaluation with a new protocol. This cannot be replaced by connecting Colab alone.

The paper can report transport failure and alert burden cautiously; these results do not support a claim of model superiority, improved patient outcomes or clinical deployment. Publication, Q1 classification, zero cost and a two–three month publication timeline are not guaranteed by this evaluation.

## Reproducibility and attribution

The package includes public raw data, licenses, pinned benchmark inputs, six frozen models, original and amended protocols/locks, code, tests, complete external results and audit records. Both runs were repeated from an extracted package in isolated copies: all 18 numerical tables, 24 prediction vectors and eight feature/hour/label arrays matched exactly (50 comparisons). The verification record is supplied. `README_STAGE4.md` and the Colab notebook provide execution steps. The notebook is schema/code checked; a signed-in Colab session was not run here.

Dataset: Johnson A, Pollard T, Badawi O, Raffa J. eICU-CRD Demo v2.0.1 (2021), DOI [10.13026/4mxk-na84](https://doi.org/10.13026/4mxk-na84). Parent database: Pollard et al. Scientific Data (2018), DOI [10.1038/sdata.2018.178](https://doi.org/10.1038/sdata.2018.178).

Benchmark: van de Water et al. YAIB: Yet Another ICU Benchmark. ICLR 2024; [arXiv:2306.05109](https://arxiv.org/abs/2306.05109). Benchmark repository code is MIT; derived datasets are ODbL, not relicensed as MIT by this package.

Measurement documentation: [patient](https://eicu.mit.edu/eicutables/patient/), [lab](https://eicu.mit.edu/eicutables/lab/), [vitalPeriodic](https://eicu.mit.edu/eicutables/vitalperiodic/), [nurseCharting](https://eicu.mit.edu/eicutables/nursecharting/), [respiratoryCharting](https://eicu.mit.edu/eicutables/respiratorycharting/). Original target: [Challenge 2019](https://physionet.org/content/challenge-2019/1.0.0/). Access: [HiRID](https://physionet.org/content/hirid/1.1.1/), [AmsterdamUMCdb](https://github.com/AmsterdamUMC/AmsterdamUMCdb).
'''
    (S/'External_Validation_Report.md').write_text(report)
    plots(allm)
    print('Report generated; external audit checks:',len(checks))

if __name__=='__main__':run()
