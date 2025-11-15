/**
 * Minimaler Polyline6-Decoder (OSRM: geometries=polyline6)
 * Rückgabe: Array von [lat, lon]
 */
export function decodePolyline6(str) {
    if (!str || typeof str !== "string") return [];
    
    let index = 0, lat = 0, lon = 0, coords = [];
    const shift = 5; // wie Polyline5, aber Skalierung anders
    
    const next = () => {
        let result = 0, b, i = 0;
        do {
            if (index >= str.length) return null;
            b = str.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << (i * shift);
            i++;
        } while (b >= 0x20);
        return (result & 1) ? ~(result >> 1) : (result >> 1);
    };
    
    while (index < str.length) {
        const dlat = next();
        const dlon = next();
        if (dlat === null || dlon === null) break;
        lat += dlat;
        lon += dlon;
        // Polyline6 skaliert mit 1e6
        coords.push([lat / 1e6, lon / 1e6]);
    }
    
    return coords;
}

/**
 * Konvertiert Polyline6 zu GeoJSON LineString
 */
export function polyline6ToGeoJSON(str) {
    const coords = decodePolyline6(str).map(([la, lo]) => [lo, la]);
    return { type: "LineString", coordinates: coords };
}

