#!/usr/bin/env python3

from config import email,password
import csv
from datetime import datetime,timezone
import flywheel
import os


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


def find_pet_metadata(acquisition): 
            acq = acquisition.reload()
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
            # conversion to from Becquerel to mCi to tenths place
            tracer_dose_mci = round(tracer_dose_bec[0] * 2.7e-8, 1) 
            
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
            # print(pet_metadata)
            return pet_metadata


def format_times(time):
    return datetime.strftime(
        datetime.strptime(time.split(".")[0], "%H%M%S"), "%H:%M:%S"
    )

# for each subject, upload only if sessions are ABC, 2021 or later, 
# have 3T with new protocol Accelerated Sagital MPRAGE file and at least one PET session
def check_sessions(subject):
    check_for_AccSag_acquisition = [[acquisition.label for acquisition in session.acquisitions() if "Accelerated Sagittal MPRAGE (MSV21)" in acquisition.label] 
                for session in subject.sessions() if "3T" in session.label and "ABC" in session.label]    
    if len(check_for_AccSag_acquisition) >=1:
        # print(f"Subject {subject.label} has AccSag file in 3T scan, checking for PET scans")
        check_for_PET = [session.label for session in subject.sessions() if "FBBPET" in session.label or "AV1451" in session.label and "ABC" in session.label]
        return(check_for_PET)

         
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
    subjects = project.subjects.iter_find("created>2022-09-01")  #'created>2022-06-01'
except flywheel.ApiException as e:
    print(f"Error: {e}")

#create folder to hold downloads
current_time = datetime.now().strftime("%Y_%m_%d")
download_directory = f"/project/wolk/Prisma3T/relong/uploads_to_SCAN/{current_time}"
# os.system(f'mkdir {download_directory}')

for subject in subjects:
    print(f"Subject {subject.label}")
    if check_sessions(subject):
        subject_total += 1  
        for session in subject.sessions():
            if "3T" in session.label and "ABC" in session.label and "Duplicate" not in session.tags and "Misc." not in session.tags and session.timestamp >= datetime(2021,1,1,0,0,0,tzinfo=timezone.utc):
                for acquisition in session.acquisitions():
                    # get both FLAIR and T1 scans
                    if "Sagittal" in acquisition.label: 
                        print(f"downloading {session.label} {acquisition.label}")
                        scan_total += 1
                        file_loc = download_directory + "/" + session.label + "_" +acquisition.label + ".zip"
                        # fw.download_zip([acquisition], file_loc, include_types=['dicom'])
                        mri_data_list = [subject.label, file_loc, "No"]
                        mri_list_to_write.append(dict(zip(mri_columns, mri_data_list)))

            elif "FBBPET" in session.label or "AV1451PET" in session.label and "ABC" in session.label and "Duplicate" not in session.tags and "Misc." not in session.tags and session.timestamp >= datetime(2021,1,1,0,0,0,tzinfo=timezone.utc):
                print(session.timestamp)
                scan_total += 1
                file_loc = download_directory + "/" + session.label + ".zip"
                for acquisition in session.acquisitions():
                    if "BR-DY_CTAC" in acquisition.label and "LOCALIZER" not in acquisition.label:
                        print(f"downloading {session.label} {acquisition.label}")
                        # fw.download_zip([acquisition], file_loc, include_types=['dicom'])
                        pet_data_list = [
                            subject.label,
                            file_loc,
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
print(f"{scan_total} total sessions will be uploaded.")

# write_csv(mri_list_to_write, "MRI")
# write_csv(pet_list_to_write, "PET")


# call to java program
# java -jar IdaUploader_02Dec2022.jar
# --email=email --password=password
# --project=SCAN --site=ADC21
# SCAN_MRI_upload_test_20230203.csv


## when java program finished, remove all zip downloads
# os.system ("rm /{current_time}/*.zip")