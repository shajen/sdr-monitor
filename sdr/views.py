from common.helpers import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import F, Count
from django.db.models.functions import TruncSecond, TruncDate, Length
from django.shortcuts import render
from django.utils.timezone import localtime
from sdr.models import *
from sdr.signals import *
import common.utils.filters
import math
import monitor.settings
import numpy as np
import sdr.drawer
import uuid


def get_download_filename(name, id, extension, dt):
    return "%s%d_%s.%s" % (name, id, localtime(dt).strftime("%Y%m%d_%H%M%S"), extension)


def get_download_raw_iq_filename(name, id, frequency, sample_rate, dt):
    return "%s%d_%s_%d_%d_fc.raw" % (name, id, localtime(dt).strftime("%Y%m%d_%H%M%S"), frequency, sample_rate)


@login_required()
@permission_required("sdr.view_spectrogram", raise_exception=True)
def spectrograms(request):
    items = Spectrogram.objects.select_related("device").annotate(
        device_name=F("device__name"),
        datetime=F("begin_model_date"),
        date=TruncDate("begin_model_date"),
        samples=Length("labels") / 8,
        sample_rate=F("end_frequency") - F("begin_frequency"),
        frequency=F("begin_frequency") + (F("end_frequency") - F("begin_frequency")) / 2,
        duration=TruncSecond("end_real_date") - TruncSecond("begin_real_date"),
    )
    options_lists = common.utils.filters.get_options_lists(request, items, ["device_name"])
    items = common.utils.filters.filter(request, items)
    items = common.utils.filters.order_by(request, items, ["-datetime", "frequency", "device_name"])
    page_size = int(request.GET.get("page_size", "100"))
    items = Paginator(items, page_size).get_page(request.GET.get("page"))
    return render(request, "spectrograms.html", dict({"items": items}, **options_lists))


@login_required()
@permission_required("sdr.view_spectrogram", raise_exception=True)
def spectrogram(request, spectrogram_id):
    mode = request.GET.get("mode", "static")
    spectrogram = Spectrogram.objects.annotate(
        samples=Length("labels") / 8,
        sample_rate=F("end_frequency") - F("begin_frequency"),
        frequency=F("begin_frequency") + (F("end_frequency") - F("begin_frequency")) / 2,
        duration=TruncSecond("end_real_date") - TruncSecond("begin_real_date"),
    ).get(id=spectrogram_id)
    return render(request, "spectrogram.html", {"spectrogram": spectrogram, "mode": mode})


