#!/usr/bin/bash

Help(){
    echo "This program identifies files for SCAN project and uploads them to SCAN website."
    echo 
    echo "Options:"
    echo "-a     Calls add_info function to add NACCIDs to both sheets and dosage computer info to PET csv."
    echo "-c     Calls create_csvs function to review Flywheel data for qualifying files and create csv to upload with."
    echo "-u     Calls upload_files function to create report on upload numbers,"
    echo "       unzips dicom files and uploads dicom files to ida.loni.usc.edu"
    echo "-d     Date from folder created in create_csvs function. Required for upload_files function. Format: YYYY_MM_DD"
    echo "-h     Print this help."
    echo 
    echo "All functions are submitted to cluster bscsub queue."
    echo 
    echo "Before running upload_files function, use dosage computer reports to fill in missing PET time column "
    echo "and get status of NACC packets for all subjects so any with incomplete submissions can be removed from upload list." 
    echo 
    echo "Example usages:"
    echo "bash run.sh -c"
    echo "bash run.sh -d 2023_06_26 -u"
}

create_csvs(){
    module load python
    echo "Running python script find_sessions_create_csv.py." 
    python find_sessions_create_csv.py
}

add_info(){
    module load python
    echo "Running python script add_dosage_naccid.py."
    python add_dosage_naccid.py
}

upload_files(){
    module load jre

    this_date=$1
    download_directory=/project/wolk/Prisma3T/relong/uploads_to_SCAN
    current_date_directory="${download_directory}/${this_date}"

   
    #unzip dicom files and get csv file names for java call
    for dir in $current_date_directory/* ; do 
        if [[ -d $dir ]] ; then 
            echo "unzipping ${dir}"
            cd $dir  
            mkdir tmp
            unzip -jq *.zip -d $dir/tmp
            unzip -jq $dir/tmp/* 
            rm *.zip
            rm -r tmp
        elif [[ -f $dir ]] ; then
            if [[ $(basename $dir) =~ "MRI" &&  $(basename $dir) =~ "naccid_added" ]] ; then
                mrifile=$dir
            elif [[ $(basename $dir) =~ "PET"  &&  $(basename $dir) =~ "naccid_added" ]] ; then
                petfile=$dir
            fi
        fi  
    done

    #load email and password from config.py
    source /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/config.py

    #java upload program
    echo Running java uploader
    java -jar /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/IdaUploader_02Dec2022.jar \
        --email=$email --password=$password --project=SCAN --site=ADC21 $mrifile
    java -jar /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/IdaUploader_02Dec2022.jar \
        --email=$email --password=$password --project=SCAN --site=ADC21 $petfile


    sleep 2
    module load python
    python fw_tag_session.py

    # parse tracking file
    /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/parse_tracking_file.sh "$this_date" >> "$download_directory/stats_${this_date}.txt"


}

#export functions for use in cluster calls
export -f create_csvs
export -f add_info
export -f upload_files

# Get the options
while getopts ':acd:hu' option; do
    case "$option" in
        h) 
            Help
            exit;;
        a) 
            bsub -N add_info;;
        d) 
            this_date="$OPTARG" ;;
        c) 
            bsub -N create_csvs;;    
        u) 
            bsub -N -o "/project/wolk/Prisma3T/relong/uploads_to_SCAN/${this_date}/upload_job_output2.%J" upload_files $this_date ;;
        \?) 
            echo "Error: Invalid option"
            exit;;
    esac
done

