"""Setup a tale with versions.

Needs to be run from root of deploy-dev, like this:

    export DEFAULT_GIRDER_USER=<your girder username>
    sudo -E -u "#999" python3 scripts/create_versioned_tale.py
"""

import base64
import json
import requests
import os
import pathlib
import shutil
from requests.auth import HTTPBasicAuth

# Obfuscate emails via `base64.b64encode(json.dumps(DEVS).encode())`

DEVS_RAW = b"eyJ3aWxsaXM4IjogeyJlbWFpbCI6ICJ3aWxsaXM4QGlsbGlub2lzLmVkdSIsICJsYXN0TmFtZSI6ICJXaWxsaXMiLCAiZmlyc3ROYW1lIjogIkNyYWlnIiwgImxvZ2luIjogIndpbGxpczgifSwgImNhd2lsbGlzIjogeyJlbWFpbCI6ICJjYXdpbGxpc0BnbWFpbC5jb20iLCAibGFzdE5hbWUiOiAiV2lsbGlzIiwgImZpcnN0TmFtZSI6ICJDcmFpZyIsICJsb2dpbiI6ICJjYXdpbGxpcyJ9LCAibGFtYmVydDgiOiB7ImVtYWlsIjogImxhbWJlcnQ4QGlsbGlub2lzLmVkdSIsICJsYXN0TmFtZSI6ICJMYW1iZXJ0IiwgImZpcnN0TmFtZSI6ICJNaWNoYWVsIiwgImxvZ2luIjogImxhbWJlcnQ4In0sICJ0aGVsZW4iOiB7ImVtYWlsIjogInRoZWxlbkBuY2Vhcy51Y3NiLmVkdSIsICJsYXN0TmFtZSI6ICJUaGVsZW4iLCAiZmlyc3ROYW1lIjogIlRob21hcyIsICJsb2dpbiI6ICJ0aGVsZW4ifSwgInRob21hc3RoZWxlbiI6IHsiZW1haWwiOiAidGhlbGUyMzQ1bkBuY2Vhcy51Y3NiLmVkdSIsICJsYXN0TmFtZSI6ICJUaGVsZW4iLCAiZmlyc3ROYW1lIjogIlRob21hcyIsICJsb2dpbiI6ICJ0aG9tYXN0aGVsZW4ifSwgImtvd2FsaWtrIjogeyJlbWFpbCI6ICJrb3dhbGlra0BpbGxpbm9pcy5lZHUiLCAibGFzdE5hbWUiOiAiS293YWxpayIsICJmaXJzdE5hbWUiOiAiS2FjcGVyIiwgImxvZ2luIjogImtvd2FsaWtrIn19"

DEVS = json.loads(base64.b64decode(DEVS_RAW).decode())

entity = os.environ.get("DEFAULT_GIRDER_USER")
if entity not in DEVS.keys():
    print("Run: export DEFAULT_GIRDER_USER=<your girder username>")
    print(f'Available choices: [{" ".join(DEVS.keys())}]')
    exit()

entity = DEVS[entity]
entity.update({"admin": False, "password": "password"})

headers = {"Content-Type": "application/json", "Accept": "application/json"}
api_url = "https://girder.local.wholetale.org/api/v1"

try:
    r = requests.post(api_url + "/user", params=entity, headers=headers)
    r.raise_for_status()
except requests.HTTPError:
    if r.status_code == 400:
        r = requests.get(
            api_url + "/user/authentication",
            auth=HTTPBasicAuth(entity["login"], entity["password"]),
        )
        r.raise_for_status()
    else:
        raise
except Exception:
    print("Girder is no longer running")
    raise

headers["Girder-Token"] = r.json()["authToken"]["token"]

r = requests.get(api_url + "/user/me", headers=headers)
r.raise_for_status()
image = requests.get(api_url + "/image", params={"text": '"JupyterLab"'}).json()[
    0
]
tale = {
    "authors": [
        {
            "firstName": "Kacper",
            "lastName": "Kowalik",
            "orcid": "https://orcid.org/0000-0003-1709-3744",
        }
    ],
    "category": "science",
    "config": {},
    "dataSet": [],
    "description": "Something something...",
    "imageId": image["_id"],
    "public": False,
    "published": False,
    "title": "CiS",
}

r = requests.post(api_url + "/tale", headers=headers, json=tale)
r.raise_for_status()
tale = r.json()

root_workspace = pathlib.Path(f"volumes/workspaces/{tale['_id'][0]}/{tale['_id']}")
some_file = root_workspace / "Dockerfile"
with open(some_file, "w") as fp:
    fp.write("FROM cropsinsilico/jupyterlab:latest")
