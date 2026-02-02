from django.contrib import admin
from sdr.models import *


class DeviceAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ("id", "name", "raw_name")
    readonly_fields = ("raw_name",)


class GroupAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "id",
        "name",
        "begin_frequency",
        "end_frequency",
    )


class SpectrogramAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "id",
        "device",
        "source",
        "begin_frequency",
        "end_frequency",
        "step_frequency",
        "begin_real_date",
        "end_real_date",
        "begin_model_date",
        "end_model_date",
        "data_file",
    )


class TransmissionAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "id",
        "device",
        "source",
        "middle_frequency",
        "group",
        "modulation",
        "media_class",
        "accuracy",
        "bandwidth",
        "duration",
        "begin_frequency",
        "end_frequency",
        "begin_date",
        "end_date",
        "data_file",
    )


class GainTestAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "id",
        "name",
        "device_prefix",
        "datetime",
    )


class AppSettingAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "id",
        "key",
        "value",
    )


admin.site.register(Device, DeviceAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Spectrogram, SpectrogramAdmin)
admin.site.register(Transmission, TransmissionAdmin)
admin.site.register(GainTest, GainTestAdmin)
admin.site.register(AppSetting, AppSettingAdmin)
