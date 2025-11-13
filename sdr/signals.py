from gnuradio import blocks
import astropy.nddata
import numpy as np
import sdr.decoders.am_decoder
import sdr.decoders.fm_decoder
import sdr.decoders.wfm_decoder


def convert_uint8_to_float32(data):
    return (data.astype(np.float32) - 127.5) / 127.5


def make_spectrogram(data, sample_rate):
    scale = 2
    fft = 2**11
    out = np.zeros(shape=(data.size // fft // scale // 2, fft // scale), dtype=np.int8)
    window = np.concatenate((np.hanning(fft // 2), np.zeros(fft // 2))).astype(np.float32)
    window = np.repeat([window], scale, axis=0).astype(np.float32)
    block_size = 2 * fft * scale
    for i in range(data.size // block_size):
        tmp = data[i * block_size : (i + 1) * block_size].astype(np.float32)
        tmp = ((tmp - 127.5) / 127.5).reshape(-1, 2)
        tmp = (tmp[:, 0] + tmp[:, 1] * 1j).reshape(-1, fft)
        tmp = np.fft.fft(tmp * window).astype(np.complex64)
        tmp = np.absolute(tmp**2.0) / np.float32(sample_rate)
        tmp = np.fft.fftshift(10.0 * np.log10(tmp), axes=(1,))
        tmp = astropy.nddata.block_reduce(tmp, scale, func=np.mean)
        out[i] = tmp.astype(np.int8)
    return out


def decode_audio(in_file, out_file, modulation, sample_rate, out_rate=32000):
    out_rate = min(sample_rate, out_rate)
    if modulation == "FM":
        if 75000 <= sample_rate:
            decoder = sdr.decoders.wfm_decoder.wfm_decoder(in_file, sample_rate, out_rate)
        else:
            decoder = sdr.decoders.fm_decoder.fm_decoder(in_file, sample_rate, out_rate)
    elif modulation == "AM":
        decoder = sdr.decoders.am_decoder.am_decoder(in_file, sample_rate, out_rate)
    else:
        return []

    if out_file:
        wav_block = blocks.wavfile_sink(out_file, 1, out_rate, blocks.FORMAT_WAV, blocks.FORMAT_PCM_16, False)
        decoder.connect((decoder.blocks_multiply_const_vxx_0, 0), (wav_block, 0))
        decoder.run()
    else:
        vector_block = blocks.vector_sink_f(1, 1024)
        decoder.connect((decoder.blocks_multiply_const_vxx_0, 0), (vector_block, 0))
        decoder.run()
        return vector_block.data()
