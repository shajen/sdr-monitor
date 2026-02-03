#!/usr/local/bin/luaradio

local argparse = require "argparse"
local radio = require("radio")

local parser = argparse()
parser:option("-i --input"):args(1):default(io.stdin)
parser:option("-o --output"):args(1):default(io.stdout)
parser:option("-r --rate"):args(2):default({"32000", "16000"}):convert(tonumber)
parser:option("-f --format"):choices({"s16le", "f32le", "wav", "port_audio", "pulse_audio"}):default("pulse_audio")
local args = parser:parse()

local function gcd(a, b)
    return b == 0 and a or gcd(b, a % b)
end

local input_rate = args.rate[1]
local output_rate = args.rate[2]
local factor = gcd(input_rate, output_rate)

local source = radio.IQFileSource(args.input, "u8", input_rate)
local am_demod = radio.ComplexMagnitudeBlock()
local dcr_filter = radio.SinglepoleHighpassFilterBlock(100)
local af_filter = radio.LowpassFilterBlock(128, 5000)
local af_gain = radio.AGCBlock("slow", -20)
local resampler = radio.RationalResamplerBlock(output_rate / factor, input_rate / factor)
local sink = (args.format == "wav" and radio.WAVFileSink(args.output, 1)) or (args.format == "port_audio" and radio.PortAudioSink(1)) or
                 (args.format == "pulse_audio" and radio.PulseAudioSink(1)) or radio.RealFileSink(args.output, args.format)

local top = radio.CompositeBlock()
top:connect(source, am_demod, dcr_filter, af_filter, af_gain, resampler, sink)
top:run()
