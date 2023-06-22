#!/usr/bin/env python3

import csv
import pydicom
import os
import flywheel


# filepath = "/project/wolk/Prisma3T/relong/uploads_to_SCAN/2023_03_17/128983x20230131xFBBPETxABC"
# timelist = []
# for file in os.listdir(filepath):
#     ds = pydicom.filereader.dcmread(os.path.join(filepath,file))
#     timelist.append(ds[0x8,0x32].value)

# nodupelist = list(dict.fromkeys(timelist))
# nodupelist.sort()
# print(nodupelist)
#['133712.002', '134212.002', '134712.002', '135212.002']


fw = flywheel.Client()
try:
    project = fw.get_project("5c508d5fc2a4ad002d7628d8")  # NACC-SC
except flywheel.ApiException as e:
    print(f"Error: {e}")

try:
    sessions = project.sessions.iter_find('label=128983x20230131xFBBPETxABC')
except flywheel.ApiException as e:
    print(f"Error: {e}")

for session in sessions:
    for acquisition in session.acquisitions():
        if "BR-DY_CTAC" in acquisition.label and "LOCALIZER" not in acquisition.label:
            acq = acquisition.reload()
            # dicom_file_index = [x for x in range(0, len(acq.files)) if acq.files[x].type == "dicom"][0]
            # print(acq.files[dicom_file_index].info["AcquisitionTime"])
            for file in acq.files:
                if file.type != 'source code':
                    print(file.type)
                    print(file.info["AcquisitionTime"])
                    print(file.info["RadiopharmaceuticalInformationSequence"]["RadiopharmaceuticalStartTime"])
                    print(file.info["RadiopharmaceuticalInformationSequence"]["RadionuclideTotalDose"])
                # dicom
                # 135212.002
                # source code
                # 13:37:12.002000
                # nifti
                # 13:37:12.002000


# filepath = "/project/wolk/Prisma3T/relong/uploads_to_SCAN/2023_03_17"
# filename = f'{filepath}/fixed_start_times.csv'
# headernames = ['Subject','Scandate','Start time']
# with open(filename, "w", newline="") as csvfile:
#     csvwriter = csv.DictWriter(csvfile, fieldnames=headernames)
#     csvwriter.writeheader()

#     for dir in os.listdir(filepath):
#         if "PETx" in dir:
#             # print(dir)
#             timelist = []
#             list_to_write = []
#             session_name = dir.rsplit('x', 3)
#             # print(session_name)
#             subject = session_name[0]
#             date = session_name[1]
#             # print(subject)
#             # print(date)
#             for file in os.listdir(os.path.join(filepath,dir)):
#                 # print(file)
#                 ds = pydicom.filereader.dcmread(os.path.join(filepath,dir,file))
#                 timelist.append(ds[0x8,0x32].value)

#             nodupelist = list(dict.fromkeys(timelist))
#             nodupelist.sort()
#             list_to_write = [subject,date,nodupelist[0]]
#             csvwriter.writerow(dict(zip(headernames, list_to_write)))

#             print(subject)
#             print(date)
#             print(nodupelist[0])
