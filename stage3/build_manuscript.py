"""Build the review draft from retained CSV results, without running experiments."""
from pathlib import Path
import shutil
import pandas as pd

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parent
OUT = STAGE / 'manuscript'
OUT.mkdir(exist_ok=True)
prior = pd.read_csv(ROOT / 'stage2/results/main_metrics.csv')
prior = prior[(prior.cap == 'natural') & prior.transfer]
policies = pd.read_csv(STAGE / 'results/policy_metrics.csv')
local = policies[(policies.condition == 'matched_patient') &
                 (policies.anchor == 'local') & (policies.alpha == .1) & policies.transfer]
paired = pd.read_csv(STAGE / 'results/paired_policy_differences.csv')
budgets = pd.read_csv(ROOT / 'stage2/results/budget_summary.csv')
disc = pd.read_csv(ROOT / 'stage2/results/discrimination.csv')

def pct(value): return f'{100 * value:.1f}'
def direction(row): return row.source + r'$\to$' + row.test_site
def table(caption, label, columns, rows, spec, note=''):
    return (r'\begin{table}[htbp]\centering\small' + '\n' +
            r'\caption{' + caption + r'}\label{' + label + '}\n' +
            r'\begin{tabular}{' + spec + r'}\toprule' + '\n' +
            ' & '.join(columns) + r' \\\midrule' + '\n' +
            '\n'.join(' & '.join(map(str, row)) + r' \\' for row in rows) + '\n' +
            r'\bottomrule\end{tabular}' + '\n' +
            (r'\par\vspace{3pt}\begin{minipage}{.98\linewidth}\footnotesize ' + note +
             r'\end{minipage}' if note else '') + '\n' + r'\end{table}' + '\n')

tables = {}
counts = pd.read_csv(ROOT / 'stage2/results/cohort_counts.csv')
rows = []
for site in ['A', 'B']:
    for role in ['train', 'calibration', 'test']:
        r = counts[(counts.site == site) & (counts.role == role)].iloc[0]
        rows.append([site, role.capitalize(), f'{r.patients:,}', f'{r.sepsis:,}',
                     f'{r.patients-r.sepsis:,}', pct(r.sepsis/r.patients)])
tables['cohort'] = table('Eligible reserved cohort by hospital and study role.', 'tab:cohort',
 ['Hospital', 'Role', 'Admissions', 'Septic', 'Nonseptic', r'Sepsis (\%)'], rows, 'llrrrr')
names = {'source_hourly':'Source hours', 'source_patient':'Source admissions',
         'target_patient_all':'Local admissions'}
rows = []
for source, target in [('A','B'),('B','A')]:
    for policy in names:
        r = prior[(prior.source == source) & (prior.test_site == target) &
                  (prior.model == 'hgb') & (prior.policy == policy)].iloc[0]
        rows.append([direction(r), names[policy],
          f'{int(r.patient_false_alert_rate_count)}/{int(r.nonseptic_patients)}',
          pct(r.patient_false_alert_rate),
          f'{pct(r.patient_false_alert_rate_ci_low)}--{pct(r.patient_false_alert_rate_ci_high)}',
          pct(r.window6_sensitivity), pct(r.first6_sensitivity)])
tables['transfer'] = table('Locked analysis: full-feature boosting under natural observation duration.',
 'tab:transfer', ['Transfer', 'Calibration unit', 'False alerts', r'FA (\%)',
 r'95\% CI', r'Any-6 (\%)', r'First-6 (\%)'], rows, 'llrrrrr',
 r'False alerts count nonseptic admissions with at least one crossing. Any-6 and First-6 are case proportions for any crossing and the first crossing, respectively, in the six hours before reconstructed onset. Case denominators are 154 for A$\to$B and 260 for B$\to$A. Hourly and admission targets concern different events.')
model_names = {'logistic':'Logistic', 'hgb':'Boosting', 'hgb_no_observation_features':'Reduced boosting'}
rows = []
for source, target in [('A','B'),('B','A')]:
    for model in model_names:
        r = disc[(disc.cap == 'natural') & (disc.source == source) &
                 (disc.test_site == target) & (disc.model == model)].iloc[0]
        rows.append([direction(r), model_names[model], f'{r.hourly_auroc:.3f}',
                     f'{r.hourly_average_precision:.3f}', f'{r.hourly_brier:.4f}',
                     pct(r.hourly_positive_prevalence)])
