#!/usr/bin/env bash

current_date=$1
filename='/project/wolk/Prisma3T/relong/uploads_to_SCAN/all_sessions_uploaded.csv'

allfiles=$( cat $filename | wc -l )
echo "Total number of files uploaded: ${allfiles}"

todayfiles=$( cat $filename | grep $current_date | wc -l )
echo "Files uploaded in $current_date batch: ${todayfiles}"
echo 

allsessions=$( cat $filename | cut -f 2 -d "," | sort -u | wc -l )
echo "Total number of sessions uploaded: ${allsessions}"

todaysessions=$( cat $filename | grep $current_date | cut -f 2 -d "," | sort -u | wc -l )
echo "Sessions uploaded in $current_date batch: ${todaysessions}"
echo 

allsubjects=$( cat $filename | cut -f 3 -d "," | sort -u | wc -l )
echo "Total number of subjects with uploads: ${allsubjects}"

todaysubjects=$( cat $filename | grep $current_date | cut -f 3 -d "," | sort -u | wc -l)
echo "Subjects uploaded in $current_date batch: ${todaysubjects}"
echo
