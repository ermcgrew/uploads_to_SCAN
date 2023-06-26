#!/usr/bin/env python3

import csv
from datetime import datetime,timezone
import flywheel
import logging
import os
from pandas.core.common import flatten


def write_upload_csv(data, scantype, download_directory):
    #write data to csvs to pass to SCAN uploader
    if scantype == "MRI":
        headernames = mri_columns
    elif scantype == "PET":
        headernames = pet_columms
    time = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{download_directory}/{scantype}_sessions_for_SCAN_{time}.csv"
    with open(filename, "w", newline="") as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=headernames)
        csvwriter.writeheader()
        csvwriter.writerows(data)
    return


def write_to_upload_tracking_csv(info):
    #add new session info to upload tracker
    with open(upload_tracking_file, "a", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(info)
        logging.debug(f"adding {info} to tracking csv.")
    return


def read_upload_tracking_csv():
    #read in list of sessions already uploaded
    sessions_uploaded=[]
    with open(upload_tracking_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            sessions_uploaded.append(row[1])

    return sessions_uploaded


def find_pet_metadata(acquisition): 
    #parse through acquisition to get specific pet metadata info
    acq = acquisition.reload()
    
    if "Amyloid" in acq.label:
        tracer = "Florbetaben"
    elif "AV1451" in acq.label:
        tracer = "Flortaucipir"
    else:
        tracer=""
        logging.warning(f"Unable to identify tracer")
    
    dicom_file_index = [
        x for x in range(0, len(acq.files)) if acq.files[x].type == "dicom"
    ][0]
    nifti_file_index = [
        x for x in range(0, len(acq.files)) if acq.files[x].type == "nifti"
    ][0]
    
    try:
        tracer_dose_bec = [acq.files[dicom_file_index].info["RadiopharmaceuticalInformationSequence"]["RadionuclideTotalDose"]]
    except KeyError as e:
        tracer_dose_bec = [0]
        logging.warning(f"Key {e} doesn't exist")
    # conversion to from Becquerel to mCi to tenths place
    tracer_dose_mci = round(tracer_dose_bec[0] * 2.7e-8, 1) 

    try:
        tracer_inj_time = acq.files[dicom_file_index].info[
            "RadiopharmaceuticalInformationSequence"
        ]["RadiopharmaceuticalStartTime"]
    except KeyError as e:
        tracer_inj_time = "000000"
        logging.warning(f"Key {e} doesn't exist")
    tracer_inj_time_formatted = datetime.strftime(datetime.strptime(tracer_inj_time.split(".")[0], "%H%M%S"), "%H:%M:%S")

    #Use nifti_file_index for start time, flywheel's dicom 'AcquisitionTime' may be any of the scan timepoints, not necessarily the first one
    #dcm2niix gear chooses the first of the dicom times to add to the nifit 'AcquisitionTime' field
    try:
        emission_start_time = acq.files[nifti_file_index].info["AcquisitionTime"]
    except KeyError as e:
        emission_start_time = ""
        logging.warning(f"Key {e} doesn't exist") 
    emission_start_time_formatted = emission_start_time.split(".")[0]    
    
    pet_metadata = [tracer, tracer_dose_mci, "000000", tracer_inj_time_formatted, emission_start_time_formatted]
    return pet_metadata

 
def check_sessions(subject):
    # for each subject, upload only if sessions are ABC, 2021 or later, 
    # have 3T with new protocol Accelerated Sagital MPRAGE file and at least one PET session
    check_for_AccSag_acquisition = [[session.label for acquisition in session.acquisitions() if "Accelerated Sagittal MPRAGE (MSV21)" in acquisition.label] 
                for session in subject.sessions() if "3T" in session.label and "ABC" in session.label]
    usable_sessions = list(flatten(check_for_AccSag_acquisition))
    if usable_sessions:    
        # print(f"Subject {subject.label} has AccSag file in 3T scan, checking for PET scans")
        check_for_PET = [session.label for session in subject.sessions() if ("FBBPET" in session.label or "AV1451" in session.label) and "ABC" in session.label and session.timestamp >= datetime(2021,1,1,0,0,0,tzinfo=timezone.utc)]
        if check_for_PET:
            usable_sessions.extend(check_for_PET)
            return(usable_sessions)
    

def main():
    #create folder to hold downloads
    os.system(f'mkdir {download_directory}')

    #make a copy of old tracking list in case it gets messed up during this run
    backup_upload_tracking = upload_tracking_file.replace(".csv",f"_backupcopy_{current_time}.csv")
    os.system(f"cp {upload_tracking_file} {backup_upload_tracking}")

    #list of sessions already uploaded to compare to
    sessions_uploaded = read_upload_tracking_csv()

    # Access flywheel subject list
    fw = flywheel.Client()
    try:
        project = fw.get_project("5c508d5fc2a4ad002d7628d8")  # NACC-SC
    except flywheel.ApiException as e:
        print(f"Error: {e}")
    try:
        subjects = project.subjects.iter_find()  #'created>2022-06-01'
    except flywheel.ApiException as e:
        print(f"Error: {e}")

    for subject in subjects:
        print(f"Subject {subject.label}")
        #if subject has x01, change to .01 for upload csv, to match NACC IDs (subject.label is always a string)
        if "x" in subject.label:
            subjectindd=subject.label.replace("x",'.')
        else:
            subjectindd=subject.label

        usable_sessions = check_sessions(subject)
        if usable_sessions: 
            for session in subject.sessions():
                if session.label in usable_sessions:
                    #check if session has already been added
                    if session.label in sessions_uploaded:
                        logging.info(f"session {session.label} has already been added to SCAN")
                        continue
                    else:
                        if '3T' in session.label:
                            for acquisition in session.acquisitions():
                                # gets both FLAIR and T1 scans
                                if "Sagittal" in acquisition.label: 
                                    logging.debug(f"downloading {session.label} {acquisition.label}")
                                    acquisition_type = acquisition.label.split(' ')[2]
                                    acquisition_directory = download_directory + "/" + session.label + "_" + acquisition_type
                                    os.system(f'mkdir {acquisition_directory}')
                                    acquisition_file = acquisition_directory + "/" + acquisition_type + ".zip"
                                    fw.download_zip([acquisition], acquisition_file, include_types=['dicom'])
                                    mri_data_list = [subjectindd, acquisition_directory, "No"]
                                    mri_list_to_write.append(dict(zip(mri_columns, mri_data_list)))
                                    addtototal_mri=[acquisition_type, session.label, subject.label, current_time]
                                    write_to_upload_tracking_csv(addtototal_mri)
                                    
                        elif 'PET' in session.label:
                            for acquisition in session.acquisitions():
                                if "BR-DY_CTAC" in acquisition.label and "LOCALIZER" not in acquisition.label:
                                    logging.debug(f"downloading {session.label} {acquisition.label}")
                                    acquisition_directory = download_directory + "/" + session.label
                                    os.system(f'mkdir {acquisition_directory}')
                                    acquisition_file = acquisition_directory + "/" + "PET.zip"
                                    fw.download_zip([acquisition], acquisition_file, include_types=['dicom'])
                                    pet_data_list = [
                                        subjectindd,
                                        acquisition_directory,
                                        str(session.timestamp)[:10]
                                    ]
                                    pet_metadata_list = find_pet_metadata(acquisition)
                                    pet_data_list.extend(pet_metadata_list)
                                    pet_list_to_write.append(dict(zip(pet_columms, pet_data_list)))
                                    addtototal_pet=[pet_metadata_list[0], session.label, subject.label, current_time]
                                    write_to_upload_tracking_csv(addtototal_pet)

                else:
                    continue
        else:
            continue

    write_upload_csv(mri_list_to_write, "MRI", download_directory)
    write_upload_csv(pet_list_to_write, "PET", download_directory)


# Global variables
mri_list_to_write = []
pet_list_to_write = []
mri_columns = ["Subject ID", "Directory", "Sedation", "Eyes Open", "Notes"]
pet_columms = [
    "Subject ID",
    "Directory",
    "Scan Date",
    "Tracer",
    "Tracer Dose Assay",
    "Tracer Dose Time",
    "Tracer Inj Time",
    "Emission Start Time",
    "Comments",
]
scan_directory = f"/project/wolk/Prisma3T/relong/uploads_to_SCAN"
upload_tracking_file = f"{scan_directory}/all_sessions_uploaded.csv"
current_time = datetime.now().strftime("%Y_%m_%d")
download_directory = f"{scan_directory}/{current_time}"

#set up logging
logging.basicConfig(filename=f"{scan_directory}/create_csv_{current_time}.log", filemode='w', format="%(levelname)s: %(message)s", level=logging.DEBUG)


main()
