// Frontend Helper-Funktion um "nan, nan nan" Adressen zu verhindern
export function prettyAddress(street, zip, city) {
  return [street, zip, city]
    .map(v => (v ?? '').toString().trim())
    .filter(v => v && v.toLowerCase() !== 'nan')
    .join(', ');
}

// Alternative: Einzeiler für direkte Verwendung
export const buildAddress = (street, zip, city) => 
  [street, zip, city]
    .map(v => (v ?? '').toString().trim())
    .filter(v => v && v.toLowerCase() !== 'nan')
    .join(', ');

// React/JSX Beispiel:
// <td>{prettyAddress(c.street, c.zip, c.city) || '—'}</td>

// Angular Template Beispiel:
// <td>{{ prettyAddress(c.street, c.zip, c.city) || '—' }}</td>
