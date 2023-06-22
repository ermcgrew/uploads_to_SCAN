#!/usr/bin/env bash

filename='/project/wolk/Prisma3T/relong/uploads_to_SCAN/all_sessions_uploaded_20230317.csv'

allfiles=$( cat $filename | wc -l )
echo "Total number of files uploaded: ${allfiles}"

todayfiles=$( cat $filename | grep "2023_03_17" | wc -l )
echo "Files uploaded in current batch: ${todayfiles}"

allsessions=$( cat $filename | cut -f 2 -d "," | sort -u | wc -l )
echo "Total number of sessions uploaded: ${allsessions}"

todaysessions=$( cat $filename | grep "2023_03_17" | cut -f 2 -d "," | sort -u | wc -l )
echo "Sessions uploaded in current batch: ${todaysessions}"

allsubjects=$( cat $filename | cut -f 3 -d "," | sort -u | wc -l )
echo "Total number of subjects with uploads: ${allsubjects}"

todaysubjects=$( cat $filename | grep "2023_03_17" | cut -f 3 -d "," | sort -u | wc -l)
echo "Subjects uploaded in current batch: ${todaysubjects}"

