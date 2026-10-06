# Sepsis research source code — reduced download

This is the source-only edition of Hasan Jehangir's sepsis false-alert calibration research project. It accompanies a draft manuscript; publication and clinical effectiveness are not established.

All 29 original Python source files and all three original notebooks are included without changes. Configurations, dataset roles, download receipts, protocols, author statements and documentation are included. The large saved models, prediction vectors, feature arrays, result CSV tables, PDFs and image files are excluded to make downloading easier. This is NOT the complete numerical reproduction archive.

## Upload to GitHub

Extract Sepsis_Source_Only.zip, open the Sepsis_Alert_Calibration_GitHub folder and upload its contents. Describe the repository as source code with archived outputs supplied separately. For many files, use GitHub Desktop. Do not upload a ZIP in place of the extracted source files.

## Plain-text alternative

Restore_Sepsis_Source.txt is a standalone Python script containing the identical source ZIP. Save it as Restore_Sepsis_Source.py and run:

    python Restore_Sepsis_Source.py

It uses only Python's standard library, verifies the embedded ZIP digest, and creates Sepsis_Source_Upload in the current directory. It refuses to overwrite an existing destination. No network access is needed for this extraction.

## Research execution

The recorded analysis used Python 3.12. Install dependencies with:

    python -m pip install -r requirements_complete.txt

The original reproduction wrappers, original repository verifier, manuscript builders and notebook instructions expect files from the complete archived project. They cannot reproduce or verify the recorded numerical results using this reduced source package alone. The original full-package README is preserved as README_FULL_ARCHIVE.md and describes that full version. The original REPOSITORY_MANIFEST.json describes the full version and is not the manifest for this source-only edition.

Public-data download scripts remain available, but data acquisition and fitting take time; downloading the public inputs alone does not restore saved result arrays or models. Do not treat newly generated outputs as the original recorded study outputs. Do not alter frozen protocol records to bypass missing inputs.

SOURCE_PACKAGE_MANIFEST.json lists the exact bytes in this reduced edition. The study code and results were not changed when creating this download. No CAPMI material is included.