tables['disc'] = table('Hourly discrimination and Brier score in the transferred test cohorts.',
 'tab:disc', ['Transfer', 'Model', 'AUROC', 'AP', 'Brier', r'Positive hours (\%)'],
 rows, 'llrrrr', 'AP denotes average precision. Hours are clustered within admissions. These descriptive hourly metrics do not establish admission-level error control or probability calibration.')
rows = []
for source, target in [('A','B'),('B','A')]:
    for budget in [100,250,500]:
        d = budgets[(budgets.cap == 'natural') & (budgets.source == source) &
                    (budgets.test_site == target) & (budgets.model == 'hgb') & (budgets.budget == budget)].set_index('endpoint')
        f, w = d.loc['patient_false_alert_rate'], d.loc['window6_sensitivity']
        rows.append([source + r'$\to$' + target, budget, pct(f['median']),
                     f'{pct(f["p05"])}--{pct(f["p95"])}', pct(w['median']),
                     f'{pct(w["p05"])}--{pct(w["p95"])}'])
tables['budgets'] = table('Locked analysis: full-feature boosting with small local calibration budgets.',
 'tab:budgets', ['Transfer', 'Budget', r'FA median (\%)', 'FA 5th--95th',
 r'Any-6 median (\%)', 'Any-6 5th--95th'], rows, 'lrrrrr',
 'Budgets count completed admissions sampled before retaining nonseptic records. Twenty fixed, nested samples were used per budget. The 5th--95th percentiles describe variability across those samples on the same test cohort; they are not population confidence intervals.')
policy_names = {'hourly':'Hourly', 'single':'Single', 'silence4':'Silence 4 h',
                'silence6':'Silence 6 h', 'three_of_five':'Three of five'}
rows = []
for source, target in [('A','B'),('B','A')]:
    for policy in policy_names:
        r = local[(local.source == source) & (local.test_site == target) &
                  (local.model == 'hgb') & (local.policy == policy)].iloc[0]
        rows.append([direction(r), policy_names[policy], pct(r.patient_false_alert_rate),
          f'{int(r.nonseptic_alerts):,}', f'{r.nonseptic_alerts_per_100_hours:.3f}',
          pct(r.window6_sensitivity), pct(r.first6_sensitivity)])
tables['policies'] = table(r'Exploratory follow-up: alert rules at a nominal local 10\% admission false-alert target, full-feature boosting.',
 'tab:policies', ['Transfer', 'Rule', r'FA (\%)', 'Emissions', '/100 h',
 r'Any-6 (\%)', r'First-6 (\%)'], rows, 'llrrrrr',
 r'Thresholds are recalibrated for each rule using separate local nonseptic calibration admissions. Hourly, single and silencing rules share their threshold because they preserve the first crossing. Emissions and /100 h concern only nonseptic records (110,910 scoring hours for A$\to$B; 112,566 for B$\to$A). This section reuses previously examined test records.')
endpoint_names = {'false_alert':'Admission FA (pp)', 'window6':'Any-6 (pp)',
                  'first6':'First-6 (pp)', 'negative_alerts_per_admission':'Emissions/admission'}
rows = []
for source, target in [('A','B'),('B','A')]:
    for endpoint, name in endpoint_names.items():
        r = paired[(paired.source == source) & (paired.test_site == target) &
                   (paired.model == 'hgb') & (paired.comparison == 'three_of_five_minus_hourly_local10') &
                   (paired.endpoint == endpoint)].iloc[0]
        mult = 1 if endpoint == 'negative_alerts_per_admission' else 100
        rows.append([direction(r), name, f'{mult*r.difference:+.2f}',
                     f'{mult*r.ci_low:+.2f} to {mult*r.ci_high:+.2f}'])
tables['paired'] = table(r'Exploratory paired differences: three-of-five minus hourly, at the local 10\% target.',
 'tab:paired', ['Transfer', 'Endpoint', 'Difference', r'95\% interval'], rows, 'llrr',
 'pp denotes percentage points. Intervals use 2,000 paired admission-bootstrap draws, stratified by outcome and conditional on fitted models and thresholds. They omit calibration uncertainty and multiplicity adjustment. Emissions/admission is a mean difference for nonseptic admissions.')
for key, content in tables.items():
    (OUT / f'table_{key}.tex').write_text(content)
for origin, name in [('stage2/results/transfer_comparison.png','transfer_comparison.png'),
                     ('stage3/results/alert_burden.png','alert_burden.png'),
                     ('stage3/results/workload_detection.png','workload_detection.png')]:
    shutil.copy2(ROOT / origin, OUT / name)

