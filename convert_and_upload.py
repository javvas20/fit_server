import os
import json
import time
import requests
import datetime
import fitparse
import jwt  # PyJWT
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def parse_fit_files():
    """
    1) Finds all .fit files in 'fit_files' folder.
    2) Extracts **every** available metric, including advanced running dynamics.
    3) Converts to .json, ensuring datetime fields are serialized properly.
    4) Returns a list of .json file paths.
    """
    fit_folder = "fit_files"
    json_files = []

    if not os.path.exists(fit_folder):
        print(f"Folder '{fit_folder}' does not exist!")
        return []

    for file_name in os.listdir(fit_folder):
        if file_name.endswith(".fit"):
            fit_path = os.path.join(fit_folder, file_name)
            json_path = fit_path.replace(".fit", ".json")

            print(f"🔹 Converting: {fit_path} → {json_path}")

            # Parse the .fit file
            fitfile = fitparse.FitFile(fit_path)
            data = []

            for record in fitfile.get_messages():
                record_data = {}
                for field in record:
                    value = field.value

                    # Convert ALL date/time/datetime objects to ISO strings
                    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
                        value = value.isoformat()

                    # Store field data
                    record_data[field.name] = value
                
                # Only store if there's meaningful data
                if record_data:
                    data.append(record_data)

            # Write to JSON
            with open(json_path, "w") as jf:
                json.dump(data, jf, indent=4)

            print(f"✅ Created JSON: {json_path}")
            json_files.append(json_path)

    return json_files

def get_access_token(service_account_json):
    """
    Exchanges a JWT for an OAuth access token using a Google Service Account.
    Avoids interactive browser flows.
    """
    auth_url = "https://oauth2.googleapis.com/token"

    sa_info = json.loads(service_account_json)
    email = sa_info['client_email']
    private_key_str = sa_info['private_key']

    now = int(time.time())
    # Token valid for 1 hour
    expiry = now + 3600

    # Prepare JWT payload
    payload = {
        "iss": email,
        "scope": "https://www.googleapis.com/auth/drive.file",
        "aud": auth_url,
        "exp": expiry,
        "iat": now
    }

    # Convert the private key into a usable object
    key_bytes = private_key_str.encode("utf-8")
    private_key_obj = serialization.load_pem_private_key(
        key_bytes,
        password=None,
        backend=default_backend()
    )

    # Sign the JWT (RS256)
    jwt_token = jwt.encode(payload, private_key_obj, algorithm="RS256")

    # Exchange JWT for an OAuth access token
    resp = requests.post(auth_url, data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token
    })

    if resp.status_code != 200:
        raise Exception(f"Failed to get access token: {resp.text}")

    token_info = resp.json()
    access_token = token_info["access_token"]
    print("✅ Obtained Google Drive access token.")
    return access_token

def upload_to_drive(access_token, folder_id, json_file_path):
    """
    Uploads a .json file to Google Drive using a simple multipart POST request.
    """
    filename = os.path.basename(json_file_path)
    print(f"🔹 Uploading {filename} to Drive folder {folder_id}...")

    metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    # We'll send both metadata and file content as 'multipart/form-data'
    files = {
        "metadata": ("metadata.json", json.dumps(metadata), "application/json"),
        "file": (filename, open(json_file_path, "rb"), "application/json")
    }

    url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.post(url, headers=headers, files=files)
    if resp.status_code not in (200, 201):
        raise Exception(f"Drive upload failed: {resp.text}")

    drive_file_id = resp.json().get("id")
    print(f"✅ Uploaded {filename} successfully! Drive File ID: {drive_file_id}")

def main():
    print("=== Starting convert_and_upload.py ===")

    # 1) Parse all .fit files into .json
    json_files = parse_fit_files()
    if not json_files:
        print("No JSON files created (no .fit files found?). Exiting.")
        return

    # 2) Grab secrets from environment
    service_account_json = os.getenv("GDRIVE_SERVICE_ACCOUNT", "")
    folder_id = os.getenv("GDRIVE_FOLDER_ID", "")

    if not service_account_json or not folder_id:
        print("Skipping Google Drive upload because secrets are missing.")
        return

    # 3) Get an OAuth access token
    access_token = get_access_token(service_account_json)

    # 4) Upload each .json file to Drive
    for jf in json_files:
        upload_to_drive(access_token, folder_id, jf)

    print("=== All done! ===")

if __name__ == "__main__":
    main()
