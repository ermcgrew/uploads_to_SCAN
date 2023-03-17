#!/usr/bin/bash

#run python 

for dir in /project/wolk/Prisma3T/relong/uploads_to_SCAN/2023_03_17/* ; do 
    if [[ -d $dir ]] ; then 
        cd $dir  
        # mkdir tmp
        # unzip -jq *.zip -d $dir/tmp
        # unzip -jq $dir/tmp/* 
        rm *.zip
        rm -r tmp
    fi  
done

#java