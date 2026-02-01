local radio = require('radio')

if #arg < 3 then
    io.stderr:write("Usage: " .. arg[0] .. " <input IQ file> <input bandwidth> <output bandwidth> [<output wav file>\n")
    os.exit(1)
end

local function gcd(a, b)
    return b == 0 and a or gcd(b, a % b)
end

local input_file = arg[1]
local input_bandwidth = tonumber(arg[2])
local output_bandwidth = tonumber(arg[3])
local output_file = arg[4]
local factor = gcd(input_bandwidth, output_bandwidth)

local source = radio.IQFileSource(input_file, 'u8', input_bandwidth)
local am_demod = radio.ComplexMagnitudeBlock()
local dcr_filter = radio.SinglepoleHighpassFilterBlock(100)
local af_filter = radio.LowpassFilterBlock(128, 5000)
local af_gain = radio.AGCBlock('slow', -20)
local resampler = radio.RationalResamplerBlock(output_bandwidth / factor, input_bandwidth / factor)
local sink = output_file and radio.WAVFileSink(output_file, 1) or radio.RealFileSink(1, 'f32le')

local top = radio.CompositeBlock()
top:connect(source, am_demod, dcr_filter, af_filter, af_gain, resampler, sink)
top:run()
