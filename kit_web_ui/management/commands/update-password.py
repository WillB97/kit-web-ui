"""
Update the password for an existing user.

If a wordlist is specified, the password is generated by choosing two words from
the wordlist and joining them with a hyphen. Otherwise, the password is a randomly
generated 12 character alphanumeric string.
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Generate team accounts and MQTT credentials'

    def add_arguments(self, parser) -> None:  # type: ignore
        parser.add_argument('--user', required=True, type=str, help='Broker listener name')
        parser.add_argument(
            '--wordlist', type=str, help=(
                'Word list for password generation. If not specified, passwords will be '
                'randomly generated. i.e. /usr/share/dict/british-english'))

    def handle(self, *args, **options) -> None:  # type: ignore
        from django.contrib.auth.models import User
        from kit_web_ui.utils import generate_wordlist, generate_password

        if options['wordlist']:
            wordlist = generate_wordlist(options['wordlist'])
        else:
            wordlist = None

        try:
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            raise CommandError(f"User {options['user']} does not exist")

        password = generate_password(wordlist)
        user.set_password(password)
        user.save()
        self.stdout.write(f"Updated password for {options['user']}: {password}")

        self.stdout.write("Done")