text = r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=24mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern,graphicx,booktabs,amsmath,microtype,float,caption}
\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}
\usepackage{fancyhdr}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small Sepsis alert calibration}
\fancyhead[R]{\small Research draft: author review required}
\fancyfoot[C]{\thepage}\setlength{\headheight}{14pt}
\setlength{\parskip}{4pt}\setlength{\parindent}{0pt}
\captionsetup{font=small,labelfont=bf}
\title{Admission-Level False-Alert Calibration and Alert-Policy Trade-offs in Cross-Hospital Sepsis Prediction}
\author{Research manuscript draft prepared for Hasan Jehangir\\\small Author list and affiliations require verification}
\date{30 September 2026}
\begin{document}
\maketitle
\begin{center}\small\textbf{Status: computational study completed; exploratory follow-up completed; independent external validation pending.}\end{center}
\begin{abstract}
\textbf{Background:} Repeated hourly predictions can expose many nonseptic admissions to an alert even when the hourly false-positive fraction is small. Hospital transfer and temporal alert rules further complicate interpretation of apparent false-alert reductions.

\textbf{Methods:} We analyzed 36,658 eligible adult admissions from the public PhysioNet Challenge 2019 data, excluding a separate 3,000-record development pilot. Models were fitted separately for hospitals A and B using disjoint training, calibration and test partitions. A locally locked analysis compared standard finite-rank thresholds on nonseptic hourly scores or admission maxima, source-to-target transport, and calibration budgets. A subsequent, explicitly exploratory analysis reused the examined test cohorts to compare hourly, single, four-hour silencing, six-hour silencing and an adapted three-of-five warning rule. It retained 660 policy-level comparisons across six frozen source/model combinations, two test hospitals and multiple threshold conditions.

\textbf{Results:} For full-feature gradient boosting, source admission calibration yielded nonseptic admission false-alert rates of 7.5\% for A$\to$B and 31.2\% for B$\to$A. Local admission calibration yielded 10.4\% and 11.1\%, with any-alert sensitivity in the six-hour pre-onset window of 44.8\% and 36.2\%; first-alert sensitivity was 5.2\% and 7.7\%. At this local nominal 10\% target, four-hour silencing reduced nonseptic alert emissions by 68.3\% and 57.5\%, preserving admissions alerted and first-alert timing. After separate recalibration, the three-of-five rule increased nonseptic emissions per admission in both directions. Its first-window sensitivity differences were +2.6 and -2.3 percentage points, with both paired intervals including zero.

\textbf{Conclusions:} Admission-level calibration and repeat-alert suppression address distinct outcomes. Threshold transport was asymmetric, and local adaptation did not establish high first-window sensitivity. Results support reporting admissions alerted, emitted-alert burden and timing together. They do not demonstrate a new calibration algorithm, superior clinical warning system or benefit to patients. Independent cohort validation remains necessary.
\end{abstract}
\textbf{Keywords:} sepsis; clinical artificial intelligence; threshold calibration; hospital shift; repeated alerts; retrospective evaluation.

\section{Introduction}
Sepsis prediction systems commonly update risk each hour, whereas clinical attention is directed to patients and emitted warnings. An operating threshold with a small hourly false-positive fraction can still alert a substantial fraction of nonseptic admissions when observation is prolonged. Reducing repeated warnings, reducing the number of patients exposed to a warning, and changing the timing of the first warning are separate objectives. A useful evaluation must keep their denominators and clinical interpretations explicit.

The public PhysioNet/Computing in Cardiology Challenge 2019 provides a reproducible setting for studying this problem across two released hospital datasets \cite{reyna,reynadata}. The prediction target in the released labels already begins six hours before clinical onset. Evaluations that shift these labels again or include post-onset scores can inadvertently change the intended task. The recorded trajectories also differ in duration and measurement availability, making the unit of calibration relevant.

Prior work already addresses important aspects of this question. Evaluation choices materially affect sepsis metrics \cite{do}. Published systems use single-alert evaluation, temporal suppression, warning aggregation or uncertainty-based abstention \cite{moor,composer,gupta}. Standard conformal methods describe finite-sample marginal error control under exchangeability \cite{angelopoulos}. Neither conformal prediction in healthcare nor reducing sepsis false alarms is a new research premise. In particular, an admission-maximum threshold is a standard score transformation followed by a standard order statistic.

