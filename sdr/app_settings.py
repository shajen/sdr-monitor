from common.utils.type import *
from django import forms
from enum import Enum
from sdr.models import *


class AppSettingsKey(Enum):
    SPECTROGRAMS_TOTAL_SIZE_GB = ("spectrograms_total_size_gb", 0, int)
    TRANSMISSIONS_TOTAL_SIZE_GB = ("transmissions_total_size_gb", 0, int)
    N2YO_API_KEY = ("n2yo_api_key", "", str)

    def __init__(self, key: str, default, cast):
        self.key = key
        self.default = default
        self.cast = cast


class AppSettings:
    @staticmethod
    def get(setting: AppSettingsKey):
        try:
            obj = AppSetting.objects.get(key=setting.key)
            return setting.cast(obj.value)
        except AppSetting.DoesNotExist:
            return setting.default
        except (ValueError, TypeError):
            return setting.default

    @staticmethod
    def set(setting: AppSettingsKey, value):
        AppSetting.objects.update_or_create(key=setting.key, defaults={"value": str(value)})


class AppSettingsForm(forms.Form):
    n2yo_api_key = forms.CharField(label="n2yo api key", max_length=255, required=False, help_text="get your key from https://n2yo.com/api/")
    spectrograms_total_size_gb = forms.IntegerField(label="Spectrograms size", help_text="keep only the last n GB of spectrograms, 0 for unlimited")
    transmissions_total_size_gb = forms.IntegerField(label="Transmissions size", help_text="keep only the last n GB of transmissions, 0 for unlimited")

    def load_initial(self):
        self.initial = {
            AppSettingsKey.SPECTROGRAMS_TOTAL_SIZE_GB.key: AppSettings.get(AppSettingsKey.SPECTROGRAMS_TOTAL_SIZE_GB),
            AppSettingsKey.TRANSMISSIONS_TOTAL_SIZE_GB.key: AppSettings.get(AppSettingsKey.TRANSMISSIONS_TOTAL_SIZE_GB),
            AppSettingsKey.N2YO_API_KEY.key: AppSettings.get(AppSettingsKey.N2YO_API_KEY),
        }

    def save(self):
        data = self.cleaned_data
        AppSettings.set(AppSettingsKey.SPECTROGRAMS_TOTAL_SIZE_GB, data[AppSettingsKey.SPECTROGRAMS_TOTAL_SIZE_GB.key])
        AppSettings.set(AppSettingsKey.TRANSMISSIONS_TOTAL_SIZE_GB, data[AppSettingsKey.TRANSMISSIONS_TOTAL_SIZE_GB.key])
        AppSettings.set(AppSettingsKey.N2YO_API_KEY, data[AppSettingsKey.N2YO_API_KEY.key])
