import datetime
import os
import json
import sys
import fitparse
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# ✅ Ensure log file is created at the start
with open("log.txt", "w") as log_file:
    log_file.write("✅ Script started successfully!\n")

def log_message(message):
    print(message)
    with open("log.txt", "a") as log_file:
        log_file.write(message + "\n")

log_message("✅ Script is now running...")

# Function to parse .FIT file
def parse_fit_file(file_path):
    log_message(f"🔹 Parsing FIT file: {file_path}")
    fitfile = fitparse.FitFile(file_path)

    data = []
    activity_type = "Unknown"
    activity_date = "UnknownDate"

    for record in fitfile.get_messages():
        record_data = {}
        for field in record:
            value = field.value
            if field.name == "sport":
                activity_type = value
            if field.name == "timestamp":
                activity_date = value.strftime("%Y-%m-%d")
            record_data[field.name] = value
        data.append(record_data)

    log_message(f"✅ FIT file parsed successfully: {file_path}")
    return data, activity_type, activity_date

# Function to authenticate with Google Drive
def authenticate_drive():
    log_message("🔹 Authenticating with Google Drive...")
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("client_secrets.json")

    try:
        gauth.LocalWebserverAuth()
        log_message("✅ Google Drive authentication successful!")
    except Exception as e:
        log_message(f"❌ Google Drive authentication failed: {e}")
        sys.exit(1)

    drive = GoogleDrive(gauth)
    return drive

# Function to upload JSON to Google Drive
def upload_to_drive(file_name, json_data):
    log_message("🔹 Connecting to Google Drive for upload...")
    drive = authenticate_drive()

    json_filename = f"{file_name.replace('.fit', '')}.json"
    json_path = os.path.join("fit_files", json_filename)

    log_message(f"🔹 Saving JSON file locally: {json_path}")
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=4)

    log_message(f"🔹 Uploading {json_filename} to Google Drive...")
    try:
        file_drive = drive.CreateFile({'title': json_filename})
        file_drive.SetContentFile(json_path)
        file_drive.Upload()
        log_message(f"✅ Successfully uploaded {json_filename} to Google Drive!")
    except Exception as e:
        log_message(f"❌ Failed to upload {json_filename}: {e}")
        sys.exit(1)

# Convert & Upload
def main():
    log_message("🔹 Checking for .FIT files in 'fit_files' folder...")
    fit_folder = "fit_files"
    fit_files = [f for f in os.listdir(fit_folder) if f.endswith(".fit")]

    if not fit_files:
        log_message("⚠️ No FIT files found. Exiting script.")
        sys.exit(0)

    for fit_file in fit_files:
        file_path = os.path.join(fit_folder, fit_file)
        log_message(f"🔹 Processing file: {fit_file}")
        json_data, activity_type, activity_date = parse_fit_file(file_path)
        upload_to_drive(fit_file, json_data)

if __name__ == "__main__":
    main()