We therefore frame this work as a retrospective evaluation of threshold transport and alert-policy trade-offs. The locked component asks whether an admission false-alert target transfers between hospitals, how local calibration sample size affects operating points, and how case detection relates to first-warning timing. The later exploratory component applies literature-grounded temporal rules to the same frozen predictions, both at common thresholds and at comparable nominal admission targets. The proposed contribution is the joint, reproducible comparison of these outcomes; its novelty and generalizability remain provisional.

\section{Methods}
\subsection{Study design and chronology}
This is a retrospective computational study of publicly released, de-identified records. A 3,000-record pilot informed an analysis specification written on 29 September 2026, before opening the remaining reserved records. That specification was locally timestamped and hashed; it was not independently preregistered. The completed locked analysis and its outputs are retained unchanged. After inspecting its test results, we specified and ran an exploratory alert-policy follow-up. No additional model was trained and no new unseen test set was created for that follow-up. The distinction is retained throughout the results.

\subsection{Dataset, cohort and partitions}
The public version 1.0.0 release contains 40,336 subject files \cite{reynadata}. All 3,000 pilot files were excluded from reserved fitting, calibration and testing. The remaining 37,336 files retained deterministic, per-hospital 60\% training, 20\% calibration and 20\% test assignments from the original manifest. Assignments were not redrawn by outcome. Exact raw-file SHA-256 duplicates and matches with pilot records were screened; the reserved eligible cohort contained no exact duplicate hashes. This cannot identify separate admissions belonging to the same person or near-duplicate trajectories.

Eligible records represented adults aged at least 18 years with available scoring hours at ICU hour 6 or later. For positive records, reconstructed onset was the first positive released-label hour plus six hours. Records with a first positive label at hour 6 or earlier were excluded as early or left-censored onset, and onset beyond the observed record was excluded. Of the reserved files, 678 were excluded: 644 for early or left-censored onset, 19 for age below 18 and 15 for onset beyond observation. The resulting 36,658 admissions contributed 1,254,335 eligible scoring hours.

Cases were scored at available hours at least 6 and strictly before reconstructed onset. Nonseptic controls had no positive released label and were scored to their observed record end. Thus ``nonseptic'' refers to the released segment, not a guarantee of no subsequent sepsis. Table~\ref{tab:cohort} gives role-specific counts. No real-world identities are inferred for hospital A or B.
\input{table_cohort.tex}

\subsection{Causal features and fixed model families}
The 120-feature representation used 34 last-observed physiological variables; age, recorded gender, hospital-admission time and ICU hour; 34 current-measurement indicators; 34 elapsed-measurement-time variables capped at 168 hours; and seven six-hour rolling means and seven six-hour changes for vital signs. Forward filling and rolling summaries used only current and preceding measurements. Entirely unobserved values remained missing for training-only preprocessing or native missing-value handling. Unit identifiers and outcomes were not features.

Three prespecified models were fitted separately on each hospital. Logistic regression used training-only median imputation retaining empty features, standard scaling, an L2 penalty with $C=1$, LBFGS, 1,000 maximum iterations and tolerance $10^{-5}$. Histogram gradient boosting used 200 iterations, learning rate 0.07, at most 15 leaves, at least 40 samples per leaf, L2 regularization 1, no early stopping and seed 20260929. A reduced boosting model removed the 68 measurement indicators/ages and ICU hour, retaining 51 features. This ablation does not remove all information about missingness. No class weighting, resampling, hyperparameter search or test-driven model selection was used. All six fits converged without recorded warnings. Longer admissions contributed more training rows because hourly observations were not patient-weighted.

\subsection{Threshold calibration and hospital transfer}
For admission $i$, let $p_{it}$ be a frozen model score and $M_i=\max_t p_{it}$ over its eligible scoring hours. Using $n$ nonseptic calibration admissions, the nominal false-alert target $\alpha$ gives rank
\[
k=\left\lceil(n+1)(1-\alpha)\right\rceil,\qquad
\theta=M_{(k)}.
\]
If $k>n$, $\theta=+\infty$. An alert requires a score strictly greater than $\theta$, preserving conservative handling of ties. This standard finite-rank construction offers marginal control for a new exchangeable nonseptic admission and a model fitted separately from calibration \cite{angelopoulos}. It does not guarantee control for an arbitrary fixed threshold, under hospital shift, or under future temporal drift.

