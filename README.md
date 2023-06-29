# uploads_to_SCAN
Program to find and upload SCAN-compliant data to IDA-LONI database from Univeristy of Pennsylvania ADRC.

## Options for run.sh
- c: Calls create_csvs function to review Flywheel data for qualifying files and create csv to upload with.
- u: Calls upload_files function to create report on upload numbers, unzips dicom files and uploads dicom files to ida.loni.usc.edu.
- d: Date from folder created in create_csvs function. Required for upload_files function. Format: YYYY_MM_DD.
- h: Prints help.

## Functions in run.sh
Functions are submitted to bscsub cluster queue to run.

**create_csvs** calls *find_sessions_create_csv.py*, which:
  - Accesses NACC-SC flywheel project 
  - checks for subjects with MRI-PET pairs or triplets with correct 3T T1 protocol obtained after 2021 
  - downloads dicoms of acquisitions 
  - collects file information and metadata and writes to uploader csv 
  - adds new file names to csv all_sessions_uploaded.csv to track uploads
  
**upload_files**
  - calls *parse_tracking_files.sh* to produce statistics report on how many uploads have been done
  - unzips dicom files
  - calls *IdaUploader.jar* to upload files to SCAN

***
## Procedure
1. Every 3 months, do `bash run.sh -c` to check for new sessions and create csvs.
2. Edits to PET csv:
    - Download PET csv
    - Get dosage computer data from Ilya
    - Convert pdf to excel and add new info to total doc
    - Match dates/times to add info to upload csv using *../Box/SCAN_uploading/dosage_computer_reports/find from dosage computer.ipynb*
    - upload csv back to cluster
3. Check for any subjects without NACC packet:
    - Download list of subjects 
    - Check subject packet status with Nicole
    - Remove any subjects that haven’t been submitted to NACC yet using code in *remove_nacc_issues.sh*
4. `bash run.sh -d YYYY_MM_DD -u` 
5. Download *stats_YYYY_MM_DD.txt* and send to NI core slack channel.
***
## Abbreviations
- ADRC: Alzheimer's Disease Research Center
- IDA: Image and Data Archive
- LONI: Laboratory of NeuroImaging at University of Southern California
- SCAN: Standardized Centralized Alzheimer’s & Related Dementias Neuroimaging
