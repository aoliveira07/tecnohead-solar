from tecnohead_solar.driver import decode_micro_registers


def put_u32(registers: list[int], offset: int, value: int) -> None:
    registers[offset] = value & 0xFFFF
    registers[offset + 1] = (value >> 16) & 0xFFFF


def test_decode_micro_profile_registers_without_network() -> None:
    registers = [0] * 60
    registers[0] = 37
    put_u32(registers, 3, 123456)
    registers[19] = 6000
    put_u32(registers, 26, 19875)
    for channel in range(4):
        registers[5 + channel] = 8 + channel
        put_u32(registers, 9 + channel * 2, 9000 + channel * 100)
        registers[49 + channel * 2] = 320 + channel
        registers[50 + channel * 2] = 150 + channel

    result = decode_micro_registers(registers, 123456789)

    assert result.energy_today_kwh == 3.7
    assert result.energy_total_kwh == 12345.6
    assert result.power_ac_w == 1987.5
    assert result.frequency_hz == 60
    assert result.channels[0].voltage_v == 32.0
    assert result.channels[0].current_a == 15.0
    assert result.channels[0].power_dc_w == 480.0
    assert all(channel.supported for channel in result.channels)


def test_decode_short_reply_marks_channels_unsupported() -> None:
    result = decode_micro_registers([0] * 10, 123)

    assert result.power_ac_w is None
    assert all(not channel.supported for channel in result.channels)