The locked analysis compared source hourly calibration, source admission calibration, and all-local admission calibration at $\alpha=0.10$. Source hourly calibration used the same rank rule on pooled nonseptic hours; dependence and duration weighting prevent an independent-hour interpretation. Empirical admission quantiles with rank $\lceil n(1-\alpha)\rceil$ were retained to isolate the small finite-rank correction from the change in calibration unit. Source thresholds were applied without modification to both source and other-hospital test cohorts.

Local calibration used disjoint, retrospectively labeled, completed admissions from the target hospital. Budgets of 100, 250 and 500 admissions were sampled without replacement using 20 fixed nested permutations; only nonseptic admissions within each sample determined its threshold. This is label-informed recalibration, not outcome-free adaptation. A separate source-calibration threshold targeted at least 80\% empirical any-alert sensitivity within the six-hour window. It is a descriptive reference rather than a test sensitivity guarantee.

Natural record duration was primary. Secondary administrative caps at ICU hours 24, 48 and 72 were applied to calibration and evaluation alike. Case denominators included only reconstructed onset at or before each cap; later-onset cases were excluded, not relabeled negative. Caps therefore define retrospective conditional cohorts, not complete fixed prospective follow-up.

\subsection{Exploratory alert-policy comparisons}
Five causal emission rules were evaluated: every eligible hourly crossing; only the first crossing per admission; four-hour silencing; six-hour silencing; and three warnings in the current and previous four hours. For silencing, an emission at hour $t$ permits the next emission at $t+4$ or $t+6$, respectively. These structures are motivated by published evaluation and alert designs \cite{do,moor,composer,gupta}. We adapt rules, not the papers' models, training samples, outcome windows or reported performance.

For the three-of-five adaptation, an hour is eligible when at least three scores in $[t-4,t]$ exceed the threshold. Partial startup windows can qualify once three observations exist. Every eligible hour emits; there is no invented reset or clinician-response mechanism. Equivalently, transform each hour to its third-largest score in that window, treating unavailable startup positions as $-\infty$, then calibrate its admission maximum. This explicit adaptation need not reproduce the complete SepsisAI implementation \cite{gupta}.

Each rule was evaluated at the unchanged source-hourly, source-admission, local-admission and source-80\%-sensitivity thresholds, and at 0.5 as a model-scale reference. The 0.5 reference is not a reproduction of another system's probability threshold. Separately, admission thresholds were fitted for each rule at nominal targets of 5\%, 10\% and 20\%, using source or local calibration. Hourly, single and silencing rules preserve the first crossing and therefore share an admission calibration threshold. The resulting design retained 660 policy-level rows, including internal controls and all model/direction combinations. No best rule was selected from these test outcomes.

\subsection{Outcomes, uncertainty and implementation verification}
Admission false-alert rate was the fraction of nonseptic admissions receiving at least one emission. Burden was measured as nonseptic emissions per admission and per 100 observed eligible nonseptic hours. Case endpoints distinguished any emitted alert in $[\mathrm{onset}-6,\mathrm{onset})$ from the first emitted alert in that window. Earlier first warnings, corresponding twelve-hour endpoints and lead times among alerted cases were also retained. An early warning is not automatically clinically useless; six-hour first-warning sensitivity is a timing diagnostic rather than a complete clinical-utility definition.

Individual patient proportions have exact two-sided 95\% binomial intervals. Paired comparisons used 2,000 admission-bootstrap draws stratified by outcome. Exploratory comparisons contrasted three-of-five and both silencing rules with hourly at the local 10\% target. Intervals are descriptive, conditional on fitted models and thresholds, omit calibration uncertainty and have no multiplicity correction. Budget percentiles summarize the 20 calibration samples on the same test records and are not population confidence intervals. No independent-hour intervals were used for emitted-alert burden.

Fourteen locked-study checks and six additional policy checks passed. Tests covered causal rolling eligibility, strict crossings, startup ineligibility, silence boundaries and single-alert timing. An independent direct-crossing audit matched all 72 natural-duration locked anchors. The follow-up also matched those anchors and verified actual-data invariants: common-threshold hourly, single and silencing rules have identical admissions alerted and first-alert counts; suppression cannot increase emissions; and single-alert any-window counts equal first-window counts. Inputs, code, protocol and completion metadata are hashed and retained.

