#!/usr/bin/env python
import json
import requests
import time
import os
import sys

params = {
    "login": "admin",
    "email": "root@dev.null",
    "firstName": "John",
    "lastName": "Doe",
    "password": "arglebargle123",
    "admin": True,
}
headers = {"Content-Type": "application/json", "Accept": "application/json"}


def final_msg():
    print("-------------- You should be all set!! -------------")
    print("try going to https://girder.local.wholetale.org and log in with: ")
    print("  user : %s" % params["login"])
    print("  pass : %s" % params["password"])


api_url = "https://girder.local.wholetale.org/api/v1"

# Give girder time to start
while True:
    print("Waiting for Girder to start")
    r = requests.get(api_url)
    if r.status_code == 200:
        break
    time.sleep(2)

print("Creating admin user")
r = requests.post(api_url + "/user", params=params, headers=headers)
if r.status_code == 400:
    print("Admin user already exists. Database was not purged.")
    print("If that is OK:")
    final_msg()
    sys.exit()

# Store token for future requests
headers["Girder-Token"] = r.json()["authToken"]["token"]

print("Creating default assetstore")
r = requests.post(
    api_url + "/assetstore",
    headers=headers,
    params={
        "type": 0,
        "name": "Base",
        "root": "/tmp/data/base",
    },
)

print("Enabling plugins")
plugins = [
    "oauth",
    "gravatar",
    "jobs",
    "worker",
    "globus_handler",
    "virtual_resources",
    "wt_data_manager",
    "wholetale",
    "wt_home_dir",
    "wt_versioning",
    "cis",
]
r = requests.put(
    api_url + "/system/plugins",
    headers=headers,
    params={"plugins": json.dumps(plugins)},
)
r.raise_for_status()

print("Restarting girder to load plugins")
r = requests.put(api_url + "/system/restart", headers=headers)
r.raise_for_status()

# Give girder time to restart
while True:
    print("Waiting for Girder to restart")
    r = requests.get(
        api_url + "/oauth/provider",
        headers=headers,
        params={"redirect": "http://blah.com"},
    )
    if r.status_code == 200:
        break
    time.sleep(2)

print("Setting up Plugin")

settings = [
    {
        "key": "core.cors.allow_origin",
        "value": "https://dashboard.local.wholetale.org,https://ui.local.wholetale.org",
    },
    {
        "key": "core.cors.allow_headers",
        "value": (
            "Accept-Encoding, Authorization, Content-Disposition, Set-Cookie, "
            "Content-Type, Cookie, Girder-Authorization, Girder-Token, "
            "X-Requested-With, X-Forwarded-Server, X-Forwarded-For, "
            "X-Forwarded-Host, Remote-Addr, Cache-Control"
        ),
    },
    {"key": "worker.api_url", "value": "http://girder:8080/api/v1"},
    {"key": "worker.broker", "value": "redis://redis/"},
    {"key": "worker.backend", "value": "redis://redis/"},
    {"key": "oauth.globus_client_id", "value": os.environ.get("GLOBUS_CLIENT_ID")},
    {
        "key": "oauth.globus_client_secret",
        "value": os.environ.get("GLOBUS_CLIENT_SECRET"),
    },
    {"key": "oauth.orcid_client_id", "value": os.environ.get("ORCID_CLIENT_ID")},
    {
        "key": "oauth.orcid_client_secret",
        "value": os.environ.get("ORCID_CLIENT_SECRET"),
    },
    {"key": "oauth.providers_enabled", "value": ["globus"]},
    {"key": "dm.globus_gc_dir", "value": "/opt/globusconnectpersonal"},
    {
        "key": "wholetale.dataverse_extra_hosts",
        "value": ["dev2.dataverse.org", "demo.dataverse.org"],
    },
    {
        "key": "wholetale.zenodo_extra_hosts",
        "value": ["https://sandbox.zenodo.org/record/"]
    },
    {"key": "dm.private_storage_path", "value": "/tmp/data/ps"},
    {"key": "wthome.homedir_root", "value": "/tmp/data/homes"},
    {"key": "wthome.taledir_root", "value": "/tmp/data/workspaces"},
    {"key": "wtversioning.runs_root", "value": "/tmp/data/runs"},
    {"key": "wtversioning.versions_root", "value": "/tmp/data/versions"},
]

r = requests.put(
    api_url + "/system/setting", headers=headers, params={"list": json.dumps(settings)}
)
try:
    r.raise_for_status()
except requests.exceptions.HTTPError:
    if r.status_code >= 400 and r.status_code < 500:
        print(f"Request died with {r.status_code}: {r.reason}")
        print(f"Returned: {r.text}")
    raise

