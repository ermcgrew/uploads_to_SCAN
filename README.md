# uploads_to_SCAN
Program to find and upload SCAN-compliant data to IDA-LONI database from Univeristy of Pennsylvania ADRC.

change download directory date in run.sh line 15
On bscsub cluster:
`bsub < run.sh -o /project/wolk/Prisma3T/relong/uploads_to_SCAN/2023_03_17/output.%J -e /project/wolk/Prisma3T/relong/uploads_to_SCAN/2023_03_17/errors.%J`

Run.sh:
- calls find_sessions_create_csv.py
    - Accesses NACC-SC flywheel project 
    - checks for subjects with MRI-PET pairs or triplets with correct 3T T1 protocol obtained after 2021 
    - downloads dicoms of acquisitions 
    - collects file information and metadata and writes to uploader csv
- unzips dicom.zip files from flywheel
- calls IdaUploader .jar to run upload
 

SCAN: Standardized Centralized Alzheimer’s & Related Dementias Neuroimaging
IDA: Image and Data Archive
LONI: Laboratory of NeuroImaging at University of Southern California
ADRC: Alzheimer's Disease Research Center