\section{Results}
\subsection{Locked analysis: calibration unit and asymmetric transport}
Full-feature boosting illustrates the main transport results (Table~\ref{tab:transfer}; Figure~\ref{fig:transfer}). Source-hourly calibration produced admission false-alert rates of 22.9\% in A$\to$B and 60.3\% in B$\to$A. Replacing hours with source admission maxima reduced these rates to 7.5\% and 31.2\%, but six-hour any-alert sensitivity also fell, from 55.8\% to 42.9\% and from 83.1\% to 58.8\%. These changes compare different nominal error events and do not show improved discrimination.

All three model families displayed the same direction of source-admission threshold transport: rates below 10\% in A$\to$B and above 10\% in B$\to$A. For the latter direction, source-admission rates ranged from 31.2\% to 48.9\%. Local admission calibration brought natural-duration test rates to 10.2--11.1\% across the six transferred model fits. The finite-rank versus empirical admission-quantile correction changed full-calibration natural-duration false-alert rates by at most 0.06 percentage points. Most of the observed operating-point difference therefore concerned the calibration unit and site, rather than the extra rank correction.
\input{table_transfer.tex}
\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{transfer_comparison.png}
\caption{Locked-study calibration comparisons for full-feature boosting in both hospital transfers. The endpoints distinguish nonseptic admissions alerted, any warning in the six-hour pre-onset window and the first warning in that window. See the retained CSV tables for exact intervals and all models.}\label{fig:transfer}\end{figure}

\subsection{Locked analysis: timing, discrimination and local sample size}
At all-local admission calibration, full-feature boosting detected any six-hour-window crossing in 69/154 cases (44.8\%) in A$\to$B and 94/260 (36.2\%) in B$\to$A. The first crossing occurred in that window in only 8/154 (5.2\%) and 20/260 (7.7\%). Earlier first crossings occurred in 44.8\% and 40.4\% of cases. Extending the first-crossing window to twelve hours yielded 11.7\% and 11.2\%, respectively. Thus a repeated window crossing often followed a substantially earlier initial warning.

In B$\to$A, local versus source admission calibration changed the full-feature boosting admission false-alert rate by -20.1 percentage points (paired 95\% interval -21.4 to -18.6) and six-hour any-alert sensitivity by -22.7 points (-28.1 to -17.7). The first-window difference was +0.4 points, with its interval including zero. Discrimination remained modest across transferred models (Table~\ref{tab:disc}); threshold adaptation did not alter the ranking of their predictions. Smaller calibration samples showed substantial conditional operating-point variability (Table~\ref{tab:budgets}). All sample results, observation caps, sensitivity references and internal-site controls are retained in the companion results, rather than interpreted as independent replications.
\input{table_disc.tex}
\input{table_budgets.tex}

\subsection{Exploratory follow-up: repetition and admissions alerted}
At a nominal local 10\% admission target, full-feature boosting emitted 4,093 nonseptic hourly alerts in A$\to$B and 1,736 in B$\to$A. Four-hour silencing reduced these to 1,298 and 737: reductions of 68.3\% and 57.5\% (Table~\ref{tab:policies}; Figure~\ref{fig:burden}). Admission false-alert rates and first-warning timing were unchanged by construction. Any emitted six-hour-window alert decreased from 44.8\% to 43.5\% and from 36.2\% to 34.6\%. Six-hour silencing reduced emissions further, with any-window sensitivity of 43.5\% and 33.8\%.

Retaining only one warning reduced nonseptic emissions to 362 and 380, but its any-window sensitivity became equal to first-window sensitivity: 5.2\% and 7.7\%. This is an evaluation consequence of removing later alerts, not evidence that their underlying scores disappeared. Figure~\ref{fig:workload} displays the jointly observed admission and detection operating points at three nominal local targets; these are descriptive points rather than an optimized frontier.
\input{table_policies.tex}
\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{alert_burden.png}
\caption{Exploratory nonseptic alert-emission burden at the nominal local 10\% admission target, full-feature boosting. Text in bars gives the observed percentage of nonseptic admissions alerted. Suppression preserves that percentage while reducing repeated emissions. The three-of-five rule is separately recalibrated and emits at every eligible hour.}\label{fig:burden}\end{figure}
\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{workload_detection.png}
\caption{Exploratory observed admission false-alert rate versus six-hour any-emission sensitivity at nominal local targets of 5\%, 10\% and 20\%, full-feature boosting. Lines connect the three evaluated targets; they are not fitted optimal frontiers. Each rule is calibrated separately on the same held-out local calibration pool.}\label{fig:workload}\end{figure}

