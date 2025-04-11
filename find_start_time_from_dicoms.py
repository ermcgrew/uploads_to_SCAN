#!/usr/bin/env python3

import os
import pydicom

#directory containing zip file of dicoms
filepath = "/project/wolk/Prisma3T/relong/uploads_to_SCAN/2025_03_03/131766x20241016xFBBPETxABCD2"

## Unzip download from flywheel
# os.system(f'cd {filepath}')
os.chdir(filepath)
os.system('pwd')
os.system("unzip -j PET.zip")
os.system("unzip -j \[BR*")
os.system("rm *.zip")

## record all timepoints from dicom files
timelist = []
for file in os.listdir(filepath):
    ds = pydicom.filereader.dcmread(os.path.join(filepath,file))
    timelist.append(ds[0x8,0x32].value)

#de-dupe and sort timepoints to get list of 4 (amyloi) or 6 (tau) with earliest first 
## use earliest as Emission Start Time in SCAN upload csv
nodupelist = list(dict.fromkeys(timelist))
nodupelist.sort()
print(nodupelist)
