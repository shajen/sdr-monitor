#!/usr/local/bin/luaradio

local argparse = require "argparse"
local radio = require("radio")

local parser = argparse()
parser:option("-i --input"):args(1):default(io.stdin)
parser:option("-o --output"):args(1):default(io.stdout)
parser:option("-r --rate"):args(1):default("32000"):convert(tonumber)
parser:option("-b --baud_rate"):args(1):default("1200"):convert(tonumber)
parser:option("-f --format"):choices({"raw", "json"}):default("json")
local args = parser:parse()

local function gcd(a, b)
    return b == 0 and a or gcd(b, a % b)
end

local input_rate = args.rate
local baud_rate = args.baud_rate

local source = radio.IQFileSource(args.input, "u8", input_rate)
local filter = radio.LowpassFilterBlock(128, 12500)
local nbfm_demod = radio.NBFMDemodulator(3e3, 3e3)
local hilbert = radio.HilbertTransformBlock(129)
local translator = radio.FrequencyTranslatorBlock(-1700)
local afsk_filter = radio.LowpassFilterBlock(128, 750)
local afsk_demod = radio.FrequencyDiscriminatorBlock(1.25)
local data_filter = radio.LowpassFilterBlock(128, baud_rate)
local clock_recoverer = radio.ZeroCrossingClockRecoveryBlock(baud_rate)
local sampler = radio.SamplerBlock()
local bit_slicer = radio.SlicerBlock()
local bit_decoder = radio.DifferentialDecoderBlock(true)
local framer = radio.AX25FramerBlock()
local sink = (args.format == "raw" and radio.RawFileSink(args.output, "f32le")) or (args.format == "json" and radio.JSONSink(args.output, 1))

local top = radio.CompositeBlock()
top:connect(source, filter, nbfm_demod, hilbert, translator, afsk_filter, afsk_demod, data_filter, clock_recoverer)
top:connect(data_filter, "out", sampler, "data")
top:connect(clock_recoverer, "out", sampler, "clock")
top:connect(sampler, bit_slicer, bit_decoder, framer, sink)
top:run()
