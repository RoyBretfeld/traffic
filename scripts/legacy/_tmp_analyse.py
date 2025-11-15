import requests
from collections import Counter, defaultdict

url = 'http://localhost:8111/api/tourplan/match'
params = {'file': './data/staging/1761782114_Tourenplan_04.09.2025.csv'}
res = requests.get(url, params=params)
res.raise_for_status()
data = res.json()
print('rows', data['rows'], 'ok', data['ok'], 'warn', data['warn'], 'bad', data['bad'])
status_counts = Counter()
issue_samples = defaultdict(list)
for item in data['items']:
    status = item.get('status')
    status_counts[status] += 1
    markers = tuple(item.get('markers') or ['(none)'])
    if status != 'ok' and len(issue_samples[markers]) < 5:
        issue_samples[markers].append({
            'row': item.get('row'),
            'name': item.get('display_name'),
            'address': item.get('resolved_address'),
            'markers': item.get('markers'),
            'geo_source': item.get('geo_source'),
            'lat': item.get('lat'),
            'lon': item.get('lon'),
            'manual_needed': item.get('manual_needed'),
            'alias_of': item.get('alias_of')
        })

print('status_counts', status_counts)
print('\nIssue categories:')
for markers, samples in issue_samples.items():
    marker_str = repr(markers).encode('ascii', 'replace').decode()
    print('\nMarkers:', marker_str)
    for s in samples:
        print(' ', {k: (str(v).encode('ascii', 'replace').decode() if isinstance(v, str) else v) for k, v in s.items()})
