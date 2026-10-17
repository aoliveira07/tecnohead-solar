"""Report rendering kept local to the App."""

from __future__ import annotations

import io
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def pdf_report(rows: list[dict[str, Any]], title: str = "TecnoHead Solar") -> bytes:
    output = io.BytesIO()
    document = canvas.Canvas(output, pagesize=A4)
    _width, height = A4
    y = height - 48
    document.setTitle(title)
    document.setFont("Helvetica-Bold", 16)
    document.drawString(40, y, title)
    y -= 24
    document.setFont("Helvetica", 9)
    document.drawString(40, y, "Relatório local — fonte e período devem ser conferidos no painel.")
    y -= 24
    headers = ["Horário", "Coletor", "PV", "AC W", "DC W", "Hoje kWh", "Qualidade"]
    document.setFont("Helvetica-Bold", 8)
    document.drawString(40, y, " | ".join(headers))
    y -= 14
    document.setFont("Helvetica", 7)
    for row in rows[:120]:
        values = [
            str(row.get("captured_at", ""))[:19],
            str(row.get("collector_name", ""))[:18],
            str(row.get("pv_name", "AC"))[:12],
            str(row.get("power_ac_w", "—"))[:9],
            str(row.get("power_dc_w", "—"))[:9],
            str(row.get("energy_today_kwh", "—"))[:10],
            str(row.get("quality", ""))[:12],
        ]
        document.drawString(40, y, " | ".join(values))
        y -= 11
        if y < 42:
            document.showPage()
            y = height - 48
            document.setFont("Helvetica", 7)
    document.save()
    return output.getvalue()
