#!/usr/bin/env python

import pandas as pd
import os

irb_dict={
    844047: "ABCD2 Florbetaben", 
    844403: 'ABCD2 Flortaucipir',   
    825943: "ABC Florbetaben", 
    825944: 'ABC Flortaucipir',
    822544: 'ABC Flortaucipir'
    }

upload_dir = "/project/wolk/Prisma3T/relong/uploads_to_SCAN"

all_dirs = [x for x in os.listdir(upload_dir) if ".txt" not in x and ".csv" not in x]
all_dirs.sort(reverse=True)
upload_dir_current = os.path.join(upload_dir,all_dirs[0])

pet_csv = [x for x in os.listdir(upload_dir_current) if "PET_sessions" in x][0]
mri_csv = [x for x in os.listdir(upload_dir_current) if "MRI_sessions" in x][0]
dosage_csv = [x for x in os.listdir(upload_dir_current) if "dosage" in x][0]
nacc_id_csv = [ x for x in os.listdir(upload_dir_current) if "nacc" in x][0]

pet_csv_updated = pet_csv.split('.')[0] + "_dosagetime_naccid_added.csv"
mri_csv_updated = mri_csv.split('.')[0] + "_naccid_added.csv"

petinfo=pd.read_csv(os.path.join(upload_dir_current,pet_csv))
dosage_master=pd.read_csv(os.path.join(upload_dir_current,dosage_csv))
nacc_id=pd.read_csv(os.path.join(upload_dir_current,nacc_id_csv))

# print(petinfo.info())
# print(dosage_master.head())


def add_nacc_id(df):
    count = 0
    for index,row in df.iterrows():
        ptid = str(row['Subject ID'])
        match = nacc_id.loc[nacc_id['PTID'] == ptid]
        if len(match) < 1:
            # print("drop this row, cannot upload without NACCID")
            df.drop([index],inplace=True)
            count += 1
        else:
            # print('match found')
            df.at[index,'Subject ID'] = ptid + "+" + match['NACCID'].values[0]
    print(f"Dropped {count} sessions from df for not having NACCID yet.")
    return df


for index,row in petinfo.iterrows():
    # print(f"For row {index} {row['Subject ID']}")
    session = row['Directory'].split('/')[-1:]
    study = session[0].split('x')[-1:][0]
    studytracer= study + " " + row['Tracer']

    #match on date and tracer
    match=dosage_master.loc[(dosage_master['Assay Date'] == row['Scan Date']) & (dosage_master['Tracer'] == row['Tracer'])]
    if len(match) == 0:
        print(f"row index {index}, ID {row['Subject ID']}, has no date/tracer match in dosage csv.")
        continue
    else:
        irbnum=match['IRBnum'].values

        #Match on Tracer inj. time
        shortinjtime=":".join(row['Tracer Inj Time'].split(':')[0:2])
        if row['Tracer Inj Time'] == "00:00:00":
            #match on IRB number
            matchindextokeep=[match.loc[match['IRBnum'] == num].index.values.astype(int)[0] for num in irbnum 
                    if num in irb_dict and irb_dict[num] == studytracer]       
            smaller_match=dosage_master.iloc[matchindextokeep]
            if len(smaller_match) == 1:
                #add Assay Time, Inj.Tm, Inj.Act
                assaytimetoadd = smaller_match['Assay Time'].values[0] + ":00"
                injtimetoadd = smaller_match['Inj.Tm'].values[0] + ":00"
                injamttoadd = round(float(smaller_match['Inj.Act'].values[0].split(" ")[0]),1) ##rounding, drop unit
                # print(assaytimetoadd)
                # print(injtimetoadd)
                # print(injamttoadd)
                petinfo.at[index,'Tracer Dose Time'] = assaytimetoadd
                petinfo.at[index,'Tracer Inj Time'] = injtimetoadd
                petinfo.at[index,'Tracer Dose Assay'] = injamttoadd            
            else:
                print(f"row index {index}, ID {row['Subject ID']}, has multiple date/tracer matches in dosage.csv")
        else:
            select_match=match.loc[match['Inj.Tm'] == shortinjtime]
            # print(select_match)
            if len(select_match) < 1:
                print(f"Row index {index}, ID {row['Subject ID']}, no match to injection time")
            else:
                test=select_match['IRBnum'].values[0]
                if str(test) == 'nan':
                    print(f"Row index {index}, ID {row['Subject ID']}, match unclear, IRB num is NAN")
                else:
                    if len(select_match) == 1 and irb_dict[test] == studytracer:
                        #add Assay Time
                        timetoadd = select_match['Assay Time'].values[0] + ":00"
                        # print(timetoadd)
                        petinfo.at[index,'Tracer Dose Time'] = timetoadd
                    else:
                        print(f"Row index {index}, ID {row['Subject ID']}, match unclear")

##Add NACCID to PET csv
petinfo_naccid = add_nacc_id(petinfo)
# print(petinfo_naccid.head())
# print(petinfo_naccid.info())
petinfo_naccid.to_csv(os.path.join(upload_dir_current,pet_csv_updated),index=False,header=True)


##Add NACCID to MRI csv
mriinfo=pd.read_csv(os.path.join(upload_dir_current,mri_csv))
mriinfo_naccid = add_nacc_id(mriinfo)
# print(mriinfo_naccid.head())
mriinfo_naccid.to_csv(os.path.join(upload_dir_current,mri_csv_updated),index=False,header=True)
