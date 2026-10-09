# Field mapping

Silver is the typed model. Bronze keeps source text. Gold is filled later and is not a source mapping.

`vehicle_id` is the plate for the GPS vendor and `TKNO` for logistics. The connected-vehicle sample has no plate, so a later load stores `''`. Event time is ISO-8601 with an offset, in UTC and in `Asia/Bangkok`. A source `Y`/`N` becomes `1`/`0`. A missing number becomes `NULL`. A bronze blank is `''`, not `NULL`, so the bronze unique key can match a rerun.

## GPS vendor

Source object fields land on `bronze.gps_vendor_report` under the same names (`Temp1` becomes `temp1`). Silver target is `silver.position_report` unless noted.

| Source field | Target column | Transform | Notes |
|---|---|---|---|
| registration | vehicle_id | text | Plate |
| local_timestamp | event_time_utc, event_time_bangkok | parse `YYYY-MM-DD HH:MM:SS` as `Asia/Bangkok` | No offset in the source |
| lat | latitude | REAL | |
| lon | longitude | REAL | |
| speed | speed_kmh | REAL | |
| course | heading_deg | INTEGER | |
| type_of_fix | gps_fix_code | INTEGER | |
| no_of_satellite | satellite_count | INTEGER | |
| internal_power | internal_power_mv | REAL | |
| external_power | external_power_mv | REAL | |
| mileage | mileage_km | REAL, null stays NULL | |
| fuel_sensor | fuel_sensor | REAL | |
| fuel_canbus | fuel_canbus | REAL | |
| driver_name | driver_name | text; `"-"` becomes NULL | |
| event_en | — | excluded | Not a position attribute. Bronze still keeps it |
| event_th | — | excluded | Same fact as `event_en` |
| location_th | — | excluded | Display text, not a coordinate |
| location_en | — | excluded | Display text, not a coordinate |
| temp1, temp2, temp3 | — | excluded | Sample values are `"-"` and no unit is defined |

`gps_signal_flag`, `engine_on_flag`, and `altitude_m` stay NULL for this source.

## Logistics fleet

Source columns land on `bronze.logistics_report` in snake_case. Silver target is `silver.position_report`.

| Source field | Target column | Transform | Notes |
|---|---|---|---|
| TKNO | vehicle_id | text | Not a plate |
| IMEI | — | excluded from silver | Device id. Bronze keeps `imei` |
| GPS_TIME | event_time_utc, event_time_bangkok | parse `YYYY-MM-DD HH:MM:SS` as `Asia/Bangkok` | |
| LATITUDE | latitude | REAL | |
| LONGITUDE | longitude | REAL | |
| SPEED | speed_kmh | REAL | |
| DIRECTION | heading_deg | INTEGER | |
| GPS_STATUS | gps_signal_flag | `Y` to 1, `N` to 0 | |
| ENGINE_STATUS | engine_on_flag | `Y` to 1, `N` to 0 | |
| ALTITUDE | altitude_m | REAL | |

Fuel, mileage, power, satellite count, fix code, and driver name stay NULL for this source.

## Connected vehicle

Each packet is one `bronze.connected_packet` row. `packet_type` is `0x51` or `0x52`. `payload` is the raw JSON text.

The periodic packet uses `B2B Event List`. The engine-on packet uses `B2B event`. Both become `silver.b2b_event`. The contained-data list, nested under `Engine RPM information` on the periodic packet, becomes `silver.signal_row`. The engine-on packet has no contained-data list.

A position report is also written from the common-header GPS so this feed can answer a cross-fleet speed question. `vehicle_id` is `''` on this sample.

| Source field | Target column | Transform | Notes |
|---|---|---|---|
| Common header GPS lat, lon | position_report.latitude, longitude | REAL | |
| Common header GPS timestamp | position_report event times | parse `YYYYMMDDHHMMSS` as `Asia/Bangkok` | |
| Common header GPS direction | position_report.heading_deg | INTEGER | |
| B2B event type | b2b_event.event_type | INTEGER | 30 heartbeat, 33 engine ON, 34 engine OFF |
| B2B timestamp, lat, lon | b2b_event event times and coordinates | same clock parse | Identity of the event |
| B2B vehicle speed | b2b_event.speed_kmh | REAL | Also copied to the position report when that is the latest fix |
| B2B engine RPM by direct line | b2b_event.engine_rpm | REAL | |
| Contained-data CAN signal | signal_row.signal_name, signal_value, signal_timestamp | one row per signal; timestamp parsed as `Asia/Bangkok` | |
| `+B Voltage Value` under `WNG` | signal_row | same as a CAN signal | Not dropped because the key is `WNG` |
| Engine RPM List | — | excluded | 60 values, no timestamp of their own |
| Vehicle speed List | — | excluded | 60 values, no timestamp of their own |
| Licence card | — | excluded | Empty in this sample. Not a vehicle id |
| Number of unsent message | — | excluded | Transport counter, not a position attribute |

## Excluded on purpose

- GPS vendor display text and the three temperature channels.
- Logistics `IMEI` on silver. It is not the vehicle id.
- Connected-vehicle parallel lists, the empty licence card, and the unsent-message counter.
- No shared vehicle id is invented. `gold.cross_source_pair` can stay empty for these samples.
