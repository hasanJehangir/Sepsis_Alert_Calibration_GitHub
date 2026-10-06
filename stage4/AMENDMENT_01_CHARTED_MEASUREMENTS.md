# Post-result amendment 01: charted temperature and FiO2

The original external run completed on 30 September 2026 at 21:31:40 UTC and its test results were examined. It is preserved in `results/`, with the original `run_external.py`, protocol and lock unchanged.

The original adapter captured temperature only from the periodic bedside-monitor table. Its feature audit showed temperature observations in 2.1% of scoring rows. Official eICU documentation identifies additional nursing-chart measurements; respiratory charting also includes FiO2 settings. Adding these sources addresses incomplete harmonization. It does not tune or retrain a model, alter the cohort, change the nominal targets or redefine sepsis.

An amended supplementary run will add explicitly Celsius/Fahrenheit-labeled nursing temperatures (convert Fahrenheit to Celsius) and three explicitly FiO2-labeled respiratory fields. Parse numeric values conservatively. For both chart sources, available time is the later of event offset and chart-entry offset. Bin to the next complete hour, keeping the last available observation per channel/hour across all sources. When the same availability time has both Celsius and Fahrenheit chart entries, prefer Celsius to avoid conversion of rounded Fahrenheit duplicates. Nursing-entry time does not prove exactly when a clinician could see the measurement; that assumption remains subject to review.

Keep both native numeric and ambiguity-masked Lactate/Magnesium variants. Retain all 180 comparisons in each run without selecting the more favorable result. The amended evaluation is **post-test exploratory**, and its outcomes cannot be described as an unseen confirmatory validation. Its output is saved separately in `results_amended/`.

The raw release contains 186 hospital surrogate IDs in both patient and hospital tables, whereas the resource overview describes 20 hospitals. Downloaded original files match official checksums and all patient hospital IDs join to the hospital table. The discrepancy remains unresolved. Treat these values as surrogate identifiers and do not claim that their count verifies a clinical hospital count or cross-resource independence.

Human clinical review, source-unit provenance and hospital/patient nonoverlap remain unverified. The amendment must be disclosed if these results are incorporated into a manuscript. No result from the unchanged locked Challenge analysis is altered.
