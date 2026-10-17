# Third-party notices

TecnoHead Solar ships its dependencies inside the published image at build time. It never downloads code at runtime.

| Component | Version | License | Use |
| --- | --- | --- | --- |
| Home Assistant base-debian | `trixie` | Apache-2.0 and bundled notices | S6 overlay, Bashio, runtime base |
| FastAPI | `0.143.3` | MIT | Local web/API server |
| Uvicorn | `0.54.0` | BSD-3-Clause | ASGI server |
| httpx | `0.28.1` | BSD-3-Clause | Optional API sync and health checks |
| psycopg | `3.3.6` | LGPL-3.0-only | PostgreSQL client |
| psycopg-pool | `3.3.3` | LGPL-3.0-only | Connection pooling |
| pysolarmanv5 | `3.0.6` | MIT | Solarman V5 frame transport; used read-only |
| umodbus | `1.0.4` | MIT | Modbus RTU frame encoding used by pysolarmanv5 |
| pyserial | `3.5` | BSD-3-Clause | Transitive dependency of umodbus |
| aiomqtt | `2.5.1` | MIT | Optional MQTT Discovery publisher |
| pydantic | `2.14.1` | MIT | Request/response validation |
| python-multipart | `0.0.32` | Apache-2.0 | Multipart support for the HTTP stack |
| reportlab | `5.0.1` | BSD-3-Clause | Local PDF reports |

The driver uses the Deye micro register map as an independently implemented profile. The public references used for protocol and compatibility research are documented in the repository README and architecture manual. No source file from those projects is vendored here.
