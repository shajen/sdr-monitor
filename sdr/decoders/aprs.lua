local radio = require('radio')

if #arg < 2 then
    io.stderr:write("Usage: " .. arg[0] .. " <input IQ file> <input bandwidth>\n")
    os.exit(1)
end

local input_file = arg[1]
local input_bandwidth = tonumber(arg[2])

local baudrate = 1200

local source = radio.IQFileSource(input_file, 'u8', input_bandwidth)
local nbfm_demod = radio.NBFMDemodulator(3e3, 3e3)
local hilbert = radio.HilbertTransformBlock(129)
local translator = radio.FrequencyTranslatorBlock(-1700)
local afsk_filter = radio.LowpassFilterBlock(128, 750)
local afsk_demod = radio.FrequencyDiscriminatorBlock(1.25)
local data_filter = radio.LowpassFilterBlock(128, baudrate)
local clock_recoverer = radio.ZeroCrossingClockRecoveryBlock(baudrate)
local sampler = radio.SamplerBlock()
local bit_slicer = radio.SlicerBlock()
local bit_decoder = radio.DifferentialDecoderBlock(true)
local framer = radio.AX25FramerBlock()
local sink = radio.JSONSink(io.stdout)

local top = radio.CompositeBlock()
top:connect(source, nbfm_demod, hilbert, translator, afsk_filter, afsk_demod, data_filter, clock_recoverer)
top:connect(data_filter, 'out', sampler, 'data')
top:connect(clock_recoverer, 'out', sampler, 'clock')
top:connect(sampler, bit_slicer, bit_decoder, framer, sink)
top:run()
