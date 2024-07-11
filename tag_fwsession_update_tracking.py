#!/usr/bin/env python3

import csv
import flywheel
import logging
import pandas as pd
from uploads_to_SCAN import *


def write_to_upload_tracking_csv(info):
    ##add new session info to upload tracker
    with open(upload_tracking_file, "a", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(info)
        logging.info(f"adding {info} to tracking csv.")
    return


def find_fw_object_for_tag(session_label,acquisition_type):
    ### tag session,acquisitions, and files in flywheel
    try:
        sessions = project.sessions.find(f'label={session_label}')  
    except flywheel.ApiException as e:
        logging.error(f"{session_label}: Error finding flywheel session: {e}")
    
    for session in sessions: 
        sess_tag="session_shared_to_SCAN"
        add_tag(session,sess_tag,session_label)

        for acquisition in session.acquisitions():
            acq_tag = "acq_shared_to_SCAN"
            file_tag = "file_shared_to_SCAN"
            if (acquisition_type == "MPRAGE" and "Accelerated Sagittal MPRAGE" in acquisition.label) \
            or (acquisition_type == "FLAIR" and "Sagittal 3D FLAIR" in acquisition.label) \
            or ((acquisition_type != "MPRAGE" and acquisition_type != "FLAIR") and "BR-DY_CTAC" in acquisition.label and "LOCALIZER" not in acquisition.label):
                add_tag(acquisition,acq_tag,session_label)

                ## get dicom file object
                dicom_file_index = [
                    x for x in range(0, len(acquisition.files))
                    if acquisition.files[x].type == "dicom"
                    ][0]
                file_obj = acquisition.files[dicom_file_index]
                add_tag(file_obj,file_tag,session_label)
        

def add_tag(fw_object,scan_tag,session_label):
    if scan_tag not in fw_object.tags:
        try:
            fw_object.add_tag(scan_tag)
            logging.info(f"{session_label}:{fw_object.id}: added tag sucessfully") 
        except:
            logging.error(f"{session_label}:{fw_object.id}: An error occurred when tagging.")
    else:
        logging.debug(f"{session_label}:{fw_object.id}: already tagged.")


def main():
    receipt_files = [os.path.join(current_upload_dir,x) for x in os.listdir(current_upload_dir) if "receipt" in x]
    for file in receipt_files:
        receipt_df=pd.read_csv(file)
        logging.info(f"Reading receipt file: {file}")
        receipt_df.info()
        for index, row in receipt_df.iterrows():
            filepath = row['Directory']
            if row['Status'] != "ARCHIVED": 
                logging.warning(f"Error with uploading session {filepath}")
            else:
                if 'PET' in file:
                    session_label = filepath.split("/")[-1]
                    acquisition_type = session_label.split("x")[-2]
                elif "MRI" in file: 
                    session_acq = filepath.split("/")[-1]
                    session_label = session_acq.split("_")[0]
                    acquisition_type = session_acq.split("_")[1]

                subject = session_label.rsplit("x",3)[0]
                upload_dir_date = current_upload_dir.split("/")[-1]
                addtototal=[acquisition_type, session_label, subject, upload_dir_date]
                
                ## Add successfully uploaded acquisitions to tracking csv
                write_to_upload_tracking_csv(addtototal)
                
                ## Tag successfully uploaded acquisitions in flywheel
                find_fw_object_for_tag(session_label,acquisition_type)


def historic_tag():
    all_uploads=pd.read_csv(upload_tracking_file,header=None,names=['acquisition','session_label','id','date_uploaded'])
    for index, row in all_uploads.iterrows():
        session_label = row['session_label']
        acquisition_type = row['acquisition']
        ##  Tag successfully uploaded acquisitions in flywheel
        find_fw_object_for_tag(session_label,acquisition_type)


## Set up
current_upload_dir = get_current_upload_dir()

logging.basicConfig(filename=f"{current_upload_dir}/update_tracking_csv_tag_in_flywheel_log.txt", filemode='w', format="%(levelname)s: %(message)s", level=logging.DEBUG)

fw = flywheel.Client()
try:
    project = fw.get_project("5c508d5fc2a4ad002d7628d8")  # NACC-SC
except flywheel.ApiException as e:
    logging.error(f"Flywheel Connection Error: {e}")   

main()
# historic_tag()