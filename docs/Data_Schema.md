<!-- START: VJUMI-DATA-SCHEMA -->
## Tabelle: vehicle_positions
| Feld            | Typ        | Pflicht | Beschreibung                              |
|-----------------|------------|---------|--------------------------------------------|
| id              | uuid       | ja      | Primärschlüssel                             |
| transponder_id  | text       | ja      | Eindeutige Vjumi-Kennung                    |
| last_ping       | timestamptz| ja      | Zeitstempel der letzten Meldung             |
| latitude        | double     | ja      | Breitengrad                                 |
| longitude       | double     | ja      | Längengrad                                  |
| speed_kmh       | double     | nein    | Geschwindigkeit in km/h                     |
| status          | text enum  | ja      | `on_route` \| `stopped` \| `idle` \| `offline` |
| meta            | jsonb      | nein    | Roh-/Zusatzdaten                            |
| created_at      | timestamptz| ja      | Insertzeit                                  |
| updated_at      | timestamptz| ja      | Updatezeit                                  |

**Indizes:**  
- `idx_vehicle_positions_transponder_time (transponder_id, last_ping desc)`
- `gist` Geografie-Index optional (PostGIS) für Geofunktionen.
<!-- END: VJUMI-DATA-SCHEMA -->
