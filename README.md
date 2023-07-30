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

