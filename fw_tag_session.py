#!/usr/bin/env python3

import flywheel


def main():
    fw = flywheel.Client()
    try:
        project = fw.get_project("5c508d5fc2a4ad002d7628d8")  # NACC-SC
    except flywheel.ApiException as e:
        print(f"Error: {e}")


    # /project/wolk/Prisma3T/relong/uploads_to_SCAN/all_sessions_uploaded.csv 

    
main()