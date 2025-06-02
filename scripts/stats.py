from collections import defaultdict
from sdr.models import *
import sdr.templatetags.sdr_filters


def run(*args):
    counter = defaultdict(int)
    for t in Transmission.objects.all():
        frequency = (t.begin_frequency + t.end_frequency) // 2
        counter[frequency] += 1
    for count, frequency in sorted(((v, k) for k, v in counter.items()), reverse=True):
        print("%s - %d" % (sdr.templatetags.sdr_filters.frequency(frequency), count))
