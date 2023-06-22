#!/usr/bin/env python3

import csv
from datetime import datetime,timezone
import flywheel
import logging
import os
from pandas.core.common import flatten


def write_upload_csv(data, scantype, download_directory):
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


def add_to_master_list(info):
    with open(master_upload_list, "a", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(info)


def find_pet_metadata(acquisition): 
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

    # pet_times_list=["000000"] ## fake data to hold place for Tracer Dose Time from dosage computer, entered manually 

    try:
        tracer_inj_time = acq.files[dicom_file_index].info[
            "RadiopharmaceuticalInformationSequence"
        ]["RadiopharmaceuticalStartTime"]
    except KeyError as e:
        tracer_inj_time = "000000"
        logging.warning(f"Key {e} doesn't exist")
    # pet_times_list.append(tracer_inj_time)
    tracer_inj_time_formatted = datetime.strftime(datetime.strptime(tracer_inj_time.split(".")[0], "%H%M%S"), "%H:%M:%S")

    #Use nifti_file_index for start time, flywheel's dicom 'AcquisitionTime' may be any of the scan timepoints, not necessarily the first one
    #dcm2niix gear chooses the first of the dicom times to add to the nifit 'AcquisitionTime' field
    try:
        emission_start_time = acq.files[nifti_file_index].info["AcquisitionTime"]
    except KeyError as e:
        emission_start_time = ""
        logging.warning(f"Key {e} doesn't exist") 
    # pet_times_list.append(emission_start_time)
    emission_start_time_formatted = emission_start_time.split(".")[0]    
    
    pet_metadata = [tracer, tracer_dose_mci, "000000", tracer_inj_time_formatted, emission_start_time_formatted]
    # pet_metadata = list(map(format_times, pet_times_list))
    # pet_metadata.insert(0, tracer_dose_mci)
    # pet_metadata.insert(0, tracer)
    print(pet_metadata)
    return pet_metadata


# def format_times(time):
#     return datetime.strftime(
#         datetime.strptime(time.split(".")[0], "%H%M%S"), "%H:%M:%S"
#     )


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
    # Access flywheel subject list
    fw = flywheel.Client()
    try:
        project = fw.get_project("5c508d5fc2a4ad002d7628d8")  # NACC-SC
    except flywheel.ApiException as e:
        print(f"Error: {e}")

    try:
        subjects = project.subjects.iter_find('created>2023-01-01')  #'created>2022-06-01'
    except flywheel.ApiException as e:
        print(f"Error: {e}")

    #create folder to hold downloads
    current_time = datetime.now().strftime("%Y_%m_%d")
    download_directory = f"/project/wolk/Prisma3T/relong/uploads_to_SCAN/{current_time}"
    # os.system(f'mkdir {download_directory}')

    for subject in subjects:
        print(f"Subject {subject.label}")
        #if subject has x01, change to .01 for upload csv, to match NACC IDs (subject.label is always a string)
        if "x" in subject.label:
            subjectindd=subject.label.replace("x",'.')
        else:
            subjectindd=subject.label

        usable_sessions = check_sessions(subject)
        if usable_sessions:
            global subject_total 
            subject_total += 1  
            for session in subject.sessions():
                if session.label in usable_sessions:
                    #check if session has already been added
                    if session.label in sessions_uploaded:
                        print(f"session {session.label} has already been added to SCAN")
                    else:
                        print(f"continuing to process {session.label}")

                    if '3T' in session.label:
                        for acquisition in session.acquisitions():
                        # get both FLAIR and T1 scans
                            if "Sagittal" in acquisition.label: 
                                print(f"downloading {session.label} {acquisition.label}")
                                global scan_total
                                scan_total += 1
                                acquisition_type = acquisition.label.split(' ')[2]
                                acquisition_directory = download_directory + "/" + session.label + "_" + acquisition_type
                                # os.system(f'mkdir {acquisition_directory}')
                                acquisition_file = acquisition_directory + "/" + acquisition_type + ".zip"
                                # fw.download_zip([acquisition], acquisition_file, include_types=['dicom'])
                                mri_data_list = [subjectindd, acquisition_directory, "No"]
                                mri_list_to_write.append(dict(zip(mri_columns, mri_data_list)))
                                ##add session name to master list
                                
                    elif 'PET' in session.label:
                        for acquisition in session.acquisitions():
                            if "BR-DY_CTAC" in acquisition.label and "LOCALIZER" not in acquisition.label:
                                print(f"downloading {session.label} {acquisition.label}")
                                scan_total += 1
                                acquisition_directory = download_directory + "/" + session.label
                                # os.system(f'mkdir {acquisition_directory}')
                                acquisition_file = acquisition_directory + "/" + "PET.zip"
                                # fw.download_zip([acquisition], acquisition_file, include_types=['dicom'])
                                pet_data_list = [
                                    subjectindd,
                                    acquisition_directory,
                                    str(session.timestamp)[:10]
                                ]
                                pet_metadata_list = find_pet_metadata(acquisition)
                                pet_data_list.extend(pet_metadata_list)
                                pet_list_to_write.append(dict(zip(pet_columms, pet_data_list)))
                                ##add session to master list
                else:
                    continue
        else:
            continue


#set up logging
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)

# Global variables
subject_total = 0
scan_total = 0
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

master_upload_list = f"/project/wolk/Prisma3T/relong/uploads_to_SCAN/sessions_uploaded_master.csv"
sessions_uploaded=[]
with open(master_upload_list) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        sessions_uploaded.append(row[0])


main()
print(f"{subject_total} subjects have sessions to upload.")
print(f"{scan_total} total scan files will be uploaded.")

# write_upload_csv(mri_list_to_write, "MRI", download_directory)
# write_upload_csv(pet_list_to_write, "PET", download_directory)
