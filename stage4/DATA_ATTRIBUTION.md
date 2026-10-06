# Dataset and code attribution

This package redistributes an identified subset of the public eICU-CRD Demo v2.0.1 and the openly released YAIB eICU-demo sepsis inputs. The databases and their derived cohort/timeline/feature data remain subject to ODbL 1.0. A copy is at `data/eicu/LICENSE.txt`. No alternative license overrides those rights or duties.

- Johnson A, Pollard T, Badawi O, Raffa J. **eICU-CRD Demo v2.0.1** (2021). https://physionet.org/content/eicu-crd-demo/2.0.1/ . DOI: https://doi.org/10.13026/4mxk-na84 . Parent database: Pollard et al. Scientific Data (2018), https://doi.org/10.1038/sdata.2018.178 .
- van de Water R, Schmidt H, Elbers P, Thoral P, Arnrich B, Rockenschaub P. **YAIB: Yet Another ICU Benchmark**, ICLR 2024. https://arxiv.org/abs/2306.05109 . Repository: https://github.com/rvandewater/YAIB . Exact commit: `0d1d39a131a65f453aeb019828394396d6bfd171`. Cohort code: https://github.com/rvandewater/YAIB-cohorts . YAIB repo code is MIT (`data/yaib/LICENSE_CODE_MIT.txt`); the released databases are ODbL.

Adaptations here: raw tables selected; numeric units/measurement times mapped to the frozen source feature representation; one stay per person selected; published benchmark labels aligned to scoring hours; original and exploratory amended cohorts/features/timelines and model outputs produced. These were created for research reproducibility and have not been certified clinically.

The six source models were developed in the separate Challenge 2019 study using public Challenge inputs. Source dataset attribution: PhysioNet/Computing in Cardiology Challenge 2019, https://physionet.org/content/challenge-2019/1.0.0/ . Raw Challenge records are not included in this external-evaluation package.

Downloaded-file URL, byte count and SHA256 provenance appears in `download_receipt.json` and `amended_download_receipt.json`; official eICU checksums are preserved. Internal downloaded third-party reference papers and full reference code are excluded from this distribution. The prior project manuscript is a draft for human review, not a published article.
