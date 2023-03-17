#!/usr/bin/bash
#BSUB -N

module load python3
module load jre

#run python script
echo Running python script
python find_sessions_create_csv.py

download_directory=/project/wolk/Prisma3T/relong/uploads_to_SCAN
#unzip dicom files and get csv file names for java call
for dir in $download_directory/2023_03_17/* ; do 
    if [[ -d $dir ]] ; then 
        cd $dir  
        mkdir tmp
        unzip -jq *.zip -d $dir/tmp
        unzip -jq $dir/tmp/* 
        rm *.zip
        rm -r tmp
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
echo Running java uploader
java -jar /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/IdaUploader_02Dec2022.jar --email=$email --password=$password --project=SCAN --site=ADC21 $mrifile
# java -jar IdaUploader_02Dec2022.jar --email=$email --password=$password --project=SCAN --site=ADC21 $petfile

# bsub < run.sh -o /project/wolk/Prisma3T/relong/uploads_to_SCAN/2023_03_17/output.%J -e /project/wolk/Prisma3T/relong/uploads_to_SCAN/2023_03_17/output.%J/errors.%J