\subsection{Exploratory follow-up: warning aggregation after recalibration}
The three-of-five adaptation yielded admission false-alert rates of 10.7\% and 11.7\% after local calibration. Its six-hour any-emission sensitivity was 45.5\% and 37.7\%, while first-window sensitivity was 7.8\% and 5.4\%. Compared with hourly, first-window changes were +2.6 points in A$\to$B and -2.3 in B$\to$A; both paired intervals included zero (Table~\ref{tab:paired}). Nonseptic emissions increased to 5,145 and 2,915. Mean increases per nonseptic admission were 0.30 (95\% interval 0.25 to 0.35) and 0.34 (0.29 to 0.40). This recurrent eligibility rule did not establish a consistent timing advantage.

At the unchanged source-admission threshold, three-of-five instead reduced the admission false-alert rate from 7.5\% to 4.2\% in A$\to$B and from 31.2\% to 20.6\% in B$\to$A, while reducing any-window sensitivity from 42.9\% to 39.0\% and from 58.8\% to 50.0\%. Those apparent improvements concern stricter eligibility at an unmatched operating point. After matching nominal local targets, all three model families had more nonseptic emissions per 100 hours under three-of-five than under hourly. This does not prove clinical harm or characterize a differently implemented published system.
\input{table_paired.tex}

\section{Discussion}
The central empirical finding is that the unit and site of calibration matter for the observable event being controlled. A threshold calibrated on nonseptic hours should not be interpreted as a target on admissions with any alert. An admission-maximum threshold aligns the calibration unit with that event, but its target did not transfer symmetrically between the two public hospitals. Local completed-admission calibration brought operating points closer to the nominal target while sometimes sacrificing substantial case-window detection. This is an operating-point adaptation, not an improvement in model discrimination.

The exploratory temporal comparisons separate an additional source of misleading interpretation. Suppression can sharply reduce the number of emitted warnings while preserving every admission's first warning. Reporting only repeated-alert burden could suggest that fewer patients were exposed to a false warning, although that event was unchanged. Conversely, a single-alert evaluation removes later window detections and exposes the weak alignment of first-warning times with the selected six-hour window. Earlier warnings might be valuable or unhelpful in practice; these retrospective records cannot establish either interpretation.

Three-of-five aggregation also illustrates why fixed-threshold and matched-target comparisons answer different questions. At a common raw threshold, it removes isolated exceedances and generally creates stricter eligibility. Recalibrating its transformed admission score lowers its threshold, which can restore admissions alerted while allowing many successive eligible hours. Under our explicitly recurrent implementation this increased emissions. A reset, episode definition or clinician-triggered acknowledgement could change the result, but introducing those mechanisms after seeing the test outcomes would require another explicitly exploratory analysis and eventual fresh validation.

These findings complement existing work on evaluation strategy and practical alarm rules \cite{do,moor,composer,gupta}. They should not be advertised as the first use of conformal methods in sepsis or as a novel general-purpose conformal algorithm. The study currently offers a reproducible application and a compact comparison of transport, calibration budgets, alert repetition and timing. A focused novelty review and validation in a genuinely independent cohort are required to assess whether that empirical contribution is sufficient for a journal research article.

Several limitations constrain interpretation. Only two historical public hospital datasets were used, and record-level splits cannot exclude related admissions. Exact-hash screening detects identical files, not patient overlap. Source A/B transfer is geographic dataset validation within one challenge resource, not an additional external cohort. Released labels are retrospective approximations; reconstructed onset, early-case exclusion and record censoring shape the task. Temporal splits, prospective outcomes, subgroup fairness and clinical workflow effects were not assessed. Longer stays contributed more training rows and more opportunity to alert. The reduced-feature ablation still contains implicit measurement-process information.

Confidence intervals condition on model and threshold estimates, and the large number of descriptive comparisons was not multiplicity-adjusted. The policy follow-up reused examined test records and cannot supply new confirmatory evidence. Actual local test rates can exceed the nominal target even under a valid marginal procedure, and no error-control guarantee under hospital shift is claimed. Scoring-hour denominators are observed, selected record segments, rather than a prospectively sampled deployment population. We therefore do not estimate clinical treatment benefit, intervention effects, prospective positive predictive value or an official Challenge leaderboard score. Independent validation should audit hospital and patient overlap, harmonize labels and features, and lock its evaluation before examining outcomes.

