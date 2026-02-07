from django.db import models
from django.utils.timezone import timedelta

AUDIO_MODULATIONS = ["AM", "NBFM"]
AUDIO_MODULATIONS_NO_AUTO_DETECT = ["WBFM"]
TXT_MODULATIONS = ["AFSK 1200"]


def get_default_device_id():
    return Device.objects.get_or_create(raw_name="Default")[0].id


def get_default_group_id():
    return Group.objects.get_or_create(name="Default", begin_frequency=0, end_frequency=10000000000)[0].id


def get_default_audio_class_id():
    return 1


def get_default_modulation():
    return "Default"


def get_default_media_class():
    return "Default"


def get_media_type(modulation):
    if modulation in AUDIO_MODULATIONS or modulation in AUDIO_MODULATIONS_NO_AUTO_DETECT:
        return "audio"
    elif modulation in TXT_MODULATIONS:
        return "txt"
    else:
        return ""


class Device(models.Model):
    name = models.CharField("Name", max_length=255)
    raw_name = models.CharField("Raw name", max_length=255, db_index=True, unique=True)

    def __str__(self):
        return self.raw_name


class Spectrogram(models.Model):
    begin_frequency = models.PositiveBigIntegerField("Begin (frequency)", db_index=True)
    end_frequency = models.PositiveBigIntegerField("End (frequency)", db_index=True)
    step_frequency = models.PositiveIntegerField("Step (frequency)", db_index=True)
    begin_model_date = models.DateTimeField("Begin (model)", db_index=True)
    end_model_date = models.DateTimeField("End (model)", db_index=True)
    begin_real_date = models.DateTimeField("Begin (data)", db_index=True)
    end_real_date = models.DateTimeField("End (data)", db_index=True)
    sample_nos = models.PositiveBigIntegerField("Labels", db_index=True)
    data_file = models.FileField("Data file", upload_to="spectrogram/%Y-%m-%d/")
    labels_file = models.FileField("Labels data file", upload_to="spectrogram/%Y-%m-%d/")
    device = models.ForeignKey(Device, on_delete=models.CASCADE, default=get_default_device_id)
    source = models.CharField("Source", max_length=255)

    class Meta:
        unique_together = ("device", "begin_frequency", "end_frequency", "step_frequency", "begin_model_date", "end_model_date")


class Group(models.Model):
    name = models.CharField("Name", max_length=255)
    begin_frequency = models.PositiveBigIntegerField("Begin frequency", db_index=True)
    end_frequency = models.PositiveBigIntegerField("End frequency", db_index=True)

    class Meta:
        unique_together = ("name", "begin_frequency", "end_frequency")

    def __str__(self):
        return self.name


class Transmission(models.Model):
    begin_frequency = models.PositiveBigIntegerField("Begin (frequency)", db_index=True)
    end_frequency = models.PositiveBigIntegerField("End (frequency)", db_index=True)
    begin_date = models.DateTimeField("Begin (date)", db_index=True)
    end_date = models.DateTimeField("End (date)", db_index=True)
    sample_size = models.PositiveIntegerField("Sample size", db_index=True)
    data_file = models.FileField("Data file", upload_to="transmission/%Y-%m-%d/")
    modulation = models.CharField("Modulation", max_length=255, default=get_default_modulation)
    media_class = models.CharField("Media class", max_length=255, default=get_default_media_class)
    accuracy = models.FloatField("Accuracy", default=0.0)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=get_default_group_id)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, default=get_default_device_id)
    source = models.CharField("Source", max_length=255)

    def duration(self):
        return timedelta(seconds=round((self.end_date - self.begin_date).total_seconds()))

    def middle_frequency(self):
        return self.begin_frequency + (self.end_frequency - self.begin_frequency) // 2

    def bandwidth(self):
        return self.end_frequency - self.begin_frequency

    @property
    def media_type(self):
        return get_media_type(self.modulation)


class GainTest(models.Model):
    name = models.CharField("Name", max_length=255)
    device_prefix = models.CharField("Device prefix", max_length=255)
    datetime = models.DateTimeField(auto_now_add=True)


class AppSetting(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.key}={self.value}"
