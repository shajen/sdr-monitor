#!/usr/bin/env python3

from gnuradio import audio, analog, blocks, filter, gr
from gnuradio.fft import window
from gnuradio.filter import firdes, pfb
import itertools
import signal
import sys


class am_decoder(gr.top_block):
    def __init__(self, input, sample_rate=32000, audio_rate=32000, duration=60, output=blocks.null_sink(gr.sizeof_float * 1)):
        gr.top_block.__init__(self, "am decoder", catch_exceptions=True)

        _blocks = [
            blocks.file_source(gr.sizeof_char * 1, input, False, 0, 0),
            blocks.head(gr.sizeof_char * 1, (int(sample_rate * duration * 2))),
            blocks.add_const_bb(128),
            blocks.interleaved_char_to_complex(False, 1.0),
            filter.fir_filter_ccf(1, firdes.low_pass(1, sample_rate, 6000, 2000, window.WIN_HAMMING, 6.76)),
            analog.agc_cc(0.000625, 1.0, 1.0, 65536),
            analog.pll_carriertracking_cc(0.05, (-0.0654), 0.0654),
            analog.am_demod_cf(channel_rate=sample_rate, audio_decim=1, audio_pass=2000, audio_stop=5000),
            pfb.arb_resampler_fff((audio_rate / sample_rate), taps=None, flt_size=32, atten=100),
            blocks.multiply_const_ff(1),
            output,
        ]

        for b1, b2 in itertools.pairwise(_blocks):
            self.connect(b1, b2)


def main(file):
    tb = am_decoder(input=file, output=audio.sink(32000, "", True))

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()
    tb.wait()


if __name__ == "__main__":
    main(sys.argv[1])