print("Create a Jupyter image")
i_params = {
    "config": json.dumps(
        {
            "command": (
                "jupyter notebook --no-browser --port {port} --ip=0.0.0.0 "
                "--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} "
                "--NotebookApp.port_retries=0"
            ),
            "memLimit": "2048m",
            "port": 8888,
            "targetMount": "/home/jovyan/work",
            "urlPath": "?token={token}",
            "buildpack": "PythonBuildPack",
            "user": "jovyan",
        }
    ),
    "icon": (
        "https://raw.githubusercontent.com/whole-tale/jupyter-base/master/"
        "squarelogo-greytext-orangebody-greymoons.png"
    ),
    "iframe": True,
    "name": "Jupyter Notebook",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()


print("Create an RStudio image")
i_params = {
    "config": json.dumps(
        {
            "command": "/start.sh",
            "environment": [
                "PASSWORD=djkslajdklasjdklsajd",
            ],
            "memLimit": "2048m",
            "port": 8787,
            "targetMount": "/WholeTale",
            "urlPath": "",
            "buildpack": "RockerBuildPack",
            "user": "rstudio",
        }
    ),
    "icon": "https://www.rstudio.com/wp-content/uploads/" "2014/06/RStudio-Ball.png",
    "iframe": True,
    "name": "RStudio",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()

print("Create a Jupyter Lab image")
i_params = {
    "config": json.dumps(
        {
            "command": (
                "jupyter notebook --no-browser --port {port} --ip=0.0.0.0 "
                "--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} "
                "--NotebookApp.port_retries=0"
            ),
            "memLimit": "2048m",
            "port": 8888,
            "targetMount": "/home/jovyan/work",
            "urlPath": "lab?token={token}",
            "buildpack": "PythonBuildPack",
            "user": "jovyan",
        }
    ),
    "fullName": "xarthisius/jupyter",
    "icon": (
        "https://raw.githubusercontent.com/whole-tale/jupyter-base/master/"
        "squarelogo-greytext-orangebody-greymoons.png"
    ),
    "iframe": True,
    "name": "Jupyter Lab",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()

print("Create OpenRefine image")
i_params = {
    "config": json.dumps(
        {
            "memLimit": "2048m",
            "port": 3333,
            "targetMount": "/wholetale",
            "urlPath": "",
            "buildpack": "OpenRefineBuildPack",
            "user": "wtuser",
        }
    ),
    "icon": (
        "https://raw.githubusercontent.com/whole-tale/openrefine/master/openrefine_logo.png"
    ),
    "iframe": True,
    "name": "OpenRefine",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()

print("Create Jupyter Spark image")
i_params = {
    "config": json.dumps(
        {
            "command": (
                "jupyter notebook --no-browser --port {port} --ip=0.0.0.0 "
                "--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} "
                "--NotebookApp.port_retries=0"
            ),
            "memLimit": "2048m",
            "port": 8888,
            "targetMount": "/home/jovyan/work",
            "urlPath": "lab?token={token}",
            "buildpack": "SparkBuildPack",
            "user": "jovyan",
        }
    ),
    "icon": (
        "https://raw.githubusercontent.com/whole-tale/jupyter-base/master/"
        "squarelogo-greytext-orangebody-greymoons.png"
    ),
    "iframe": True,
    "name": "Jupyter with Spark",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()

print('Create Jupyter with R image')
i_params = {
    'config': json.dumps({
        'command': (
            'jupyter notebook --no-browser --port {port} --ip=0.0.0.0 '
            '--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} '
            '--NotebookApp.port_retries=0'
        ),
        'memLimit': '2048m',
        'port': 8888,
        'targetMount': '/home/jovyan/work',
        'urlPath': '?token={token}',
        'buildpack': 'RBuildPack',
        'user': 'jovyan'
    }),
    'icon': (
        'https://raw.githubusercontent.com/whole-tale/jupyter-base/master/'
        'squarelogo-greytext-orangebody-greymoons.png'
    ),
    'iframe': True,
    'name': 'Jupyter with R',
    'public': True
}
r = requests.post(api_url + '/image', headers=headers,
                  params=i_params)
r.raise_for_status()
image = r.json()

print('Create Jupyter with Matlab image')
i_params = {
    'config': json.dumps({
        'command': (
            'jupyter notebook --no-browser --port {port} --ip=0.0.0.0 '
            '--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} '
            '--NotebookApp.port_retries=0'
        ),
        'environment': [
            'VERSION=R2020b'
        ],
        'memLimit': '2048m',
        'port': 8888,
        'targetMount': '/home/jovyan/work',
        'urlPath': 'lab?token={token}',
        'buildpack': 'MatlabBuildPack',
        'user': 'jovyan'
    }),
    'icon': (
        'https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/'
        'Matlab_Logo.png/267px-Matlab_Logo.png'
    ),
    'iframe': True,
    'name': 'MATLAB (Jupyter Kernel)',
    'public': True
}
r = requests.post(api_url + '/image', headers=headers,
                  params=i_params)
r.raise_for_status()
image = r.json()

print('Create Matlab Xpra image')
i_params = {
    'config': json.dumps({
        'command': (
            'xpra start --bind-tcp=0.0.0.0:10000 --html=on --daemon=no --exit-with-children=no --start-after-connect="matlab -desktop"'
        ),
        'environment': [
            'VERSION=R2020b'
        ],
        'memLimit': '2048m',
        'port': 10000,
        'targetMount': '/home/jovyan/work',
        'urlPath': '/',
        'buildpack': 'MatlabBuildPack',
        'user': 'jovyan'
    }),
    'icon': (
        'https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/'
        'Matlab_Logo.png/267px-Matlab_Logo.png'
    ),
    'iframe': True,
    'name': 'MATLAB (Linux Desktop)',
    'public': True
}
r = requests.post(api_url + '/image', headers=headers,
                  params=i_params)
r.raise_for_status()
image = r.json()

print('Create Matlab Web Desktop image')
i_params = {
    'config': json.dumps({
        'command': (
            'matlab-jupyter-app'
        ),
        'environment': [
            'VERSION=R2020b'
        ],
        'memLimit': '2048m',
        'port': 8888,
        'targetMount': '/home/jovyan/work',
        'urlPath': 'matlab/index.html',
        'buildpack': 'MatlabBuildPack',
        'user': 'jovyan',
        'csp': "default-src 'self' *.mathworks.com:*; style-src 'self' 'unsafe-inline' *.mathworks.com:*; script-src 'self' 'unsafe-inline' 'unsafe-eval' *.mathworks.com:*; img-src 'self' *.mathworks.com:* data:; frame-ancestors 'self' *.mathworks.com:* dashboard.local.wholetale.org; frame-src 'self' *.mathworks.com:*; connect-src 'self' *.mathworks.com:* wss://localhost:* wss://127.0.0.1:*"
    }),
    'icon': (
        'https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/'
        'Matlab_Logo.png/267px-Matlab_Logo.png'
    ),
    'iframe': True,
    'name': 'MATLAB (Desktop)',
    'public': True
}
r = requests.post(api_url + '/image', headers=headers,
                  params=i_params)
r.raise_for_status()
image = r.json()

print('Create Jupyter with Stata image')
i_params = {
    'config': json.dumps({
        'command': (
            'jupyter notebook --no-browser --port {port} --ip=0.0.0.0 '
            '--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} '
            '--NotebookApp.port_retries=0'
        ),
        'environment': [
            'VERSION=16'
        ],
        'memLimit': '2048m',
        'port': 8888,
        'targetMount': '/home/jovyan/work',
        'urlPath': 'lab?token={token}',
        'buildpack': 'StataBuildPack',
        'user': 'jovyan'
    }),
    'icon': (
        'https://raw.githubusercontent.com/whole-tale/stata-install/main/stata-square.png'
    ),
    'iframe': True,
    'name': 'STATA (Jupyter)',
    'public': True
}
r = requests.post(api_url + '/image', headers=headers,
                  params=i_params)
r.raise_for_status()
image = r.json()

print('Create Stata Xpra image')
i_params = {
    'config': json.dumps({
        'command': (
            'xpra start --bind-tcp=0.0.0.0:10000 --html=on --daemon=no --exit-with-children=no --start-after-connect=xstata'
        ),
        'environment': [
            'VERSION=16'
        ],
        'memLimit': '2048m',
        'port': 10000,
        'targetMount': '/home/jovyan/work',
        'urlPath': '/',
        'buildpack': 'StataBuildPack',
        'user': 'jovyan'
    }),
    'icon': (
        'https://raw.githubusercontent.com/whole-tale/stata-install/main/stata-square.png'
    ),
    'iframe': True,
    'name': 'STATA (Desktop)',
    'public': True
}
r = requests.post(api_url + '/image', headers=headers,
                  params=i_params)
r.raise_for_status()
image = r.json()

print("Restarting girder to update WebDav roots")
r = requests.put(api_url + "/system/restart", headers=headers)
r.raise_for_status()
final_msg()
