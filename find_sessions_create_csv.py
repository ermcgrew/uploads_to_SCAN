#!/usr/bin/env python3

import csv
from datetime import datetime,timezone
import flywheel
import logging
import os
from pandas.core.common import flatten


def write_csv(data, scantype):
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


def find_pet_metadata(acquisition): 
    acq = acquisition.reload()
    dicom_file_index = [
        x for x in range(0, len(acq.files)) if acq.files[x].type == "dicom"
    ][0]
    
    pet_times_list=["000000"] ## fake data to hold place for Tracer Dose Time from dosage computer

    try:
        tracer_inj_time = acq.files[dicom_file_index].info[
            "RadiopharmaceuticalInformationSequence"
        ]["RadiopharmaceuticalStartTime"]
    except KeyError as e:
        tracer_inj_time = "000000"
        logging.warning(f"Key {e} doesn't exist")
    pet_times_list.append(tracer_inj_time)

    try:
        emission_start_time = acq.files[dicom_file_index].info["AcquisitionTime"]
    except KeyError as e:
        emission_start_time = ""
        logging.warning(f"Key {e} doesn't exist") 
    pet_times_list.append(emission_start_time)

    try:
        tracer_dose_bec = [acq.files[dicom_file_index].info["RadiopharmaceuticalInformationSequence"]["RadionuclideTotalDose"]]
    except KeyError as e:
        tracer_dose_bec = [0]
        logging.warning(f"Key {e} doesn't exist")

    # conversion to from Becquerel to mCi to tenths place
    tracer_dose_mci = round(tracer_dose_bec[0] * 2.7e-8, 1) 
    
    if "Amyloid" in acq.label:
        tracer = "Florbetaben"
    elif "AV1451" in acq.label:
        tracer = "Flortaucipir"
    else:
        tracer=""
        logging.warning(f"Unable to identify tracer")

    pet_metadata = list(map(format_times, pet_times_list))
    pet_metadata.insert(0, tracer_dose_mci)
    pet_metadata.insert(0, tracer)
    # print(pet_metadata)
    return pet_metadata


def format_times(time):
    return datetime.strftime(
        datetime.strptime(time.split(".")[0], "%H%M%S"), "%H:%M:%S"
    )

# for each subject, upload only if sessions are ABC, 2021 or later, 
# have 3T with new protocol Accelerated Sagital MPRAGE file and at least one PET session
def check_sessions(subject):
    check_for_AccSag_acquisition = [[session.label for acquisition in session.acquisitions() if "Accelerated Sagittal MPRAGE (MSV21)" in acquisition.label] 
                for session in subject.sessions() if "3T" in session.label and "ABC" in session.label]
    usable_sessions = list(flatten(check_for_AccSag_acquisition))
    if usable_sessions:    
        # print(f"Subject {subject.label} has AccSag file in 3T scan, checking for PET scans")
        check_for_PET = [session.label for session in subject.sessions() if ("FBBPET" in session.label or "AV1451" in session.label) and "ABC" in session.label and session.timestamp >= datetime(2021,1,1,0,0,0,tzinfo=timezone.utc)]
        if check_for_PET:
            usable_sessions.extend(check_for_PET)
            return(usable_sessions)
    

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

#create folder to hold downloads
current_time = datetime.now().strftime("%Y_%m_%d")
download_directory = f"/project/wolk/Prisma3T/relong/uploads_to_SCAN/{current_time}"
os.system(f'mkdir {download_directory}')

for subject in subjects:
    print(f"Subject {subject.label}")
    usable_sessions = check_sessions(subject)
    if usable_sessions:
        subject_total += 1  
        for session in subject.sessions():
            if session.label in usable_sessions:
                if '3T' in session.label:
                    for acquisition in session.acquisitions():
                    # get both FLAIR and T1 scans
                        if "Sagittal" in acquisition.label: 
                            print(f"downloading {session.label} {acquisition.label}")
                            scan_total += 1
                            acquisition_type = acquisition.label.split(' ')[2]
                            acquisition_directory = download_directory + "/" + session.label + "_" + acquisition_type
                            os.system(f'mkdir {acquisition_directory}')
                            acquisition_file = acquisition_directory + "/" + acquisition_type + ".zip"
                            fw.download_zip([acquisition], acquisition_file, include_types=['dicom'])
                            mri_data_list = [subject.label, acquisition_directory, "No"]
                            mri_list_to_write.append(dict(zip(mri_columns, mri_data_list)))
                elif 'PET' in session.label:
                    for acquisition in session.acquisitions():
                        if "BR-DY_CTAC" in acquisition.label and "LOCALIZER" not in acquisition.label:
                            print(f"downloading {session.label} {acquisition.label}")
                            scan_total += 1
                            acquisition_directory = download_directory + "/" + session.label
                            os.system(f'mkdir {acquisition_directory}')
                            acquisition_file = acquisition_directory + "/" + "PET.zip"
                            fw.download_zip([acquisition], acquisition_file, include_types=['dicom'])
                            pet_data_list = [
                                subject.label,
                                acquisition_directory,
                                str(session.timestamp)[:10]
                            ]
                            pet_metadata_list = find_pet_metadata(acquisition)
                            pet_data_list.extend(pet_metadata_list)
                            pet_list_to_write.append(dict(zip(pet_columms, pet_data_list)))
            else:
                continue
    else:
        continue

print(f"{subject_total} subjects have sessions to upload.")
print(f"{scan_total} total scan files will be uploaded.")

write_csv(mri_list_to_write, "MRI")
write_csv(pet_list_to_write, "PET")
