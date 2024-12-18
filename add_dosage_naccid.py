#!/usr/bin/env python

from datetime import datetime
import logging
import pandas as pd
import os
from uploads_to_SCAN import *


uses_ptid_instead_of_indd={101545:4219, 107486:4029, 113612_01:8680}


def add_nacc_id(df,nacc_id):
    count = 0
    for index,row in df.iterrows():
        ptid = str(row['Subject ID'])

        if int(ptid) in list(uses_ptid_instead_of_indd.keys()):
            ptid = str(uses_ptid_instead_of_indd[int(ptid)])
            logging.debug(f"row {index}:{row['Subject ID']}:Uses PTID instead of INDDID for NACC mapping.")

        match = nacc_id.loc[nacc_id['PTID'] == ptid]
        if len(match) < 1:
            logging.debug(f"drop row {index}:{row['Subject ID']}:no NACCID match")
            df.drop([index],inplace=True)
            count += 1
        else:
            df.at[index,'Subject ID'] = ptid + "+" + match['NACCID'].values[0]
    logging.debug(f"Dropped {count} sessions from df for not having NACCID yet.")
    return df


def add_dosage_info(petinfo,dosage_master):
    irb_dict={
        844047: "ABCD2 Florbetaben", 
        844403: 'ABCD2 Flortaucipir',   
        825943: "ABC Florbetaben", 
        825944: 'ABC Flortaucipir',
        822544: 'ABC Flortaucipir', 
        850160: "MPC Florbetaben",
        850679: "MPC Flortaucipir"
    }

    for index,row in petinfo.iterrows():
        session = row['Directory'].split('/')[-1:]
        study = session[0].split('x')[-1:][0]
        studytracer= study + " " + row['Tracer']

        #match on date and tracer
        match=dosage_master.loc[(dosage_master['Assay Date'] == row['Scan Date']) & (dosage_master['Tracer'] == row['Tracer'])]
        if len(match) == 0:
            logging.debug(f"row index {index}, ID {row['Subject ID']}, date {row['Scan Date']} has no date/tracer match in dosage csv.")
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
                    injamttoadd = round(float(smaller_match['Inj.Act'].values[0]),1)
                    petinfo.at[index,'Tracer Dose Time'] = assaytimetoadd
                    petinfo.at[index,'Tracer Inj Time'] = injtimetoadd
                    petinfo.at[index,'Tracer Dose Assay'] = injamttoadd            
                else:
                    logging.debug(f"row index {index}, ID {row['Subject ID']}, date {row['Scan Date']} has multiple date/tracer matches in dosage.csv")
            else:
                select_match=match.loc[match['Inj.Tm'] == shortinjtime]
                if len(select_match) < 1:
                    logging.debug(f"Row index {index}, ID {row['Subject ID']}, date {row['Scan Date']} no match to injection time")
                else:
                    test=select_match['IRBnum'].values[0]
                    if str(test) == 'nan':
                        logging.debug(f"Row index {index}, ID {row['Subject ID']}, date {row['Scan Date']} match unclear, IRB num is NAN")
                    else:
                        if len(select_match) == 1 and irb_dict[test] == studytracer:
                            #add Assay Time
                            timetoadd = select_match['Assay Time'].values[0] + ":00"
                            petinfo.at[index,'Tracer Dose Time'] = timetoadd
                        else:
                            logging.debug(f"Row index {index}, ID {row['Subject ID']}, date {row['Scan Date']} match unclear")
    return petinfo


def main():
    upload_dir_current = get_current_upload_dir()
    current_date = datetime.now().strftime("%Y_%m_%d")
    logging.basicConfig(filename=f"{upload_dir_current}/add_info_{current_date}.log", filemode='w', format="%(levelname)s: %(message)s", level=logging.DEBUG)

    ## Load PET csv and Dosage csv
    pet_csv = [x for x in os.listdir(upload_dir_current) if "PET_sessions" in x][0]
    petinfo=pd.read_csv(os.path.join(upload_dir_current,pet_csv))
    dosage_csv = [x for x in os.listdir(upload_dir_current) if "dosage" in x][0]
    dosage_master=pd.read_csv(os.path.join(upload_dir_current,dosage_csv))

    # Add missing assay time info from dosage report
    petinfo_dosage = add_dosage_info(petinfo,dosage_master)

    ## Load NACCID csv
    nacc_id_csv = [ x for x in os.listdir(upload_dir_current) if "nacc" in x][0]
    nacc_id = pd.read_csv(os.path.join(upload_dir_current,nacc_id_csv))
    
    ##Add NACCID to PET csv
    petinfo_naccid = add_nacc_id(petinfo_dosage, nacc_id)
    petinfo_naccid.info()
    pet_csv_updated = pet_csv.split('.')[0] + "_dosagetime_naccid_added.csv"
    petinfo_naccid.to_csv(os.path.join(upload_dir_current,pet_csv_updated),index=False,header=True)

    ##Add NACCID to MRI csv
    mri_csv = [x for x in os.listdir(upload_dir_current) if "MRI_sessions" in x][0]
    mriinfo=pd.read_csv(os.path.join(upload_dir_current,mri_csv))
    mriinfo_naccid = add_nacc_id(mriinfo, nacc_id)
    mriinfo_naccid.info()
    mri_csv_updated = mri_csv.split('.')[0] + "_naccid_added.csv"
    mriinfo_naccid.to_csv(os.path.join(upload_dir_current,mri_csv_updated),index=False,header=True)


main()