@login_required()
@permission_required("sdr.view_spectrogram", raise_exception=True)
def spectrogram_data(request, spectrogram_id):
    format = request.GET.get("format", "image")
    s = Spectrogram.objects.get(id=spectrogram_id)
    if format == "image":
        filename = "tmp_%s.jpg" % uuid.uuid4().hex
        y_labels = np.frombuffer(s.labels, dtype=np.uint64)
        y_size = y_labels.size
        x_size = s.data_file.file.size // y_size
        data = np.memmap(s.data_file.path, dtype=np.int8, mode="r", shape=(y_size, x_size))

        kwargs = {"draw_frequency": False, "draw_power": False, "draw_time": False, "draw_data": False}
        data_type = request.GET.get("data", "")
        if data_type == "left":
            kwargs["draw_time"] = True
        elif data_type == "top":
            kwargs["draw_power"] = True
            kwargs["draw_frequency"] = True
        elif data_type == "main":
            kwargs["draw_data"] = True
        else:
            kwargs = {}

        drawer = sdr.drawer.Drawer(frequency_labels_count=(s.end_frequency - s.begin_frequency) // 200000, **kwargs)
        drawer.draw_spectrogram(data, filename, x_size, y_size, s.begin_frequency, s.end_frequency, y_labels)
        return file_response(filename, get_download_filename("spectrogram", s.id, "jpg", s.begin_real_date))
    elif format == "raw":
        return file_response(s.data_file.path, get_download_filename("spectrogram", s.id, "raw", s.begin_real_date), False)


@login_required()
@permission_required("sdr.view_transmission", raise_exception=True)
def transmissions(request):
    items = (
        Transmission.objects.select_related("device")
        .select_related("group")
        .annotate(
            device_name=F("device__name"),
            group_name=F("group__name"),
            modulation=F("group__modulation"),
            datetime=F("begin_date"),
            duration=TruncSecond("end_date") - TruncSecond("begin_date"),
            frequency=F("begin_frequency") + (F("end_frequency") - F("begin_frequency")) / 2,
            class_name=F("audio_class__name"),
            class_subname=F("audio_class__subname"),
        )
    )
    options_lists = common.utils.filters.get_options_lists(request, items, ["device_name", "modulation", "group_name", "class_name"])
    items = common.utils.filters.filter(request, items)
    items = common.utils.filters.order_by(request, items, ["-datetime", "frequency"])
    page_size = int(request.GET.get("page_size", "100"))
    items = Paginator(items, page_size).get_page(request.GET.get("page"))
    return render(request, "transmissions.html", dict({"items": items}, **options_lists))


@login_required()
@permission_required("sdr.view_transmission", raise_exception=True)
def transmission(request, transmission_id):
    transmission = Transmission.objects.annotate(
        duration=TruncSecond("end_date") - TruncSecond("begin_date"),
        sample_rate=F("end_frequency") - F("begin_frequency"),
        frequency=F("begin_frequency") + (F("end_frequency") - F("begin_frequency")) / 2,
    ).get(id=transmission_id)
    return render(request, "transmission.html", {"transmission": transmission})


@login_required()
@permission_required("sdr.view_transmission", raise_exception=True)
def transmission_data(request, transmission_id):
    format = request.GET.get("format")
    t = Transmission.objects.get(id=transmission_id)
    data = np.memmap(t.data_file.path, dtype=np.uint8, mode="r")
    sample_rate = t.end_frequency - t.begin_frequency
    if format == "spectrogram":
        filename = get_download_filename("transmission", t.id, "jpg", t.begin_date)
        data = make_spectrogram(data, sample_rate)
        drawer = sdr.drawer.Drawer(frequency_labels_count=8, draw_time=False, draw_power=True, text_size=16, text_stroke=2, min_width=1024)
        drawer.draw_spectrogram(data, filename, data.shape[1], data.shape[0], t.begin_frequency, t.end_frequency, list(range(data.shape[0])))
        return file_response(filename)
    elif format == "raw":
        filename = get_download_raw_iq_filename("transmission", t.id, t.middle_frequency(), sample_rate, t.begin_date)
        block_size = 10 * 2**10 * 2**10
        if os.path.exists(filename):
            os.remove(filename)
        for i in range(math.ceil(data.size / block_size)):
            with open(filename, "ab") as file:
                file.write(convert_uint8_to_float32(data[i * block_size : (i + 1) * block_size]).tobytes())
        return file_response(filename)
    elif t.group.modulation in ["FM", "AM"]:
        filename = get_download_filename("transmission", t.id, "mp3", t.begin_date)
        factor = t.sample_size
        (data, sample_rate) = decode(data[: factor * (t.data_file.size // factor)].reshape(-1, factor), sample_rate, t.group.modulation)
        save(data, sample_rate, filename)
        return file_response(filename)


@login_required()
@permission_required("sdr.change_group", raise_exception=True)
def groups(request, message_success="", message_error=""):
    items = Group.objects.annotate(bandwidth=F("end_frequency") - F("begin_frequency"), transmissions_count=Count("transmission"))
    options_lists = common.utils.filters.get_options_lists(request, items, ["name", "modulation"])
    items = common.utils.filters.filter(request, items)
    items = common.utils.filters.order_by(request, items, ["begin_frequency", "-bandwidth"])
    page_size = int(request.GET.get("page_size", "100"))
    items = Paginator(items, page_size).get_page(request.GET.get("page"))
    messages.success(request, message_success)
    messages.error(request, message_error)
    return render(request, "groups.html", dict({"items": items}, **options_lists))


@login_required()
@permission_required("sdr.change_group", raise_exception=True)
def update_groups(request):
    Transmission.objects.update(group_id=get_default_group_id())
    for group in sdr.models.Group.objects.annotate(bandwidth=F("end_frequency") - F("begin_frequency")).order_by("-bandwidth").all():
        Transmission.objects.annotate(frequency=(F("begin_frequency") + F("end_frequency")) / 2).filter(
            frequency__gte=group.begin_frequency, frequency__lte=group.end_frequency
        ).update(group_id=group.id)


@login_required()
@permission_required("sdr.change_group", raise_exception=True)
def add_group(request):
    try:
        name = request.GET["name"]
        begin_frequency = int(request.GET["begin_frequency"])
        end_frequency = int(request.GET["end_frequency"])
        modulation = request.GET["modulation"]
        Group.objects.get_or_create(name=name, begin_frequency=begin_frequency, end_frequency=end_frequency, modulation=modulation)
        update_groups(request)
        return groups(request, "Success!", "")
    except:
        return groups(request, "", "Error!")


@login_required()
@permission_required("sdr.change_group", raise_exception=True)
def delete_group(request, group_id):
    try:
        default_group_id = get_default_group_id()
        if int(group_id) == default_group_id:
            return groups(request, "", "Can not delete Default group!")
        else:
            Group.objects.get(id=group_id).transmission_set.update(group_id=default_group_id)
            Group.objects.filter(id=group_id).delete()
            update_groups(request)
            return groups(request, "Success!", "")
    except:
        return groups(request, "", "Error!")


@login_required()
@permission_required("sdr.change_device", raise_exception=True)
def config(request):
    return render(request, "config.html", {"mqtt": monitor.settings.MQTT})
