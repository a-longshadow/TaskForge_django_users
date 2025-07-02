from django.core.management.base import BaseCommand

from tasks.models import AppSetting

DEFAULTS = {
    "MONDAY_BOARD_ID": "9212659997",
    "MONDAY_GROUP_ID": "group_mkqyryrz",
    "MONDAY_COLUMN_MAP": (
        '{"team_member":"text_mkr7jgkp","email":"text_mkr0hqsb","priority":"status_1","status":"status","due_date":"date5","brief_description":"long_text"}'
    ),
}

class Command(BaseCommand):
    help = "Create default Monday.com AppSettings if they don't exist"

    def handle(self, *args, **options):
        created = 0
        for key, val in DEFAULTS.items():
            obj, was_created = AppSetting.objects.get_or_create(key=key, defaults={"value": val})
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} Monday settings (idempotent).")) 