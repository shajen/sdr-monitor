from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.utils import timezone
from django.utils.timezone import make_aware
from humanize import naturalsize
from sdr.models import *
import base64
import json
import logging
import re
import sdr.utils.device
import sdr.utils.file


class TransmissionReader:
    def __init__(self):
        self.__logger = logging.getLogger("Transmission")
        self.__regex = re.compile("sdr/transmission/\\w+/([\\w\\.]+)")

    def get_device(self, name):
        try:
            return Device.objects.get(raw_name=name)
        except ObjectDoesNotExist:
            return Device.objects.create(name=sdr.utils.device.convert_raw_to_name_to_pretty_name(name), raw_name=name)

    def append_transmission(self, device, dt, begin_frequency, end_frequency, samples, sample_size, sample_type, source, name):
        device = self.get_device(device)
        frequency = (begin_frequency + end_frequency) // 2
        try:
            group_id = (
                Group.objects.annotate(bandwidth=F("end_frequency") - F("begin_frequency"))
                .order_by("bandwidth")
                .filter(begin_frequency__lte=frequency, end_frequency__gte=frequency)[0]
                .id
            )
        except:
            group_id = get_default_group_id()
        try:
            t = Transmission.objects.get(
                device=device,
                begin_frequency=begin_frequency,
                end_frequency=end_frequency,
                end_date__gt=dt - timezone.timedelta(seconds=1),
                end_date__lt=dt,
                sample_size=sample_size,
                data_type=sample_type,
                group_id=group_id,
                source=source,
                name=name,
            )
            t.end_date = dt
        except Transmission.DoesNotExist:
            dir = "device_%d/transmission" % device.id
            (filename, filename_full) = sdr.utils.file.get_filename(dir, dt, "%s_%d_%s.bin" % (dt.strftime("%H_%M_%S"), (begin_frequency + end_frequency) // 2, sample_type), True)
            t = Transmission.objects.create(
                device=device,
                begin_frequency=begin_frequency,
                end_frequency=end_frequency,
                begin_date=dt,
                end_date=dt,
                sample_size=sample_size,
                data_file=filename,
                data_type=sample_type,
                group_id=group_id,
                source=source,
                name=name,
            )
        self.__logger.debug("new size: %d = %d x %d, size: %s" % (len(samples), len(samples) / sample_size, sample_size, naturalsize(sample_size)))
        with open(t.data_file.path, "ab") as file:
            file.write(samples)
        t.end_date = dt
        t.save()

    def on_message(self, client, message):
        topic = message.topic
        m = self.__regex.match(topic)
        if m:
            device = m.group(1)
            message = json.loads(message.payload.decode("utf-8"))
            data = base64.b64decode(message["data"])
            source = message["source"]
            name = message["name"]
            frequency = message["frequency"]
            bandwidth = message["bandwidth"]
            begin_frequency = frequency - bandwidth // 2
            end_frequency = frequency + bandwidth // 2
            dt = make_aware(timezone.datetime.fromtimestamp(message["time"] / 1000))
            self.__logger.info(
                f"source: {source}, name: {name}, device: {device}, frequency: {frequency}, bandwidth: {bandwidth}, datetime: {dt}, data size: {naturalsize(len(data))}"
            )
            self.append_transmission(device, dt, begin_frequency, end_frequency, data, bandwidth, "uint8", source, name)
            return True
        return False
