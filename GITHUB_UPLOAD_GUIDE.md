# Upload the complete repository on Windows

1. Extract Sepsis_Complete_GitHub_Code.zip. Open the extracted
   Sepsis_Alert_Calibration_GitHub folder. Its README.md, experiment.py, stage2,
   stage3, stage4 and publication should be directly inside that folder.
2. In GitHub Desktop, choose File > Add Local Repository and select this folder.
   If it is not yet a Git repository, use the offered create-repository option
   for this existing directory. Keep the project files at repository root.
3. Review the changed files. Raw downloads under data/ and stage4/data/ are
   ignored; retained fitted models and study outputs should be included.
4. Commit with a message such as "Add reproducible sepsis evaluation code".
5. Click Publish repository. Choose a name such as
   sepsis-alert-calibration. Make it public for reviewer access, then publish.
6. Open the repository in your browser. Check that README.md, experiment.py,
   stage2/run_stage2.py, stage3/run_followup.py,
   stage4/run_external.py and publication/ are visible. Share that URL.

Upload the extracted project contents, not only the ZIP file. GitHub Desktop
is convenient for this package because it contains many files and arrays.
No GitHub credentials or access token need to be sent to the assistant.

If Git is already installed, the alternative terminal commands from the
extracted project directory are:

```bash
git init
git add .
git commit -m "Add reproducible sepsis evaluation code"
git branch -M main
git remote add origin YOUR_NEW_EMPTY_REPOSITORY_URL
git push -u origin main
```

Replace YOUR_NEW_EMPTY_REPOSITORY_URL with the new repository URL. Use
GitHub's supported sign-in method. Check the .gitignore before committing.
Keep the saved fitted models, predictions and protocol locks; don't regenerate
locks to make a failed check pass.

After publishing, a versioned GitHub release gives reviewers a stable named
snapshot. Archiving a release in a DOI service can add a permanent identifier;
a DOI is not claimed or required to perform the upload above.
