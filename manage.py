#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_rls.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    def alias_map(argv):
        from django.conf import settings

        if len(argv) > 1:
            argv[1:2] = (
                getattr(settings, "COMMAND_ALIASES", {})
                .get(argv[1], argv[1])
                .split(" ")
            )
        return argv

    execute_from_command_line(alias_map(sys.argv))


if __name__ == "__main__":
    main()
