#!/usr/bin/bash
#Remove subjects that don't have nacc packets submitted & accepted yet (SCAN will reject them)

#list of subjects from this upload batch that need to have all lines removed
cat all_sessions_uploaded.csv | grep "2023_06_26" | grep '128345\|128689\|128936\|128971\|128983\|129250\|129574' >> 2023_06_26/nacc_packets_not_ready.csv

# from all sessions uploaded list 
cp all_sessions_uploaded.csv 2023_06_26/all_sessions_uploaded_pre_nacc_check.csv #backup just in case
for line in $( cat 2023_06_26/nacc_packets_not_ready.csv ) ; do sed -i "/$line/d" all_sessions_uploaded.csv ; done

# from MRI list
sed -i '/\(128345\|128689\|128936\|128971\|128983\|129250\|129574\)/d' MRI_sessions_for_SCAN_20230626_1636.csv
# from PET list
sed -i '/\(128345\|128689\|128936\|128971\|128983\|129250\|129574\)/d' PET_sessions_for_SCAN_20230626_1636_dosagetimeadded.csv 

#remove dicoms--they take forever to unzip & take up space
current_date_directory="/project/wolk/Prisma3T/relong/uploads_to_SCAN/2023_06_26"
subs=('128345' '128689' '128936' '128971' '128983' '129250' '129574')
for dir in $current_date_directory/* ; do 
    for sub in "${subs[@]}" ; do
        if [[ -d $dir && $dir =~ ${sub} ]] ; then 
           rm -r $dir
        fi
    done
done



    