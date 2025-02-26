import os
import json
import time
import requests
import fitparse
import datetime
import jwt  # PyJWT
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# 1) Convert all .fit files in 'fit_files/' to .json
def convert_fit_files():
    json_files = []
    for fname in os.listdir('fit_files'):
        if fname.endswith('.fit'):
            fit_path = os.path.join('fit_files', fname)
            json_path = fit_path.replace('.fit', '.json')
            print(f"Converting {fit_path} → {json_path}")

            # Parse the .fit file
            data = []
            fitfile = fitparse.FitFile(fit_path)
            for record in fitfile.get_messages():
                record_data = {}
                for field in record:
                    val = field.value
                    # If it's a datetime.time, convert to string
                    if isinstance(val, datetime.time):
                        val = val.isoformat()
                    record_data[field.name] = val
                data.append(record_data)

            # Write JSON next to .fit
            with open(json_path, 'w') as jf:
                json.dump(data, jf, indent=4)
            json_files.append(json_path)
    return json_files

# 2) Get an OAuth access token using a Service Account (JWT)
def get_access_token(service_account_json):
    # Parse the service account JSON
    sa_info = json.loads(service_account_json)
    email = sa_info['client_email']
    private_key = sa_info['private_key']
    # Google OAuth token URL for service accounts
    auth_url = "https://oauth2.googleapis.com/token"

    # Construct a JWT for Drive scope
    now = int(time.time())
    # Expire in 1 hour
    expiry = now + 3600

    payload = {
        "iss": email,
        "scope": "https://www.googleapis.com/auth/drive.file",
        "aud": auth_url,
        "exp": expiry,
        "iat": now
    }

    # Sign the JWT with the private key
    # Convert private_key (str) → cryptography object
    key_bytes = private_key.encode('utf-8')
    private_key_obj = serialization.load_pem_private_key(key_bytes, password=None, backend=default_backend())

    jwt_token = jwt.encode(payload, private_key_obj, algorithm="RS256")

    # Exchange JWT for access token
    resp = requests.post(auth_url, data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token
    })

    if resp.status_code != 200:
        raise Exception(f"Failed to get access token: {resp.text}")

    token_info = resp.json()
    access_token = token_info["access_token"]
    return access_token

# 3) Upload .json files to Google Drive using raw HTTP
def upload_to_drive(access_token, folder_id, json_file):
    # We'll do a multipart upload:
    # 1. Metadata (JSON)
    # 2. File content
    filename = os.path.basename(json_file)
    metadata = {
        "name": filename,
        "parents": [folder_id]  # Put in the shared folder
    }

    files = {
        'metadata': ('metadata.json', json.dumps(metadata), 'application/json'),
        'file': (filename, open(json_file, 'rb'), 'application/json')
    }

    resp = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        headers={"Authorization": f"Bearer {access_token}"},
        files=files
    )
    if resp.status_code not in [200, 201]:
        raise Exception(f"Drive upload failed: {resp.text}")
    print(f"Uploaded {filename} to Google Drive. File ID: {resp.json().get('id')}")

# 4) Main Script
def main():
    print("Starting FIT → JSON conversion...")
    json_files = convert_fit_files()
    if not json_files:
        print("No .fit files found. Exiting.")
        return

    # Read service account from env (populated by GitHub secret)
    service_account_json = os.getenv("GDRIVE_SERVICE_ACCOUNT")
    if not service_account_json:
        print("No GDRIVE_SERVICE_ACCOUNT env var found. Skipping Drive upload.")
        return

    # Folder ID from env (or fallback if you want)
    folder_id = os.getenv("GDRIVE_FOLDER_ID", "")
    if not folder_id:
        print("No GDRIVE_FOLDER_ID provided. Skipping Drive upload.")
        return

    print("Getting access token for Google Drive service account...")
    access_token = get_access_token(service_account_json)

    print("Uploading JSON files to Google Drive...")
    for jf in json_files:
        upload_to_drive(access_token, folder_id, jf)

    print("All done!")

if __name__ == "__main__":
    main()


