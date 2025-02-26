import os
import json
import time
import signal
import datetime
import fitparse
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

### ✅ 1️⃣ Print Start Message ###
print("✅ Script started: Running convert_and_upload.py")

### ✅ 2️⃣ Check if Google Drive Credentials Exist ###
if not os.path.exists("client_secrets.json"):
    print("❌ ERROR: `client_secrets.json` is missing! Exiting workflow.")
    exit(1)
else:
    print("✅ Google Drive credentials file found.")

### ✅ 3️⃣ Timeout Handler for FIT File Parsing ###
def timeout_handler(signum, frame):
    raise TimeoutError("❌ ERROR: FIT file processing took too long! Exiting.")

signal.signal(signal.SIGALRM, timeout_handler)

### ✅ 4️⃣ Google Drive Authentication with Timeout ###
def authenticate_drive():
    print("🔹 [STEP] Authenticating with Google Drive...")
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("client_secrets.json")

    try:
        start_time = time.time()
        gauth.LocalWebserverAuth()
        elapsed_time = time.time() - start_time

        if elapsed_time > 30:  # Google authentication timeout (30 sec)
            raise TimeoutError("❌ ERROR: Google Drive authentication took too long!")

        print("✅ [SUCCESS] Google Drive authentication successful!")
    except Exception as e:
        print(f"❌ ERROR: Google Drive authentication failed: {e}")
        exit(1)

    drive = GoogleDrive(gauth)
    return drive

### ✅ 5️⃣ FIT File Parsing with Timeout ###
def parse_fit_file(file_path):
    print(f"🔹 [STEP] Parsing FIT file: {file_path}")

    # Set timeout (30 sec max)
    signal.alarm(30)

    try:
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

        signal.alarm(0)  # Cancel timeout after success
        print(f"✅ [SUCCESS] FIT file parsed successfully: {file_path}")

        return data, activity_type, activity_date
    except TimeoutError:
        print("❌ ERROR: FIT file parsing took too long! Exiting.")
        exit(1)
    except Exception as e:
        print(f"❌ ERROR: Failed to parse FIT file: {e}")
        exit(1)

### ✅ 6️⃣ Upload JSON to Google Drive ###
def upload_to_drive(file_name, json_data):
    print("🔹 [STEP] Connecting to Google Drive for upload...")
    drive = authenticate_drive()

    json_filename = f"{file_name.replace('.fit', '')}.json"
    json_path = os.path.join("fit_files", json_filename)

    print(f"🔹 [STEP] Saving JSON file locally: {json_path}")
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"🔹 [STEP] Uploading {json_filename} to Google Drive...")
    try:
        file_drive = drive.CreateFile({'title': json_filename})
        file_drive.SetContentFile(json_path)
        file_drive.Upload()
        print(f"✅ [SUCCESS] Successfully uploaded {json_filename} to Google Drive!")
    except Exception as e:
        print(f"❌ ERROR: Failed to upload {json_filename}: {e}")
        exit(1)

### ✅ 7️⃣ Main Function ###
def main():
    print("✅ [START] Script execution begins.")

    fit_folder = "fit_files"
    fit_files = [f for f in os.listdir(fit_folder) if f.endswith(".fit")]

    if not fit_files:
        print("❌ ERROR: No FIT files found! Exiting.")
        exit(1)

    for fit_file in fit_files:
        file_path = os.path.join(fit_folder, fit_file)
        json_data, activity_type, activity_date = parse_fit_file(file_path)
        upload_to_drive(fit_file, json_data)

    print("✅ [DONE] Script execution finished successfully.")

if __name__ == "__main__":
    main()