\section{Conclusion}
In these two released hospitals, standard admission-level calibration changed false-alert exposure but did not yield reliable cross-hospital transport or high first-window sensitivity. Repeat-alert suppression reduced emissions while preserving admissions alerted; warning aggregation did not consistently improve timing at comparable nominal admission targets. An interpretable sepsis evaluation should report patient exposure, emitted-alert burden and first-warning timing together. This research draft requires author verification and independent cohort validation before a submission decision.

\section*{Declarations and author verification}
\textbf{Ethics and consent:} The analysis uses publicly released de-identified data. The eventual authors must obtain and document their institution's determination concerning ethics review and consent requirements. This draft asserts neither ethics approval nor exemption.

\textbf{Authorship, affiliations and contributions:} The final author list, institutional affiliations and individual contributions have not been verified. The named recipient of this draft does not establish an author contribution or an institutional endorsement.

\textbf{Funding and competing interests:} Project-specific statements require confirmation from every eventual author. No funding or conflict declaration from another project has been imported.

\textbf{Data and code availability:} Source data are available from PhysioNet, version 1.0.0, under CC BY 4.0 \cite{reynadata,pollard}. The companion package retains exact frozen inputs, source code, protocols, test outcomes and CSV results. A public repository or archival DOI has not yet been established; journal-required deposition should precede final submission. No credentialed patient dataset was accessed for this follow-up.

\textbf{AI assistance:} An OpenAI Codex assistant helped implement computational analyses and prepare this manuscript draft. The eventual human authors must independently review the code, numerical findings, citations and text, determine the journal's required disclosure, and take responsibility for the submitted work. The assistant is not an author. No CAPMI material was used.

\begin{thebibliography}{9}
\bibitem{reyna} Reyna MA, Josef CS, Jeter R, et al. Early Prediction of Sepsis From Clinical Data: The PhysioNet/Computing in Cardiology Challenge. \textit{Critical Care Medicine}. 2020;48(2):210--217. \href{https://doi.org/10.1097/CCM.0000000000004145}{doi:10.1097/CCM.0000000000004145}.
\bibitem{reynadata} Reyna M, Josef C, Jeter R, et al. Early Prediction of Sepsis from Clinical Data: The PhysioNet/Computing in Cardiology Challenge 2019. PhysioNet; 2019. Version 1.0.0. \href{https://doi.org/10.13026/v64v-d857}{doi:10.13026/v64v-d857}.
\bibitem{do} Do DK, et al. The Impact of Evaluation Strategy on Sepsis Prediction Model Performance Metrics in Intensive Care Data: Retrospective Cohort Study. \textit{Journal of Medical Internet Research}. 2026;28:e72083. \href{https://doi.org/10.2196/72083}{doi:10.2196/72083}.
\bibitem{moor} Moor M, Bennett N, Plecko D, et al. Predicting sepsis using deep learning across international sites: a retrospective development and validation study. \textit{eClinicalMedicine}. 2023;62:102124. \href{https://doi.org/10.1016/j.eclinm.2023.102124}{doi:10.1016/j.eclinm.2023.102124}.
\bibitem{composer} Shashikumar SP, Wardi G, Malhotra A, Nemati S. Artificial intelligence sepsis prediction algorithm learns to say ``I don't know''. \textit{npj Digital Medicine}. 2021;4:134. \href{https://doi.org/10.1038/s41746-021-00504-6}{doi:10.1038/s41746-021-00504-6}.
\bibitem{gupta} Gupta A, et al. Improving sepsis prediction in intensive care with SepsisAI: A clinical decision support system with a focus on minimizing false alarms. \textit{PLOS Digital Health}. 2024;3(8):e0000569. \href{https://doi.org/10.1371/journal.pdig.0000569}{doi:10.1371/journal.pdig.0000569}.
\bibitem{angelopoulos} Angelopoulos AN, Bates S. A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification. arXiv preprint; 2021. \href{https://arxiv.org/abs/2107.07511}{arXiv:2107.07511}.
\bibitem{pollard} Pollard T, Moody BE, Lehman L, et al. PhysioNet as a global platform for biomedical research. \textit{Nature Health}. 2026;1:792--795. \href{https://doi.org/10.1038/s44360-026-00096-z}{doi:10.1038/s44360-026-00096-z}.
\end{thebibliography}
\end{document}
'''
(OUT / 'Sepsis_Calibration_Manuscript_Draft.tex').write_text(text)
print('Wrote manuscript source and six data-derived tables to', OUT)
