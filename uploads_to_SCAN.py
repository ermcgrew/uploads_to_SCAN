#!/usr/bin/env python3

## Shared variables and functions

import os

scan_directory = f"/project/wolk/Prisma3T/relong/uploads_to_SCAN"
upload_tracking_file = f"{scan_directory}/all_sessions_uploaded_tester.csv"

def get_current_upload_dir():
    all_dirs = [x for x in os.listdir(scan_directory) if ".txt" not in x and ".csv" not in x]
    all_dirs.sort(reverse=True)
    upload_dir_current = os.path.join(scan_directory,all_dirs[0])
    return upload_dir_current
