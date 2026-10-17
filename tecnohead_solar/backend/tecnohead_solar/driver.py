"""Read-only Deye microinverter driver through Solarman V5/TCP."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from pysolarmanv5 import PySolarmanV5

LOGGER = logging.getLogger("tecnohead_solar.driver")


@dataclass(slots=True)
class PVChannelReading:
    channel: int
    voltage_v: float | None
    current_a: float | None
    power_dc_w: float | None
    energy_today_kwh: float | None
    energy_total_kwh: float | None
    supported: bool
    quality: str


@dataclass(slots=True)
class CollectorReading:
    captured_at: datetime
    logger_serial: int
    power_ac_w: float | None
    energy_today_kwh: float | None
    energy_total_kwh: float | None
    frequency_hz: float | None
    temperature_c: float | None
    channels: list[PVChannelReading]
    raw_registers: list[int]
    protocol: str = "solarman_v5_tcp"

    def as_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["captured_at"] = self.captured_at.isoformat()
        return payload


def _u32_lw_hw(registers: list[int], offset: int) -> int:
    return (int(registers[offset + 1]) << 16) | int(registers[offset])


def _scaled_u16(registers: list[int], offset: int, scale: float) -> float | None:
    if offset >= len(registers):
        return None
    return round(int(registers[offset]) * scale, 4)


def _scaled_u32_lw_hw(registers: list[int], offset: int, scale: float) -> float | None:
    if offset + 1 >= len(registers):
        return None
    return round(_u32_lw_hw(registers, offset) * scale, 4)


def decode_micro_registers(registers: list[int], logger_serial: int) -> CollectorReading:
    """Decode registers 60..119 from the reviewed Deye micro profile.

    Register addresses are kept here instead of hidden behind zero defaults so
    unsupported or incomplete replies remain visibly unsupported.
    """

    captured_at = datetime.now(UTC)
    channels: list[PVChannelReading] = []
    for channel in range(1, 5):
        voltage_offset = 49 + (channel - 1) * 2  # register 109, 111, 113, 115
        current_offset = voltage_offset + 1
        day_offset = 5 + (channel - 1)  # register 65..68
        total_offset = 9 + (channel - 1) * 2  # register pairs 69/70..77/78
        voltage = _scaled_u16(registers, voltage_offset, 0.1)
        current = _scaled_u16(registers, current_offset, 0.1)
        power = round(voltage * current, 3) if voltage is not None and current is not None else None
        day_energy = _scaled_u16(registers, day_offset, 0.1)
        total_energy = _scaled_u32_lw_hw(registers, total_offset, 0.1)
        supported = voltage is not None and current is not None and day_energy is not None
        # A near-zero voltage/current pair is a valid observed idle/unoccupied
        # channel, not a fabricated zero metric.
        quality = "valid" if supported else "unsupported"
        channels.append(
            PVChannelReading(
                channel=channel,
                voltage_v=voltage,
                current_a=current,
                power_dc_w=power,
                energy_today_kwh=day_energy,
                energy_total_kwh=total_energy,
                supported=supported,
                quality=quality,
            )
        )
    return CollectorReading(
        captured_at=captured_at,
        logger_serial=logger_serial,
        power_ac_w=_scaled_u32_lw_hw(registers, 26, 0.1),  # registers 86/87
        energy_today_kwh=_scaled_u16(registers, 0, 0.1),  # register 60
        energy_total_kwh=_scaled_u32_lw_hw(registers, 3, 0.1),  # registers 63/64
        frequency_hz=_scaled_u16(registers, 19, 0.01),  # register 79
        temperature_c=None,  # not exposed consistently by this profile
        channels=channels,
        raw_registers=registers,
    )


def read_collector(
    *,
    address: str,
    logger_serial: int,
    port: int = 8899,
    slave_id: int = 1,
    timeout: float = 8,
) -> CollectorReading:
    """Perform one read-only request. No write-register method is called."""

    client = None
    try:
        client = PySolarmanV5(
            address,
            logger_serial,
            port=port,
            mb_slave_id=slave_id,
            socket_timeout=timeout,
            auto_reconnect=False,
        )
        # The Deye logger profile accepts holding-register function 3. Input
        # register function 4 is intentionally not used because these devices
        # return an acknowledge exception for it.
        registers = client.read_holding_registers(register_addr=60, quantity=60)
        return decode_micro_registers(registers, logger_serial)
    finally:
        if client is not None:
            try:
                client.disconnect()
            except Exception:  # pragma: no cover - cleanup best effort
                LOGGER.debug("Deye socket cleanup failed", exc_info=True)


async def read_collector_async(**kwargs: Any) -> CollectorReading:
    return await asyncio.to_thread(read_collector, **kwargs)
