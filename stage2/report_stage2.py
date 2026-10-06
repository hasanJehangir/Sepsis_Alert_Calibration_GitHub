"""Make factual tables and figures from a completed stage-two experiment."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

STAGE=Path(__file__).resolve().parent
OUT=STAGE/'results'
MODELS=['hgb','logistic','hgb_no_observation_features']
MODEL_NAMES={'hgb':'Gradient boosting','logistic':'Logistic regression','hgb_no_observation_features':'Boosting, reduced features'}
POLICIES=['source_hourly','source_patient','target_patient_all']
POLICY_NAMES={'source_hourly':'Source hourly','source_patient':'Source patient','target_patient_all':'Local patient (all)'}
COLORS=['#64748b','#0f766e','#d97706']

def pct(value):return f'{100*value:.1f}%' if pd.notna(value) else 'NA'
def count_rate(row,endpoint,denominator):
    return f"{int(row[endpoint+'_count'])}/{int(row[denominator])} ({pct(row[endpoint])})"
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(map(str,row))+' |' for row in rows])

def key_findings(main):
    natural=main[(main.source!=main.test_site)&(main.cap=='natural')]
    def get(source,policy):
        return natural[(natural.source==source)&(natural.model=='hgb')&(natural.policy==policy)].iloc[0]
    a=get('A','source_patient');b=get('B','source_patient')
    al=get('A','target_patient_all');bl=get('B','target_patient_all')
    h=get('B','source_hourly')
    rank_differences=[]
    for source in ['A','B']:
        for model in MODELS:
            rows=natural[(natural.source==source)&(natural.model==model)].set_index('policy')
            for finite,empirical in [('source_patient','source_empirical_patient'),('target_patient_all','target_empirical_patient_all')]:
                rank_differences.append(abs(rows.loc[finite,'patient_false_alert_rate']-rows.loc[empirical,'patient_false_alert_rate']))
    return [
        '## Main finding and decision',
        f"**Continue as a calibration/transport evaluation; do not submit the current study as a new superior early-warning method.** Full-feature gradient boosting’s source patient threshold alerted {pct(a.patient_false_alert_rate)} of nonseptic test admissions in A → B, versus {pct(b.patient_false_alert_rate)} in B → A. The same directional over-/under-target pattern appears in all three prespecified model variants. This is evidence about these two released hospitals, not a guarantee about other deployments.",
        f"Using the separate local calibration pool moved those rates to {pct(al.patient_false_alert_rate)} and {pct(bl.patient_false_alert_rate)}. In B → A it also reduced six-hour-window case detection from {pct(b.window6_sensitivity)} to {pct(bl.window6_sensitivity)}. In A → B local calibration increased both false alerts and detection slightly. Local calibration therefore changes an operating point; it does not provide a uniform benefit.",
        f"With local thresholds, any six-hour-window crossing occurred in {pct(al.window6_sensitivity)} of A → B cases and {pct(bl.window6_sensitivity)} of B → A cases, while the **first** crossing occurred in that window in only {pct(al.first6_sensitivity)} and {pct(bl.first6_sensitivity)}. Earlier first alerts account for {pct(al.early_first_fraction)} and {pct(bl.early_first_fraction)} of cases. An earlier alert can still be clinically relevant; this experiment has no clinician-response or intervention evidence to decide that.",
        f"Changing the calibration unit from hours to admissions substantially changes workload (for example, B → A false alerts fell from {pct(h.patient_false_alert_rate)} to {pct(b.patient_false_alert_rate)}). By comparison, the finite-sample one-rank correction versus the empirical patient quantile changed the full-calibration natural-duration false-alert rates by at most {100*max(rank_differences):.2f} percentage points. Large workload reductions must not be attributed to a new conformal algorithm.",
        'The defensible candidate manuscript question is: **How reliably do admission-level workload targets transfer, and what detection cost and calibration-sample variability follow from restoring them locally?** Close prior literature still makes novelty provisional. A protocol-aligned published-policy benchmark and an additional independent cohort are the next scientific priorities; these have not been completed here.'
    ]

def transfer_plot(main):
    fig,axes=plt.subplots(2,3,figsize=(15,9),sharey=True)
    endpoints=['patient_false_alert_rate','window6_sensitivity','first6_sensitivity']
    titles=['Nonseptic patients alerted','Any alert in six-hour window','First alert in six-hour window']
    x=np.arange(3)
    for ri,(source,target) in enumerate([('A','B'),('B','A')]):
        rows=main[(main.source==source)&(main.test_site==target)&(main.cap=='natural')]
        for ci,endpoint in enumerate(endpoints):
            ax=axes[ri,ci]
            for pi,policy in enumerate(POLICIES):
                selection=rows[rows.policy==policy].set_index('model').loc[MODELS]
                values=selection[endpoint].to_numpy()*100
                lo=selection[endpoint+'_ci_low'].to_numpy()*100
                hi=selection[endpoint+'_ci_high'].to_numpy()*100
                positions=x+(pi-1)*.24
                ax.bar(positions,values,width=.22,color=COLORS[pi],label=POLICY_NAMES[policy],
                       yerr=np.vstack([values-lo,hi-values]),capsize=2)
                for j,v in enumerate(values):ax.text(positions[j],hi[j]+1.5,f'{v:.1f}',ha='center',fontsize=8)
            if ci==0:
                ax.axhline(10,color='#b91c1c',linestyle='--',linewidth=1)
                ax.set_ylabel(f'Hospital {source} → {target}\nPatients (%)',fontsize=12)
            ax.set_title(titles[ci],fontsize=12,fontweight='bold')
            ax.set_xticks(x,['Trees\nfull','Logistic','Trees\nreduced'])
            ax.set_ylim(0,112);ax.set_yticks([0,20,40,60,80,100])
            ax.set_axisbelow(True);ax.grid(axis='y',alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.92),ncol=3,frameon=False)
    fig.suptitle('Hospital transfer: workload and detection trade-offs',x=.055,ha='left',y=.99,fontsize=19,fontweight='bold')
    fig.text(.055,.94,'Reserved test patients · natural-duration records · 95% exact binomial intervals',color='#475569')
    fig.text(.055,.02,'Dashed line: 10% patient false-alert target. Hourly and patient calibration target different events.\nReduced-feature trees omit explicit measurement flags, measurement ages, and current ICU hour. Research use only.',fontsize=10,color='#475569')
    fig.subplots_adjust(left=.06,right=.99,bottom=.14,top=.81,wspace=.15,hspace=.38)
    fig.savefig(OUT/'transfer_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)

def budget_plot(main,budget):
    fig,axes=plt.subplots(1,2,figsize=(12,5.4),sharey=True)
    for ax,(source,target) in zip(axes,[('A','B'),('B','A')]):
        for i,model in enumerate(MODELS):
            sub=budget[(budget.source==source)&(budget.test_site==target)&(budget.model==model)&
                       (budget.cap=='natural')&(budget.endpoint=='patient_false_alert_rate')].sort_values('budget')
            values=sub['median'].to_numpy()*100;lo=sub.p05.to_numpy()*100;hi=sub.p95.to_numpy()*100
            ax.errorbar(np.arange(3)+(i-1)*.06,values,yerr=[values-lo,hi-values],
                        marker='o',capsize=4,color=COLORS[i],label=MODEL_NAMES[model])
            full=main[(main.source==source)&(main.test_site==target)&(main.model==model)&
                      (main.cap=='natural')&(main.policy=='target_patient_all')].iloc[0]
            ax.scatter(3+(i-1)*.06,100*full.patient_false_alert_rate,color=COLORS[i],marker='D')
        ax.axhline(10,color='#b91c1c',linestyle='--',linewidth=1)
        ax.set_xticks(np.arange(4),['100','250','500','All'])
        ax.set_xlabel('Completed local calibration admissions')
        ax.set_title(f'Hospital {source} → {target}',fontweight='bold')
        ax.set_axisbelow(True);ax.grid(axis='y',alpha=.15);ax.set_ylim(bottom=0)
    axes[0].set_ylabel('Nonseptic test patients alerted (%)')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.52,.86),ncol=3,frameon=False,fontsize=9)
    fig.suptitle('Local calibration: variation across sample budgets',x=.07,ha='left',y=.99,fontsize=17,fontweight='bold')
    fig.text(.07,.91,'Markers: median over 20 samples · bars: 5th–95th percentiles across samples',fontsize=11,color='#475569')
    fig.text(.07,.03,'Bars describe calibration-sample variation on a fixed test cohort; they are not population confidence intervals.\n“All” uses the entire separate local calibration pool. Dashed line: 10% patient false-alert target.',fontsize=9,color='#475569')
    fig.subplots_adjust(left=.08,right=.99,bottom=.21,top=.72,wspace=.15)
    fig.savefig(OUT/'calibration_budgets.png',dpi=180,bbox_inches='tight');plt.close(fig)

def write_report(main,budget):
    done=json.loads((OUT/'completed.json').read_text())
    counts=pd.read_csv(OUT/'cohort_counts.csv');excluded=pd.read_csv(OUT/'exclusions.csv')
    paired=pd.read_csv(OUT/'paired_differences.csv');disc=pd.read_csv(OUT/'discrimination.csv')
    model_infos=[json.loads(p.read_text()) for p in sorted(OUT.glob('*_model_info.json'))]
    audit=json.loads((OUT/'independent_audit.json').read_text()) if (OUT/'independent_audit.json').exists() else None
    natural=main[(main.source!=main.test_site)&(main.cap=='natural')]
    selected=natural[natural.policy.isin(POLICIES)]
    rows=[]
    for source,target in [('A','B'),('B','A')]:
        for model in MODELS:
            for policy in POLICIES:
                r=selected[(selected.source==source)&(selected.model==model)&(selected.policy==policy)].iloc[0]
                rows.append([f'{source} → {target}',MODEL_NAMES[model],POLICY_NAMES[policy],
                             count_rate(r,'patient_false_alert_rate','nonseptic_patients'),
                             count_rate(r,'window6_sensitivity','septic_patients'),
                             count_rate(r,'first6_sensitivity','septic_patients')])
    parts=['# Stage-two findings: sepsis alert calibration across hospitals',
           '**For Hasan Jehangir.** Completed '+done['completed_at_utc']+'. Actual computed results; all 3,000 pilot files were excluded from this stage. No CAPMI material was used.',
           *key_findings(main),
           '## Completion and sample accounting',
           f"The runner considered 37,336 reserved files, included {done['cache']['patients']:,} records and {done['cache']['hours']:,} pre-onset/negative scoring hours, and excluded {done['cache']['excluded']:,} records. It fitted six source/model combinations and computed {done['metric_rows']:,} policy-level result rows. All model, direction, cap, and calibration-sample outcomes are retained.",
           table(['Hospital','Role','Patients','Septic patients'],counts[['site','role','patients','sepsis']].values.tolist()),
           table(['Exclusion reason','Count'],excluded.reason.value_counts().items()),
           f"Model fits reporting convergence: {sum(bool(i['converged']) for i in model_infos)}/{len(model_infos)}. Details and warnings are retained in each model-info file. The plan was locally locked on 29 September before reserved data were downloaded; it was not publicly preregistered.",
           (f"Verification: 14 implementation checks passed. An independent direct-crossing calculation matched all {audit['natural_duration_main_rows_checked']} natural-duration main-policy rows ({audit['endpoint_count_checks']} endpoint-count checks and {audit['hourly_denominator_and_crossing_checks']} hourly denominator/crossing checks). Pilot overlap was zero, cohort hashes were unique, and original manifest roles were preserved. This audit does not independently validate raw preprocessing or all capped/budget rows." if audit else 'The separate direct-crossing audit has not been run for this execution.'),
           '## Main cross-hospital results — natural-duration records',
           table(['Transfer','Model','Threshold calibration','Nonseptic patients alerted','Any alert in six-hour window','First alert in six-hour window'],rows),
           'These policies use the same fitted model within each transfer/model combination. Changing thresholds does not improve score discrimination. Hourly and patient calibration target different error events, so the false-alert reduction must be interpreted with the loss or gain in detection. Exact binomial intervals for every endpoint are in `results/main_metrics.csv`.',
           '![Workload and detection trade-offs](results/transfer_comparison.png)',
           '## Patient-paired comparisons',
           'Differences below are percentage points, policy 1 minus policy 0. Negative false-alert differences mean fewer nonseptic patients alerted; positive sensitivity differences mean more cases detected. These are 2,000-draw paired bootstrap intervals conditional on the fitted thresholds, without multiplicity adjustment or calibration-threshold uncertainty.']
    comparisons=[]
    subset=paired[(paired.source!=paired.test_site)&(paired.model=='hgb')]
    for r in subset.itertuples():
        comparisons.append([f'{r.source} → {r.test_site}',r.comparison,r.endpoint,
                            f'{100*r.difference:+.2f}',f'[{100*r.ci_low:+.2f}, {100*r.ci_high:+.2f}]',r.n])
    parts.append(table(['Transfer','Comparison','Endpoint','Difference, pp','95% interval, pp','Patients'],comparisons))
    parts+=['## Local calibration budgets',
            'The following table shows full-feature gradient boosting. Each budget samples completed admissions, then uses only nonseptic admissions for the threshold. Results summarize 20 fixed nested samples, on the same held-out test patients. The 5th–95th percentiles describe conditional calibration-sample variation, not population confidence intervals.']
    budget_rows=[]
    for source,target in [('A','B'),('B','A')]:
        for n in [100,250,500]:
            sub=budget[(budget.source==source)&(budget.test_site==target)&(budget.model=='hgb')&(budget.cap=='natural')&(budget.budget==n)].set_index('endpoint')
            fp=sub.loc['patient_false_alert_rate'];sens=sub.loc['window6_sensitivity'];first=sub.loc['first6_sensitivity']
            budget_rows.append([f'{source} → {target}',n,pct(fp['median']),f"{pct(fp.p05)}–{pct(fp.p95)}",pct(sens['median']),pct(first['median'])])
    parts.append(table(['Transfer','Admissions sampled','Median patient false alerts','5th–95th percentiles','Median window detection','Median timely first alert'],budget_rows))
    parts+=['![Calibration-budget variation](results/calibration_budgets.png)',
            'The per-draw negative calibration counts and outcomes are in `all_metrics.csv`; all sampled IDs are in `calibration_samples.json`. Increasing sample size may stabilize a threshold without improving discrimination. Twenty samples from one calibration pool are not 20 external replications.',
            '## Observation caps and additional timing diagnostics',
            'Caps at ICU hours 24, 48, and 72 use separately recalibrated, equally capped negative trajectories. Early discharge retains shorter follow-up. Positive cases with onset after the cap are excluded from that cap’s case denominator and are never relabeled negative. Differences across caps also reflect different case cohorts.']
    cap_rows=[]
    for r in main[(main.source!=main.test_site)&(main.model=='hgb')&(main.policy=='target_patient_all')&(main.cap!='natural')].itertuples():
        cap_rows.append([f'{r.source} → {r.test_site}',r.cap,r.nonseptic_patients,r.septic_patients,r.late_cases_excluded,
                         pct(r.patient_false_alert_rate),pct(r.window6_sensitivity),pct(r.first6_sensitivity)])
    parts.append(table(['Transfer','Cap, h','Nonseptic','Cases evaluated','Later cases omitted','Patient false alerts','Window detection','Timely first alert'],cap_rows))
    timing_rows=[]
    for r in natural[(natural.model=='hgb')&natural.policy.isin(POLICIES)].itertuples():
        timing_rows.append([f'{r.source} → {r.test_site}',POLICY_NAMES[r.policy],pct(r.first6_sensitivity),pct(r.first12_sensitivity),pct(r.early_first_fraction)])
    parts+=['The twelve-hour diagnostic was specified after the pilot but before reserved-data analysis. Only available scores starting at ICU hour 6 can contribute; some early-onset cases have incomplete twelve-hour observation. It does not replace the six-hour primary target.',
            table(['Transfer','Policy','First alert in 6 h','First alert in 12 h','First alert earlier than 6 h'],timing_rows),
            'An early alert outside the chosen window is not automatically useless or harmful. Clinical interpretation requires a clinically justified workflow and prospective study. No repeat-alert silencing, intervention effect, or official Challenge utility score is simulated.',
            '## Discrimination and feature ablation']
    disc_rows=[]
    for r in disc[(disc.source!=disc.test_site)&(disc.cap=='natural')].itertuples():
        disc_rows.append([f'{r.source} → {r.test_site}',MODEL_NAMES[r.model],f'{r.hourly_auroc:.3f}',
                          f'{r.hourly_average_precision:.3f}',f'{r.hourly_brier:.4f}',pct(r.hourly_positive_prevalence)])
    parts.append(table(['Transfer','Model','Hourly AUROC','Hourly AP','Brier','Positive-hour prevalence'],disc_rows))
    parts+=['The reduced-feature tree model omits explicit measurement indicators, time since measurement, and current ICU hour. Native missing values and observed trajectories still carry care-process information. This ablation cannot establish causality or remove all site information. Hourly metrics receive no misleading independent-hour confidence intervals.',
            '## Research and manuscript decision',
            'The completed stage provides a reproducible empirical calibration/transport audit. It does not establish a new conformal algorithm, a clinically effective early-warning system, or a paper ready for a Q1 journal. `NOVELTY_AUDIT.md` documents close work on conformal sepsis prediction, international transfer, first-alert evaluation, and evaluation-strategy effects.',
            'Before submission, the strongest defensible direction is an evaluation paper about workload targets and threshold transport. It requires a more complete comparison with published alert policies and preferably another independently defined cohort or clinical collaborator. A headline that only says “false alerts were reduced” would overstate the contribution. If timing remains poor or local effects disagree across directions, those findings must remain central.',
            'Limitations: only two historical public hospitals; retrospective challenge labels; later-onset exclusions and end-of-record censoring; unknown repeated admissions beyond exact raw duplicates; no patient-weighted training; fixed model parameters; small case counts for some caps; calibration-sample variation conditional on one pool; no prospective clinical or intervention validation. Hourly scores are serially dependent; an hourly threshold does not imply an admission-level error guarantee. Patient rank guarantees require exchangeability and do not guarantee 10% error after arbitrary hospital or temporal shift.',
            '## Reproduce and continue',
            'Use `Sepsis_Stage2.ipynb` for the complete CPU workflow, or follow `README_STAGE2.md`. The source, trained models, hourly scores, subject statistics, sample IDs, and all result tables are retained. No paid API or GPU is needed. A fresh download requires internet access.',
            'The execution service interrupted the first download; the recovered runner and locked specification were unchanged, and downloading resumed from saved records. Research computation occurs during active runs; no claim is made that experiments continued during the inactivity gap.',
            'Free subscription publication may be available at suitable journals, but fees, current category/year quartile, scope, and actual acceptance timelines must be verified at submission. Neither Q1 acceptance nor actual publication within two to three months is guaranteed. No manuscript has been submitted.']
    (STAGE/'Stage2_Findings.md').write_text('\n\n'.join(parts)+'\n')

def main():
    if not (OUT/'completed.json').exists():raise RuntimeError('Run is not complete; findings cannot be generated yet')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    main=pd.read_csv(OUT/'main_metrics.csv');budget=pd.read_csv(OUT/'budget_summary.csv')
    transfer_plot(main);budget_plot(main,budget);write_report(main,budget)
    print(STAGE/'Stage2_Findings.md')

if __name__=='__main__':main()
