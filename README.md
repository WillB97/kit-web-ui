# kit-web-ui

## Development
This can be installed locally in WSL, Ubuntu and MacOS. These commands should be run while in the base of the repository.

Install dependencies
```bash
sudo apt install python3.10-venv
```

Create and activate a virtual environment
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
```

Install the repo as editable with the command:
```bash
pip install -e .
```

Copy `dev_env.example` to `dev_env`, and make sure it has windows line endings removed (dos2unix if necessary).

To generate a value for `DJANGO_SECRET_KEY` in the `dev_env` file run:
```bash
python -c 'import django.core.management.utils; print(django.core.management.utils.get_random_secret_key())'
```

To setup the database and create the superadmin user (you will need to enter a username and password in this step) run:
```bash
source django_env
django-admin migrate && django-admin collectstatic && django-admin createsuperuser
```

At this point you can run the webserver using:
```bash
source dev_env
django-admin runserver
```

### Building wheels
Wheels can be made for the dockerfile using:

```bash
pip install build
make build
```

## Deployment
Deploying on Ubuntu 22.04.

Install dependencies
```bash
sudo apt install nginx uwsgi uwsgi-plugin-python3 python3.10-dev python3.10-venv build-essential
```

Create a virtualenv under /srv/kit-web-ui
```bash
mkdir -p /srv/kit-web-ui && cd /srv/kit-web-ui
python3.10 -m venv venv
```

Install the package, wheel is required for the dependencies
```bash
. ./venv/bin/activate
pip install --upgrade pip wheel uwsgi
pip install kit-web-ui-x.y.z.whl
```

Copy all the files in the systemd folder to `/etc/systemd/system/`

Put SSL certificate and key in `/srv/kit-web-ui/certificates/` and name them `cert.pem`, `chain.pem` and `key.pem` respectively.

Setup nginx
```bash
sudo cp kit-web-ui.nginx /etc/nginx/sites-enabled/kit-web-ui.conf
sudo rm /etc/nginx/sites-enabled/default
```

Copy `env.example` to `/srv/kit-web-ui/django-env.env` and populate the fields.

Start the services that don't immediately connect to the database
```bash
systemctl daemon-reload && systemctl enable --now nginx uwsgi@kit-web-ui.socket
```

Allow django to generate the database and collect up static files to be served
```bash
set -o allexport
source /srv/kit-web-ui/django-env.env
set +o allexport
PYTHONPATH=/srv/kit-web-ui/ django-admin migrate
PYTHONPATH=/srv/kit-web-ui/ django-admin collectstatic
```

The webserver will start when the webpage is first visited.

Create the superuser
```bash
PYTHONPATH=/srv/kit-web-ui/ django-admin createsuperuser
```

## Mosquitto setup

Install mosquitto
```bash
sudo apt install mosquitto
```

Copy `mosquitto.conf` to `/etc/mosquitto/conf.d/kit-web-ui.conf` from the mosquitto folder in this repo.
Copy `mosquitto_acl.conf` to `/srv/kit-web-ui/mosquitto_acl.conf` from the mosquitto folder in this repo.

Create the mosquitto password file
```bash
sudo mosquitto_passwd -c /srv/kit-web-ui/mosquitto_passwd <username>
```

For any additional users, use the following command
```bash
sudo mosquitto_passwd /srv/kit-web-ui/mosquitto_passwd <username>
```

Fix certificate permissions and restart mosquitto
```bash
sudo systemctl restart mosquitto
```
