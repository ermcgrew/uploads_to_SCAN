#!/usr/bin/env python3

import csv
import flywheel
import logging
import pandas as pd
from uploads_to_SCAN import *


def write_to_upload_tracking_csv(info):
    #add new session info to upload tracker
    with open(upload_tracking_file, "a", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(info)
        logging.info(f"adding {info} to tracking csv.")
    return


def main():
    current_upload_dir = get_current_upload_dir()
    
    receipt_files = [os.path.join(current_upload_dir,x) for x in os.listdir(current_upload_dir) if "receipt" in x]
    logging.basicConfig(filename=f"{current_upload_dir}/update_tracking.log", filemode='w', format="%(levelname)s: %(message)s", level=logging.DEBUG)
    
    fw = flywheel.Client()
    try:
        project = fw.get_project("5c508d5fc2a4ad002d7628d8")  # NACC-SC
    except flywheel.ApiException as e:
        logging.error(f"Flywheel Connection Error: {e}")

    for file in receipt_files:
        receipt_df=pd.read_csv(file)
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
                write_to_upload_tracking_csv(addtototal)
            
                # tag session in flywheel
                try:
                    sessions = project.sessions.find(f'label={session_label}')  
                except flywheel.ApiException as e:
                    logging.error(f"{session_label}: Error finding flywheel session: {e}")
                
                for session in sessions: 
                    scan_tag = "Shared_to_SCAN"
                    if scan_tag not in session.tags:
                        try:
                            session.add_tag(scan_tag)
                            logging.info(f"{session_label}: added tag sucessfully") 
                        except:
                            logging.error(f"{session_label}: An error occurred when tagging.")
                    else:
                        logging.debug(f"{session_label}: already tagged.")

main()