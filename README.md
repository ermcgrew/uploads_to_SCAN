# uploads_to_SCAN
Program to find and upload SCAN-compliant data to IDA-LONI database from Univeristy of Pennsylvania ADRC.

## Options for run.sh
- a: Calls add_info function to add NACCIDs to both sheets and dosage computer info to PET csv. 
- c: Calls create_csvs function to review Flywheel data for qualifying files and create csv to upload with.
- u: Calls upload_files function to create report on upload numbers, unzips dicom files and uploads dicom files to ida.loni.usc.edu.
- d: Date from folder created in create_csvs function. Required for upload_files function. Format: YYYY_MM_DD.
- h: Prints help.

## Functions in run.sh
Functions are submitted to bscsub cluster queue to run.

**add_info** calls *add_dosage_naccid.py*, which: 
  - for PET csv, adds missing Dose Time, Inj Time, and Dose Assay, based on dosage_computer_info.csv
  - for PET and MRI csv, adds NACCID to Subject ID field. 

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
2. Dosage computer data 
    - Get dosage computer data from Ilya for the last 3 months.
    - Convert pdf to excel.
    - Edit columns and merge into existing dosage_master.csv using a copy of *../Box/SCAN_uploading/dosage_computer_reports/find from dosage computer_YYYYMMDD.ipynb*
    - upload new dosage_master.csv to cluster *uploads_to_SCAN/YYYY_MM_DD/*
3. NACCIDs:
    - Ask Nicole for updated nacc_id to PTID mapping.
    - upload new nacc_id_ptid.csv to cluster *uploads_to_SCAN/YYYY_MM_DD/*
4. `bash run.sh -a` 
5. For any sessions still missing PET data, check manually and fill in or remove row from upload.
6. `bash run.sh -d YYYY_MM_DD -u` 
7. Download *stats_YYYY_MM_DD.txt* and send to NI core slack channel.
***
## Abbreviations
- ADRC: Alzheimer's Disease Research Center
- IDA: Image and Data Archive
- LONI: Laboratory of NeuroImaging at University of Southern California
- SCAN: Standardized Centralized Alzheimer’s & Related Dementias Neuroimaging
