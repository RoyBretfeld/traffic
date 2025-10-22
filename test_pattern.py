import re

# Test-Pattern
pattern = r'\s+OT\s+[A-Za-zäöüßÄÖÜ\s\-ü]+$'
test_addr = 'Dresdner Strasse 6, 01728 Bannewitz OT Hänichen'

print(f'Test-Adresse: {test_addr}')
print(f'Pattern: {pattern}')
print(f'Match: {re.search(pattern, test_addr, re.IGNORECASE)}')

# Einfacheres Pattern testen
simple_pattern = r'\s+OT\s+.+$'
print(f'Einfaches Pattern: {simple_pattern}')
print(f'Match: {re.search(simple_pattern, test_addr, re.IGNORECASE)}')

# Noch einfacheres Pattern
very_simple = r'OT\s+'
print(f'Sehr einfaches Pattern: {very_simple}')
print(f'Match: {re.search(very_simple, test_addr, re.IGNORECASE)}')
