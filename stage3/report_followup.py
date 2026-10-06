"""Generate study-wide exploratory tables and static scientific figures."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

STAGE=Path(__file__).resolve().parent
OUT=STAGE/'results'
POLICIES=['hourly','single','silence4','silence6','three_of_five']
NAMES={'hourly':'Hourly','single':'Single','silence4':'Silence 4 h','silence6':'Silence 6 h','three_of_five':'Three of five'}
MODELS={'hgb':'Gradient boosting','logistic':'Logistic regression','hgb_no_observation_features':'Boosting, reduced'}
COLORS=['#64748b','#0f766e','#d97706','#2563eb','#9333ea']

def pct(v):return f'{100*v:.1f}%'
def md_table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(map(str,row))+' |' for row in rows])

def main():
    done=json.loads((OUT/'completed.json').read_text());assert done['status']=='EXPLORATORY_FOLLOWUP_COMPLETED'
    m=pd.read_csv(OUT/'policy_metrics.csv');paired=pd.read_csv(OUT/'paired_policy_differences.csv')
    local=m[(m.condition=='matched_patient')&(m.anchor=='local')&(m.alpha==.1)&(m.source!=m.test_site)]
    local.to_csv(OUT/'cross_hospital_local10.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(12,5.8),sharey=True)
    for ax,(source,target) in zip(axes,[('A','B'),('B','A')]):
        s=local[(local.source==source)&(local.model=='hgb')].set_index('policy').loc[POLICIES]
        x=np.arange(5);values=s.nonseptic_alerts_per_100_hours.to_numpy()
        ax.bar(x,values,color=COLORS,width=.7)
        for i,row in enumerate(s.itertuples()):
            ax.text(i,values[i]+.08,f'{values[i]:.2f}',ha='center',fontweight='bold')
            ax.text(i,.08,f'{100*row.patient_false_alert_rate:.1f}%',ha='center',fontsize=9,color='white' if values[i]>.5 else '#0f172a')
        ax.set_xticks(x,['Hourly','Single','Silence\n4 h','Silence\n6 h','Three\nof five'])
        ax.set_title(f'Hospital {source} → {target}',fontweight='bold');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
        ax.set_ylim(0,5.3)
    axes[0].set_ylabel('Nonseptic alert emissions per 100 scoring hours')
    fig.suptitle('Repeat-alert burden and admission-level false alerts differ',x=.075,ha='left',y=.99,fontsize=17,fontweight='bold')
    fig.text(.075,.91,'Full-feature gradient boosting · separate local calibration · nominal 10% patient target',color='#475569')
    fig.text(.075,.03,'Numbers above bars: alert emissions per 100 hours. Percentages inside/under bars: nonseptic admissions alerted.\nSuppression preserves first crossings; three-of-five is separately calibrated. Exploratory analysis; no clinical benefit claim.',fontsize=9,color='#475569')
    fig.subplots_adjust(left=.08,right=.99,bottom=.22,top=.77,wspace=.15)
    fig.savefig(OUT/'alert_burden.png',dpi=200,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,5.8),sharey=True)
    for ax,(source,target) in zip(axes,[('A','B'),('B','A')]):
        s=m[(m.source==source)&(m.test_site==target)&(m.model=='hgb')&(m.condition=='matched_patient')&(m.anchor=='local')]
        for policy,color in zip(POLICIES,COLORS):
            r=s[s.policy==policy].sort_values('alpha')
            ax.plot(100*r.patient_false_alert_rate,100*r.window6_sensitivity,'o-',label=NAMES[policy],color=color,linewidth=1.7,markersize=5)
        ax.set_title(f'Hospital {source} → {target}',fontweight='bold');ax.set_xlabel('Nonseptic admissions alerted (%)')
        ax.set_xlim(0,25);ax.set_ylim(0,65);ax.grid(alpha=.15)
    axes[0].set_ylabel('Cases with emitted alert in six-hour window (%)')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.53,.87),ncol=5,frameon=False,fontsize=9)
    fig.suptitle('Detection across three local workload targets',x=.075,ha='left',y=.99,fontsize=18,fontweight='bold')
    fig.text(.075,.91,'Full-feature gradient boosting · nominal targets 5%, 10%, 20% · all operating points retained',color='#475569')
    fig.text(.075,.025,'Lines join three observed operating points; they do not establish an optimized frontier or clinical utility.\nTargets concern separate calibration admissions. Displayed rates are measured on the fixed test cohort.',fontsize=9,color='#475569')
    fig.subplots_adjust(left=.08,right=.99,bottom=.2,top=.73,wspace=.15)
    fig.savefig(OUT/'workload_detection.png',dpi=200,bbox_inches='tight');plt.close(fig)
    rows=[]
    for source,target in [('A','B'),('B','A')]:
        for model in ['hgb','logistic','hgb_no_observation_features']:
            s=local[(local.source==source)&(local.model==model)].set_index('policy')
            for policy in POLICIES:
                r=s.loc[policy]
                rows.append([f'{source} → {target}',MODELS[model],NAMES[policy],pct(r.patient_false_alert_rate),
                             f'{r.nonseptic_alerts_per_100_hours:.3f}',pct(r.window6_sensitivity),pct(r.first6_sensitivity)])
    parts=['# Stage-three follow-up: alert rules and workload targets',
           'Completed '+done['completed_at_utc']+'. These are computed exploratory results using the same stage-two test records, which had already been examined. No model was retrained; no CAPMI material was used.',
           f"The run retained {done['policy_rows']} policy-level rows and {done['paired_endpoint_rows']} paired endpoint comparisons, covering six frozen source/model combinations, both test hospitals, five alert rules, fixed threshold references, and patient targets of 5%, 10%, and 20%. Six new implementation checks and all actual-data invariance/anchor checks passed.",
           '## What the benchmark changes',
           '**Repeat-alert suppression reduces alert emissions, not the number of admissions experiencing their first alert at the same threshold.** In full-feature boosting at the local 10% target, four-hour suppression reduced nonseptic emissions by 68.3% (A → B) and 57.5% (B → A). Admission false-alert and first-window-alert counts were unchanged, as required by the rule.',
           'Any emitted alert in the six-hour window fell from 44.8% to 43.5% in A → B and from 36.2% to 34.6% in B → A. With single-alert evaluation, that endpoint equaled first-window sensitivity: 5.2% and 7.7%. Retaining only the first alert changes what counts as later detection.',
           '**Three-of-five is not a demonstrated improvement at matched targets.** For full-feature boosting, local first-window sensitivity changed from 5.2% to 7.8% in A → B but from 7.7% to 5.4% in B → A. Both paired intervals included zero. Mean nonseptic emissions/admission increased in both directions after recalibration. Its per-hour eligibility is reevaluated without a reset, so repeated eligible hours can emit repeated alerts. This is an explicitly defined policy adaptation, not a claim about the full published SepsisAI implementation.',
           '## All models: separately calibrated local 10% admission target',
           md_table(['Transfer','Model','Alert rule','Nonseptic admissions alerted','Emissions/100 negative hours','Any window alert','First window alert'],rows),
           '![Repeated alert burden](results/alert_burden.png)',
           '![Workload and detection](results/workload_detection.png)',
           'Exact binomial intervals and numerators/denominators are retained in `policy_metrics.csv`. The 2,000-draw paired bootstrap is conditional on the model and thresholds, excludes calibration uncertainty, and has no multiplicity correction. Alert-rate denominators are observed pre-onset/negative scoring hours, not a prospectively sampled clinical population.',
           '## Literature scope',
           'Policy structures are grounded in Gupta et al. (2024), doi:10.1371/journal.pdig.0000569; Do et al. (2026), doi:10.2196/72083; Shashikumar et al. (2021), doi:10.1038/s41746-021-00504-6; and Moor et al. (2023), doi:10.1016/j.eclinm.2023.102124. Their complete models and reported percentages are not reproduced. See `FOLLOWUP_PROTOCOL.md` for exact boundaries and adaptation details.',
           '## Manuscript decision',
           'A research manuscript draft now combines the locked calibration/transport study with a separately identified exploratory policy section. The data support an evaluation of asymmetric threshold transport and distinctions between alert burden, admissions alerted, and detection timing. They do not establish a new conformal algorithm or superior clinical warning system.',
           'External validation is not completed. Approved access to another cohort was not supplied, and no restricted patient dataset was accessed. Before calling a new cohort independent, audit hospital/patient overlap and harmonize variables, sepsis labels, and the scoring timeline. Ethics, authorship, affiliations, funding, conflicts, and AI-use disclosures require author review. Current Q1 category/year and realistic journal timing remain publication checks, not guarantees.',
           '## Reproduce',
           'From the project root, install the pinned original requirements, run `python3 -m pytest -q stage3/tests`, then `python3 stage3/run_followup.py` and `python3 stage3/report_followup.py`. The standalone stage-three package contains the exact frozen predictions, scoring hours, and required stage-two metadata. It requires no internet after installing dependencies. When using the original full stage-two archive instead, `--restore-hours` reconstructs the omitted scoring-hour cache from public records and verifies its original hash.'
    ]
    (STAGE/'Stage3_Findings.md').write_text('\n\n'.join(parts)+'\n')
    print(STAGE/'Stage3_Findings.md')

if __name__=='__main__':main()
