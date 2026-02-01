import astropy.nddata
import datetime
import io
import json
import math
import numpy as np
import os
import struct
import subprocess
import wave


def convert_uint8_to_float32_stream(file_path: str, chunk_size: int = 16 * 1024 * 1024):
    with open(file_path, "rb") as src:
        while True:
            chunk = src.read(chunk_size)
            if not chunk:
                break
            arr = np.frombuffer(chunk, dtype=np.uint8)
            norm = (arr.astype(np.float32) - 127.5) / 127.5
            yield norm.astype(np.float32).tobytes()


def wav_header_from_cu8_pcm16(path, sample_rate):
    num_audio_frames = os.path.getsize(path) // 2
    header_buffer = io.BytesIO()
    with wave.open(header_buffer, "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.setnframes(num_audio_frames)

    data_length = num_audio_frames * 2 * 2
    data = bytearray(header_buffer.getvalue())
    data[4:8] = struct.pack("<i", 36 + data_length)
    data[40:44] = struct.pack("<i", data_length)
    return bytes(data)


def wav_stream_from_cu8_pcm16(path, sample_rate, chunk_size=16 * 1024 * 1024):
    header = wav_header_from_cu8_pcm16(path, sample_rate)
    yield header

    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            arr = np.frombuffer(chunk, dtype=np.uint8)
            arr = arr[: (len(arr) // 2) * 2]

            I = arr[0::2].astype(np.float32)
            Q = arr[1::2].astype(np.float32)
            I = ((I - 128.0) * 256.0).astype(np.int16)
            Q = ((Q - 128.0) * 256.0).astype(np.int16)
            inter = np.empty(I.size * 2, dtype=np.int16)
            inter[0::2] = I
            inter[1::2] = Q

            yield inter.tobytes()


def make_spectrogram(data, sample_rate):
    factor = max(1, int(math.sqrt(sample_rate // 20000)))
    scale = factor + 1
    fft = 2 ** (10 + factor)
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


def truncate(in_file, sample_rate, duration):
    return ["dd", "if=%s" % in_file, "bs=%d" % (sample_rate * 2), "count=%d" % duration.total_seconds(), "iflag=fullblock"]


def pipeline(commands):
    last_process = None
    last_stdout = None

    for command in commands:
        process = subprocess.Popen(command, stdin=last_stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if last_stdout:
            last_stdout.close()
        last_stdout = process.stdout
        last_process = process
    return last_process


def decode_audio(in_file, format, modulation, sample_rate=32000, out_rate=32000, duration=datetime.timedelta(hours=2)):
    if modulation == "FM":
        if 75000 <= sample_rate:
            decoder = "sdr/decoders/wbfm.lua"
        else:
            decoder = "sdr/decoders/nbfm.lua"
    elif modulation == "AM":
        decoder = "sdr/decoders/am.lua"
    else:
        return

    if format in ["mp3", "wav"]:
        return pipeline(
            [
                truncate(in_file, sample_rate, duration),
                [decoder, "-r", str(sample_rate), str(out_rate), "-f", "s16le"],
                ["sox", "-t", "raw", "-r", str(out_rate), "-e", "signed", "-b", "16", "-c", "1", "-", "-t", format, "-"],
            ]
        )
    else:
        return pipeline(
            [
                truncate(in_file, sample_rate, duration),
                [decoder, "-r", str(sample_rate), str(out_rate), "-f", format],
            ]
        )


def decode_txt(in_file, format, modulation, sample_rate, duration=datetime.timedelta(hours=2)):
    if modulation == "AFSK 1200":
        return pipeline(
            [
                truncate(in_file, sample_rate, duration),
                ["sdr/decoders/afsk.lua", "-r", str(sample_rate), "-b", "1200", "-f", format],
                ["jq", "-r", '[.addresses[].callsign, .payload] | join(" | ")'],
            ],
        )
