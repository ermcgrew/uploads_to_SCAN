#!/usr/bin/bash
import pandas as pd

df=pd.read_csv("/project/wolk/Prisma3T/relong/uploads_to_SCAN/2024_04_12/PET_sessions_for_SCAN_20240412_1330_dosagetime_naccid_added.csv")
df.info()

for index,row in df.iterrows():
    tofix=row['Emission Start Time']
    print(f"Current entry: {tofix}")
    # print(type(tofix))
    if ":" not in tofix:
        newtime=tofix[0:2] +":"+ tofix[2:4] +":" + tofix[4:]
        # print(newtime)
        df.at[index,'Emission Start Time'] = newtime
    
df.to_csv("/project/wolk/Prisma3T/relong/uploads_to_SCAN/2024_04_12/PET_sessions_for_SCAN_20240412_1330_dosagetime_naccid_added.csv",index=False,header=True)
