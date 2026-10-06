"""Regenerate manuscript tables and scientific figures from frozen CSV results.

This script does not train models, alter study outputs or compute a new validation.
Python dependencies: pandas, numpy, scipy, matplotlib.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'results'
FIG = ROOT / 'figures'
TAB = ROOT / 'tables'
for p in (FIG, TAB):
    p.mkdir(exist_ok=True)

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'axes.labelsize': 11, 'axes.titlesize': 12,
                     'pdf.fonttype': 42, 'ps.fonttype': 42,
                     'axes.spines.top': False, 'axes.spines.right': False})
COLORS = ['#17609A', '#D27A20', '#21816A']
MODEL = {'logistic': 'Logistic regression', 'hgb': 'Full boosting',
         'hgb_no_observation_features': 'Reduced boosting'}
RULE = {'hourly': 'Hourly', 'single': 'Single', 'silence4': 'Silence 4 h',
        'silence6': 'Silence 6 h', 'three_of_five': 'Three-of-five'}
RULES = list(RULE)

def save(fig, name):
    fig.savefig(FIG / (name+'.pdf'), bbox_inches='tight')
    fig.savefig(FIG / (name+'.png'), dpi=220, bbox_inches='tight')
    plt.close(fig)

def pct(x):
    return f'{100*x:.1f}'

def head(top, bottom):
    return '\\makecell{'+top+'\\\\{}'+bottom+'}'

def valcount(row, endpoint, denom):
    return f"{int(row[endpoint+'_count'])}/{int(row[denom])} ({pct(row[endpoint])})"

def ci(row, endpoint):
    return f"{pct(row[endpoint])} [{pct(row[endpoint+'_ci_low'])}--{pct(row[endpoint+'_ci_high'])}]"

def table(name, caption, label, cols, header, rows, note='', size='small'):
    body = '\n'.join(' & '.join(map(str,r))+r' \\' for r in rows)
    placement = 'htbp' if name.startswith('s_') else 'tbp'
    txt = ('\\begin{table}['+placement+']\n\\centering\n\\'+size+'\n'
           '\\setlength{\\tabcolsep}{4pt}\n\\renewcommand{\\arraystretch}{1.18}\n'
           '\\caption{'+caption+'}\\label{'+label+'}\n'
           '\\begin{tabular}{'+cols+'}\n\\toprule\n'
           +' & '.join(header)+r' \\'+'\n\\midrule\n'+body+
           '\n\\bottomrule\n\\end{tabular}\n')
    if note:
        txt += '\\par\\vspace{3pt}\\begin{minipage}{\\linewidth}\\footnotesize '+note+'\\end{minipage}\n'
    txt += '\\end{table}\n'
    (TAB/(name+'.tex')).write_text(txt)

main = pd.read_csv(DATA/'main_metrics.csv')
pol = pd.read_csv(DATA/'cross_hospital_local10.csv')
ext = pd.read_csv(DATA/'all_external_policy_metrics.csv')
disc = pd.read_csv(DATA/'discrimination.csv')
extdisc = pd.read_csv(DATA/'all_external_discrimination.csv')
counts = pd.read_csv(DATA/'cohort_counts.csv')
rows=[]
for site in ['A','B']:
    for role in ['train','calibration','test']:
        r=counts.query('site == @site and role == @role').iloc[0]
        rows.append([f'Challenge {site}', role.capitalize(), f'{r.patients:,}',
                     f'{r.sepsis:,}', f'{r.patients-r.sepsis:,}'])
rows += [['eICU demo','Calibration','195','8','187'],
         ['eICU demo','Test','461','17','444']]
table('cohort','Eligible study partitions.','tab:cohort','llrrr',
      ['Resource','Role','Admissions','Cases','Nonseptic'],rows,
      'Challenge total: 36,658 admissions; eICU demo: 656 people with one selected stay each. '
      'The external resource has no training partition. Challenge record splits cannot exclude linked admissions.')

locked = main.query("transfer == True and cap == 'natural' and model == 'hgb'")
THR = ['source_hourly','source_patient','target_patient_all']
TNAME = {'source_hourly':'Source hourly', 'source_patient':'Source admission',
         'target_patient_all':'Local admission'}
rows=[]
for source in ['A','B']:
    target='B' if source=='A' else 'A'
    for threshold in THR:
        r=locked.query('source == @source and policy == @threshold').iloc[0]
        rows.append([source+r'$\to$'+target,TNAME[threshold],
                     ci(r,'patient_false_alert_rate'),
                     valcount(r,'window6_sensitivity','septic_patients'),
                     valcount(r,'first6_sensitivity','septic_patients')])
table('transport','Primary natural-duration transport: full-feature boosting.','tab:transport','llrrr',
      ['Transfer','Calibration',head('False alerts (\\%)','[95\\% CI]'),
       head('Any6','$n/N$ (\\%)'),head('First6','$n/N$ (\\%)')],rows,
      'Nonseptic denominators are 3,473 for A$\\to$B and 3,422 for B$\\to$A. '
      'Any6 and First6 use all eligible cases. All thresholds target 10\\% on their stated calibration unit.',size='footnotesize')

hp=pol.query("model == 'hgb'")
rows=[]
for source in ['A','B']:
    target='B' if source=='A' else 'A'
    for rule in RULES:
        r=hp.query('source == @source and policy == @rule').iloc[0]
        rows.append([source+r'$\to$'+target,RULE[rule],f'{r.nonseptic_alerts:,}',
                     f'{r.nonseptic_alerts_per_100_hours:.3f}',pct(r.patient_false_alert_rate),
                     pct(r.window6_sensitivity),pct(r.first6_sensitivity)])
table('policies','Exploratory emission rules at local nominal 10\\% admission calibration.','tab:policies','llrrrrr',
      ['Transfer','Rule',head('Negative','emissions'),head('Per 100','hours'),
       head('False','alerts (\\%)'),'Any6 (\\%)','First6 (\\%)'],rows,
      'Full-feature boosting; denominators match Table~\\ref{tab:transport}. '
      'Three-of-five uses its own transformed-score threshold and emits at each qualifying hour.',size='footnotesize')

eh=ext.query("model == 'hgb' and input_variant == 'native_numeric' and policy == 'hourly'")
RUNS=['Initial','Amended']
CONDS=['source_patient','local_patient']
print('External run labels:',list(ext.run.unique()),'conditions:',list(ext.condition.unique()))
if 'Amended' not in list(ext.run.unique()):
    RUNS=['Initial',next(x for x in ext.run.unique() if x!='Initial')]
COND_NAMES={'source_patient':'Source','local_patient':'Local'}
rows=[]
for run in RUNS:
    for source in ['A','B']:
        for cond in CONDS:
            r=eh.query('run == @run and source == @source and condition == @cond').iloc[0]
            rows.append(['Initial' if run=='Initial' else 'Amended',source,COND_NAMES[cond],
                         valcount(r,'patient_false_alert_rate','nonseptic_patients'),
                         valcount(r,'window6_sensitivity','septic_patients'),
                         valcount(r,'first6_sensitivity','septic_patients')])
table('external','External public-demo evaluation: full-feature boosting, native inputs, hourly emission.','tab:external','lllrrr',
      ['Inputs','Source','Threshold',head('False alerts','$n/N$ (\\%)'),
       head('Any6','$n/N$ (\\%)'),head('First6','$n/N$ (\\%)')],rows,
      'Source denotes the training Challenge hospital; both models use the same external test cohort. '
      'Local thresholds use 187 nonseptic calibration people. The amended run is exploratory.',size='footnotesize')

# Figure 1: all three endpoint intervals, both transfer directions.
fig, axes=plt.subplots(2,3,figsize=(10.0,6.1),layout='constrained')
endpoints=['patient_false_alert_rate','window6_sensitivity','first6_sensitivity']
titles=['Nonseptic admissions alerted','Any6 case sensitivity','First6 case sensitivity']
for ii,source in enumerate(['A','B']):
    target='B' if source=='A' else 'A'
    rs=[locked.query('source == @source and policy == @t').iloc[0] for t in THR]
    for jj,e in enumerate(endpoints):
        ax=axes[ii,jj]
        for k,r in enumerate(rs):
            x=100*r[e]; lo=100*r[e+'_ci_low']; hi=100*r[e+'_ci_high']
            ax.errorbar(x,2-k,xerr=[[x-lo],[hi-x]],fmt=['o','s','D'][k],
                        color=COLORS[k],capsize=3,markersize=7)
            ax.annotate(f'{x:.1f}',(x,2-k),xytext=(5,6),textcoords='offset points',fontsize=11)
        ax.set_yticks([2,1,0],['Source hourly','Source admission','Local admission'] if jj==0 else [])
        ax.set_ylim(-.55,2.65)
        ax.set_xlim(0,90 if jj==1 else 70 if jj==0 else 18)
        ax.grid(axis='x',alpha=.2)
        ax.set_xlabel('Percent')
        ax.set_title(f'{source} → {target}\n{titles[jj]}')
        if jj==0: ax.axvline(10,color='#555555',linestyle='--',linewidth=1)
save(fig,'transport')

# Figure 2: emission counts and window metrics, exactly five retained rules.
fig,axes=plt.subplots(2,2,figsize=(9.0,7.0),layout='constrained')
short=['Hourly','Single','4 h','6 h','3 of 5']
for j,source in enumerate(['A','B']):
    target='B' if source=='A' else 'A'
    rs=[hp.query('source == @source and policy == @rule').iloc[0] for rule in RULES]
    values=[int(r.nonseptic_alerts) for r in rs]
    ax=axes[0,j];bars=ax.bar(range(5),values,color=['#17609A','#718492','#D27A20','#B75A27','#21816A'])
    ax.bar_label(bars,labels=[f'{x:,}' for x in values],padding=3,fontsize=11)
    ax.set_xticks(range(5),short);ax.set_ylim(0,max(hp.nonseptic_alerts)*1.20)
    ax.set_ylabel('Nonseptic warning emissions');ax.set_title(f'{source} → {target}')
    ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    ax=axes[1,j]
    ax.plot(range(5),[100*r.window6_sensitivity for r in rs],'o-',color=COLORS[0],label='Any6')
    ax.plot(range(5),[100*r.first6_sensitivity for r in rs],'s--',color=COLORS[1],label='First6')
    ax.set_xticks(range(5),short);ax.set_ylim(0,55)
    ax.set_ylabel('Case sensitivity (%)');ax.grid(axis='y',alpha=.2)
    ax.legend(loc='upper right',frameon=False)
save(fig,'policies')

# Figure 3: large uncertainty is visible, no truncated sensitivity error bars.
ers=[];labels=[]
for run in RUNS:
    for source in ['A','B']:
        for cond in CONDS:
            ers.append(eh.query('run == @run and source == @source and condition == @cond').iloc[0])
            labels.append(f"{'Initial' if run=='Initial' else 'Amended'} / {source} / {COND_NAMES[cond]}")
fig,axes=plt.subplots(1,3,figsize=(10.6,5.6),layout='constrained')
for j,e in enumerate(endpoints):
    ax=axes[j]
    for k,r in enumerate(ers):
        x=100*r[e];lo=100*r[e+'_ci_low'];hi=100*r[e+'_ci_high']
        color=COLORS[0] if r.condition=='source_patient' else COLORS[2]
        ax.errorbar(x,7-k,xerr=[[x-lo],[hi-x]],fmt='o' if r.run=='Initial' else 's',
                    color=color,capsize=3,markersize=6)
    ax.set_yticks(range(7,-1,-1),labels if j==0 else [])
    ax.set_ylim(-.6,7.6);ax.set_xlim(-1,70 if j else 40)
    ax.set_title(titles[j]);ax.set_xlabel('Percent [95% interval]')
    ax.axhline(3.5,color='#999999',linewidth=.8)
    ax.grid(axis='x',alpha=.2)
    if j==0:ax.axvline(10,color='#555555',linestyle='--',linewidth=1)
save(fig,'external')

# Supplementary tables: every transferred model and all external discriminations.
rows=[]
for _,r in disc.query("transfer == True and cap == 'natural'").iterrows():
    rows.append([r.source+r'$\to$'+r.test_site,MODEL[r.model],f'{r.hourly_auroc:.3f}',
                 f'{r.hourly_average_precision:.4f}',f'{r.hourly_brier:.4f}',
                 f'{100*r.hourly_positive_prevalence:.3f}'])
table('s_discrimination','Natural-duration hourly discrimination for all transferred model fits.','tab:sdisc','llrrrr',
      ['Transfer','Model','AUROC','AP','Brier','Prevalence (\\%)'],rows,
      'A$\\to$B: 121,377 eligible hours; B$\\to$A: 127,929. AP = average precision. '
      'These are descriptive operational-label metrics; no independent-hour intervals are attached.')

bud=pd.read_csv(DATA/'budget_summary.csv')
rows=[]
for source in ['A','B']:
    for budget in [100,250,500]:
        fields=[source+r'$\to$'+('B' if source=='A' else 'A'),budget]
        for endpoint in ['patient_false_alert_rate','window6_sensitivity','first6_sensitivity']:
            r=bud.query("source == @source and transfer == True and cap == 'natural' and model == 'hgb' and budget == @budget and endpoint == @endpoint").iloc[0]
            fields.append(f'{100*r["median"]:.1f} [{100*r.p05:.1f}--{100*r.p95:.1f}]')
        rows.append(fields)
table('s_budgets','Conditional local-calibration variability: full-feature boosting.','tab:sbud','lrrrr',
      ['Transfer','Budget','False alerts (\\%)','Any6 (\\%)','First6 (\\%)'],rows,
      'Values are medians [5th--95th percentiles] over 20 fixed nested calibration samples. '
      'Budgets count all sampled admissions, with only nonseptic admissions used for thresholds. '
      'Percentiles are not confidence intervals for a deployment population.')

pair=pd.read_csv(DATA/'paired_policy_differences.csv')
rows=[]
for source in ['A','B']:
    for endpoint in ['first6','window6','negative_alerts_per_admission']:
        select=pair.query("source == @source and transfer == True and model == 'hgb' and comparison == 'three_of_five_minus_hourly_local10' and endpoint == @endpoint")
        if select.empty: continue
        r=select.iloc[0];scale=1 if 'alerts' in endpoint else 100
        ename={'first6':'First6','window6':'Any6','negative_alerts_per_admission':'Emissions/admission'}[endpoint]
        rows.append([source+r'$\to$'+('B' if source=='A' else 'A'),ename,
                     f'{scale*r.difference:+.2f}',f'[{scale*r.ci_low:+.2f}, {scale*r.ci_high:+.2f}]'])
table('s_paired','Exploratory three-of-five minus hourly differences at local-10\\% targets.','tab:spair','llrr',
      ['Transfer','Endpoint','Difference','Paired 95\\% interval'],rows,
      'Sensitivity differences are percentage points; emission differences are counts per nonseptic admission. '
      'Intervals use 2,000 paired admission bootstrap draws and condition on fitted models and thresholds.')

rows=[]
for run in RUNS:
    for source in ['A','B']:
        for model in MODEL:
            for variant in ['native_numeric','mask_ambiguous_units']:
                r=extdisc.query('run == @run and source == @source and model == @model and input_variant == @variant').iloc[0]
                rows.append(['Initial' if run=='Initial' else 'Amended',source,
                             {'logistic':'Logistic','hgb':'Full HGB','hgb_no_observation_features':'Reduced HGB'}[model],
                             'Native' if variant=='native_numeric' else 'Masked',
                             f'{r.hourly_auroc:.3f}',f'{r.hourly_average_precision:.4f}',f'{r.hourly_brier:.4f}'])
table('s_external_discrimination','All external hourly discrimination results, without model or input-variant selection.','tab:sextdisc','llllrrr',
      ['Inputs','Source','Model','Variant','AUROC','AP','Brier'],rows,
      'All rows use 19,645 test hours; positive-hour prevalence is 102/19,645 (0.519\\%). '
      'Masked inputs set lactate and magnesium unavailable; they do not resolve unit provenance.',size='footnotesize')

rows=[]
for source in ['A','B']:
    for model in MODEL:
        for threshold in ['source_patient','target_patient_all']:
            r=main.query("source == @source and transfer == True and cap == 'natural' and model == @model and policy == @threshold").iloc[0]
            rows.append([source+r'$\to$'+('B' if source=='A' else 'A'),MODEL[model],
                         'Source' if threshold=='source_patient' else 'Local',ci(r,'patient_false_alert_rate'),
                         pct(r.window6_sensitivity),pct(r.first6_sensitivity)])
table('s_allmodels','Admission-threshold transport for every model family.','tab:sallmodels','lllrrr',
      ['Transfer','Model','Threshold','False alerts (\\%) [CI]','Any6 (\\%)','First6 (\\%)'],rows,
      'Natural duration, nominal 10\\% calibration; confidence intervals are exact binomial intervals.',size='footnotesize')

# A compact reproducibility diagram based on study chronology and exact cohort counts.
fig,ax=plt.subplots(figsize=(8.3,7.1));ax.set_xlim(0,10);ax.set_ylim(0,10);ax.axis('off')
def box(x,y,w,h,txt,color='#EDF3F7'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.12',facecolor=color,
                              edgecolor='#486176',linewidth=1.1))
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=11.5)
def arrow(x1,y1,x2,y2):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=14,color='#486176'))
box(1,8.25,8,1.05,'Challenge 2019: 40,336 records\n3,000 pilot records excluded')
box(1,6.65,8,1.05,'37,336 reserved → 36,658 eligible\nSeparate A/B training, calibration and test partitions')
arrow(5,8.2,5,7.85)
box(1,4.8,8,1.25,'Locally locked primary analysis\nSix fitted models; test: 7,309 admissions / 414 cases\nHourly vs admission calibration; threshold transport')
arrow(5,6.6,5,6.25)
box(1,3.05,8,1.10,'Exploratory temporal-rule follow-up\nSame frozen scores and examined tests; 660 rows')
arrow(5,4.75,5,4.35)
box(.2,.95,4.45,1.4,'External demo, initial protocol\n656 selected people\n195 calibration / 461 test\n180 comparison rows',color='#EAF4EE')
box(5.25,.95,4.45,1.4,'Post-test mapping amendment\nAdded chart Temp / FiO₂\nSame test; 180 further rows\nExploratory, not a fresh test',color='#FBF0E3')
arrow(3.2,3.0,2.4,2.55);arrow(4.8,1.65,5.05,1.65)
ax.text(5,.25,'External test: 444 nonseptic admissions and 17 cases; clinical efficacy not assessed',
        ha='center',fontsize=10.2)
save(fig,'s_study_flow')

manifest={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
          for p in sorted(DATA.glob('*.csv'))}
(ROOT/'result_provenance.json').write_text(json.dumps(manifest,indent=2))
print('Generated',len(list(TAB.glob('*.tex'))),'editable tables and',len(list(FIG.glob('*.pdf'))),'vector figures.')
