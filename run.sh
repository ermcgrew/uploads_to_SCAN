#!/usr/bin/bash


Help(){
    echo "This program identifies files for SCAN project and uploads them to SCAN website."
    echo 
    echo "Options:"
    echo "-c     Calls create_csvs function to review Flywheel data for qualifying files and create csv to upload with."
    echo "-u     Calls upload_files function to create report on upload numbers, unzip dicom files and upload dicom files to ida.loni.usc.edu"
    echo "-d     Date from folder created in create_csvs function. Required for upload_files function. Format: YYYY_MM_DD"
    echo "-h     Print this help."
    echo 
    echo "Run this program as a job on the bscsub cluster"
    echo "Example usages: "
    echo "bsub < run.sh -N -o /project/wolk/Prisma3T/relong/uploads_to_SCAN/output.%J -e /project/wolk/Prisma3T/relong/uploads_to_SCAN/errors.%J"

    echo "bash run.sh -c"
    echo "bash run.sh -d 2023_04_03 -u"
}

create_csvs(){
    module load python

    #run python script
    echo Running python script
    # python find_sessions_create_csv.py

    ##TODO: get list of subjects to check with nicole
    filename='/project/wolk/Prisma3T/relong/uploads_to_SCAN/all_sessions_uploaded.csv'
    # todaysubjects=$( cat $filename | grep $current_date | cut -f 3 -d "," | sort -u )
    echo $( cat $filename | grep $this_date | cut -f 3 -d "," | sort -u )
}

upload_files(){
    module load jre

    download_directory=/project/wolk/Prisma3T/relong/uploads_to_SCAN
    current_date_directory="${download_directory}/${this_date}"

    # parse tracking file
    # /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/parse_tracking_file.sh "$this_date" >> "$download_directory/stats_${this_date}.txt"

    #unzip dicom files and get csv file names for java call
    for dir in $current_date_directory/* ; do 
        if [[ -d $dir ]] ; then 
            echo $dir
            # cd $dir  
            # mkdir tmp
            # unzip -jq *.zip -d $dir/tmp
            # unzip -jq $dir/tmp/* 
            # rm *.zip
            # rm -r tmp
        elif [[ -f $dir ]] ; then
            if [[ $(basename $dir) =~ "MRI" ]] ; then
                mrifile=$dir
            elif [[ $(basename $dir) =~ "PET"  &&  $(basename $dir) =~ "dosagetimeadded" ]] ; then
                petfile=$dir
            fi
        fi  
    done

    #load email and password from config.py
    source /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/config.py

    #java upload program
    echo Running java uploader
    # java -jar /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/IdaUploader_02Dec2022.jar \
        # --email=$email --password=$password --project=SCAN --site=ADC21 $mrifile
    # java -jar /project/wolk/Prisma3T/relong/scripts/uploads_to_SCAN/IdaUploader_02Dec2022.jar \
    #     --email=$email --password=$password --project=SCAN --site=ADC21 $petfile

}

#export functions for use in cluster calls
export -f upload_files
export -f create_csvs

# Get the options
while getopts ':cd:hu' option; do
    case "$option" in
        h) # display Help
            Help
            exit;;
        d) 
            this_date="$OPTARG" ;;
        c) 
            bsub -N create_csvs;;    
            ##do bsub ooptions here?
        u) 
            bsub -N upload_files ;;
        \?) # Invalid option
            echo "Error: Invalid option"
            exit;;
    esac
done