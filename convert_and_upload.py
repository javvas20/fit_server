import datetime
import os
import json
import fitparse
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Function to parse .FIT file
def parse_fit_file(file_path):
    print(f"🔹 Parsing FIT file: {file_path}")
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

            if isinstance(value, datetime.time):
                value = value.isoformat()
            record_data[field.name] = value
        data.append(record_data)

    print(f"✅ FIT file parsed successfully: {file_path}")
    return data, activity_type, activity_date

# Authenticate with Google Drive
def authenticate_drive():
    print("🔹 Authenticating with Google Drive...")
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("client_secrets.json")

    try:
        gauth.LocalWebserverAuth()
        print("✅ Google Drive authentication successful!")
    except Exception as e:
        print(f"❌ Google Drive authentication failed: {e}")
        exit(1)

    drive = GoogleDrive(gauth)
    return drive

# Upload JSON to Google Drive
def upload_to_drive(file_name, json_data):
    drive = authenticate_drive()

    json_filename = f"{file_name.replace('.fit', '')}.json"
    json_path = os.path.join("fit_files", json_filename)

    print(f"🔹 Saving JSON file locally: {json_path}")
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"🔹 Uploading {json_filename} to Google Drive...")
    try:
        file_drive = drive.CreateFile({'title': json_filename})
        file_drive.SetContentFile(json_path)
        file_drive.Upload()
        print(f"✅ Successfully uploaded {json_filename} to Google Drive!")
    except Exception as e:
        print(f"❌ Failed to upload {json_filename}: {e}")

# Convert & Upload
def main():
    fit_folder = "fit_files"
    for fit_file in os.listdir(fit_folder):
        if fit_file.endswith(".fit"):
            file_path = os.path.join(fit_folder, fit_file)
            json_data, activity_type, activity_date = parse_fit_file(file_path)
            upload_to_drive(fit_file, json_data)

if __name__ == "__main__":
    main()
