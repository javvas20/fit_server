import os
import json
import datetime
import fitparse
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Function to parse .FIT file and convert to JSON
def parse_fit_file(file_path):
    fitfile = fitparse.FitFile(file_path)
    data = []

    for record in fitfile.get_messages():
        record_data = {}
        for field in record:
            value = field.value
            if isinstance(value, datetime.time):
                value = value.isoformat()
            record_data[field.name] = value
        data.append(record_data)

    return data

# Function to authenticate with Google Drive
def authenticate_drive():
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("client_secrets.json")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    drive = GoogleDrive(gauth)
    return drive

# Function to upload JSON to Google Drive
def upload_to_drive(file_name, json_data):
    drive = authenticate_drive()

    # Save JSON file locally
    json_path = file_name.replace('.fit', '.json')
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=4)

    # Upload to Google Drive
    file_drive = drive.CreateFile({'title': os.path.basename(json_path)})
    file_drive.SetContentFile(json_path)
    file_drive.Upload()
    print(f"✅ Uploaded: {json_path} to Google Drive.")

# Main function to process files in "fit_files" folder
def main():
    fit_folder = "fit_files"
    if not os.path.exists(fit_folder):
        os.makedirs(fit_folder)

    for fit_file in os.listdir(fit_folder):
        if fit_file.endswith(".fit"):
            file_path = os.path.join(fit_folder, fit_file)
            json_data = parse_fit_file(file_path)
            upload_to_drive(fit_file, json_data)

if __name__ == "__main__":
    main()
