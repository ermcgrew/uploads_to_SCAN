#!/usr/bin/bash

#run python script
echo Running python script
echo python find_sessions_create_csv.py

download_directory=/project/wolk/Prisma3T/relong/uploads_to_SCAN
for dir in $download_directory/2023_03_17/* ; do 
    if [[ -d $dir ]] ; then 
        cd $dir  
        # echo $dir
        # mkdir tmp
        # unzip -jq *.zip -d $dir/tmp
        # unzip -jq $dir/tmp/* 
        # rm *.zip
        # rm -r tmp
    elif [[ -f $dir ]] ; then
        if [[ $(basename $dir) =~ MRI* ]] ; then
            mrifile=$dir
        elif [[ $(basename $dir) =~ PET* ]] ; then
            petfile=$dir
        fi
    fi  
done

#load email and password from config.py
source /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/config.py

#java upload program
echo java -jar IdaUploader_02Dec2022.jar --email=$email --password=$password --project=SCAN --site=ADC21 $mrifile
echo java -jar IdaUploader_02Dec2022.jar --email=$email --password=$password --project=SCAN --site=ADC21 $petfile