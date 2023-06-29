# uploads_to_SCAN
Program to find and upload SCAN-compliant data to IDA-LONI database from Univeristy of Pennsylvania ADRC. Controlled via *run.sh*


## Run.sh 
### Options
-c     Calls create_csvs function to review Flywheel data for qualifying files and create csv to upload with.
-u     Calls upload_files function to create report on upload numbers, unzips dicom files and uploads dicom files to ida.loni.usc.edu.
-d     Date from folder created in create_csvs function. Required for upload_files function. Format: YYYY_MM_DD.
-h     Prints help."

### Example usage
`bash run.sh -c`
`bash run.sh -d 2023_06_26 -u`

### Functions
Functions are submitted to bscsub cluster queue to run.
**create_csvs** calls *find_sessions_create_csv.py*
    - Accesses NACC-SC flywheel project 
    - checks for subjects with MRI-PET pairs or triplets with correct 3T T1 protocol obtained after 2021 
    - downloads dicoms of acquisitions 
    - collects file information and metadata and writes to uploader csv 
    - adds new file names to csv all_sessions_uploaded.csv to track uploads
**upload_files**
    - calls *parse_tracking_files.sh* to produce statistics report on how many uploads have been done
    - unzips dicom files
    - calls *IdaUploader.jar* to upload files to SCAN


## Procedure
Every 3 months
1. run.sh -c
2. Download PET csv
    a. Get dosage computer data from Ilya
	b. Convert pdf to excel and add new info to total doc
	c. Match dates/times to add info to upload csv using *../Box/SCAN_uploading/dosage_computer_reports/find from dosage computer.ipynb*
	d. upload csv back to cluster
3. Download list of subjects 
    a. Check subject packet status with Nicole
    b. Remove any subjects that haven’t been submitted to NACC yet using code in remove_nacc_issues.sh\
4. Run.sh -d YYYY_MM_DD -u 
5. Download stats.txt and send to NI core slack channel


## Abbreviations
ADRC: Alzheimer's Disease Research Center
IDA: Image and Data Archive
LONI: Laboratory of NeuroImaging at University of Southern California
SCAN: Standardized Centralized Alzheimer’s & Related Dementias Neuroimaging
