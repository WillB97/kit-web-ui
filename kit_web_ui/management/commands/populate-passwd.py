"""
Generate the mosquitto password file from the database.
The existing passwd file is passed as an argument to the script. The existing
file is backed up before being overwritten.

Configured mqtt usernames and passwords are read from the database and hashed
with the mosquitto_passwd command. The existing passwd file is then read and
all lines that do not start with "team" are copied to the new file.
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Populate the mosquitto password file'

    def add_arguments(self, parser) -> None:  # type: ignore
        parser.add_argument('passwd_file', type=str, help='Path to the passwd file')
        parser.add_argument(
            '--reload-broker', action='store_true',
            help='Reload the mosquitto broker after updating the passwd file')

    def handle(self, *args, **options) -> None:  # type: ignore
        import os
        from pathlib import Path

        from kit_web_ui.models import MqttConfig

        passwd_file = options['passwd_file']
        self.stdout.write(f"Populating passwd file: {passwd_file}")
        mqtt_config = MqttConfig.objects.all()
        if mqtt_config.count() == 0:
            raise CommandError("No MQTT credentials configured")

        # backup the existing passwd file
        passwd_file_path = Path(passwd_file)
        if passwd_file_path.exists():
            backup_file = passwd_file_path.with_suffix('.bak')
            self.stdout.write(f"Backing up existing passwd file to {backup_file}")
            passwd_file_path.rename(backup_file)
        else:
            backup_file = None

        with open(passwd_file, 'w') as passwd:
            for team in mqtt_config:
                passwd.write(f"{team.username}:{team.password}\n")

        os.system(f"mosquitto_passwd -U {passwd_file}")
        if backup_file:
            with open(passwd_file, 'a') as passwd, open(backup_file) as backup:
                for line in backup:
                    if not line.startswith("team"):
                        passwd.write(line)

        if options['reload_broker']:
            os.system("systemctl reload mosquitto")

        self.stdout.write("Done")
