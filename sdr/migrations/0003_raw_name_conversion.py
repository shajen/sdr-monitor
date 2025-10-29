from django.db import migrations
import sdr.utils.device


def raw_name_to_pretty_name(apps, schema_editor):
    Device = apps.get_model("sdr", "Device")
    for device in Device.objects.all():
        if device.name == device.raw_name:
            device.name = sdr.utils.device.convert_raw_to_name_to_pretty_name(device.raw_name)
            device.save(update_fields=["name"])


def pretty_name_to_raw_name(apps, schema_editor):
    Device = apps.get_model("sdr", "Device")
    for device in Device.objects.all():
        device.name = device.raw_name
        device.save(update_fields=["name"])


class Migration(migrations.Migration):
    dependencies = [
        ("sdr", "0002_auto_20250704_1732"),
    ]

    operations = [
        migrations.RunPython(raw_name_to_pretty_name, pretty_name_to_raw_name),
    ]
