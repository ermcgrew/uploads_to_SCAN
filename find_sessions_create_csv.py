#!/usr/bin/env python3

import flywheel
import csv
from datetime import datetime
# from config import email,password


def write_csv(data, scantype):
    if scantype == "MRI":
        headernames = mri_columns
    elif scantype == "PET":
        headernames = pet_columms
    time = datetime.now().strftime("%Y%m%d_%H%M")
    with open(f"{scantype}_sessions_for_SCAN_{time}.csv", "w", newline="") as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=headernames)
        csvwriter.writeheader()
        csvwriter.writerows(data)
    return


def find_pet_metadata(acquisitions): 
    for acq in acquisitions:
        if "BR-DY_CTAC" in acq.label and "LOCALIZER" not in acq.label:
            acq = acq.reload()
            dicom_file_index = [
                x for x in range(0, len(acq.files)) if acq.files[x].type == "dicom"
            ][0]
            
            pet_times_list=["000000"] ## fake data to hold place for Tracer Dose Time from dosage computer
            pet_times_list.append(
                acq.files[dicom_file_index].info[
                    "RadiopharmaceuticalInformationSequence"
                ]["RadiopharmaceuticalStartTime"]
            )
            pet_times_list.append(
                acq.files[dicom_file_index].info["AcquisitionTime"]
            )
            
            tracer_dose_bec = [acq.files[dicom_file_index].info["RadiopharmaceuticalInformationSequence"]["RadionuclideTotalDose"]]
            print(tracer_dose_bec)
            tracer_dose_mci = round(tracer_dose_bec[0] * 2.7e-8, 1) # conversion to from Becquerel to mCi to tenths
            print(tracer_dose_mci)
            
            if "Amyloid" in acq.label:
                tracer = "Florbetaben"
            elif "AV1451" in acq.label:
                tracer = "Flortaucipir"
            else:
                tracer=""
                print("unable to identify tracer")

            pet_metadata = list(map(format_times, pet_times_list))
            pet_metadata.insert(0, tracer_dose_mci)
            pet_metadata.insert(0, tracer)
            print(pet_metadata)

            return pet_metadata


def format_times(time):
    return datetime.strftime(
        datetime.strptime(time.split(".")[0], "%H%M%S"), "%H:%M:%S"
    )


# Global variables
subject_total = 0
session_total = 0
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
    subjects = project.subjects.iter_find("created>2022-06-01")  #'created>2022-06-01'
except flywheel.ApiException as e:
    print(f"Error: {e}")

# for each subject, keep sessions only if they are ABC, at least one session 2021 or later (consent form changed), have 3T and FBBPET sessions
# new criteria: only if 3T session has Accelerated Sagital MPRAGE file 
for subject in subjects:
    acq_test = [[acquisition.label for acquisition in session.acquisitions() if "Accelerated Sagittal MPRAGE (MSV21)" in acquisition.label] for session in subject.sessions() if "3T" in session.label and "ABC" in session.label]    
    if acq_test and acq_test[0]:
        print(f"Subject {subject.label} has AccSag file in 3T scan, checking for PET scans")
        pet_test = [session.label for session in subject.sessions() if "FBBPET" in session.label or "AV1451" in session.label]
        if pet_test:
            print([session.label for session in subject.sessions() if "Duplicate" not in session.tags
            and "Misc." not in session.tags
            and "ABC" in session.label
            and "7T" not in session.label]) #count of sessions to upload from

########################################################################
            for session in subject.sessions():
                if "3T" in session.label:
                    session_total += 1
                    print(f"This session should be added: {session.label}")

                    # download dicom
                    # save file loc

                    mri_data_list = [subject.label, "temp", "No"]
                    mri_list_to_write.append(dict(zip(mri_columns, mri_data_list)))

                elif "FBBPET" in session.label or "AV1451PET" in session.label:
                    session_total += 1
                    print(f"This session should be added: {session.label}")
                    
                    # download dicom
                    # save file loc
                    
                    pet_data_list = [
                        subject.label,
                        "temp",
                        str(session.timestamp)[:10]
                    ]
                    pet_metadata_list = find_pet_metadata(session.acquisitions())
                    pet_data_list.extend(pet_metadata_list)
                    pet_list_to_write.append(dict(zip(pet_columms, pet_data_list)))
                else:
                    continue
    else:
        continue

# print(f"{subject_total} subjects have sessions to upload.")
# print(f"{session_total} total sessions will be uploaded.")

# write_csv(mri_list_to_write, "MRI")
# write_csv(pet_list_to_write, "PET")


# call to java program
# java -jar IdaUploader_02Dec2022.jar
# --email=email --password=password
# --project=SCAN --site=ADC21
# SCAN_MRI_upload_test_20230203.csv
