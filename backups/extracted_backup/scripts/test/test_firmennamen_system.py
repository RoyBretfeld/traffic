from repositories.geo_repo import get_address_variants

# Teste das Firmennamen-System
address = 'Naumannstr. 12 / Halle 26F, 01809 Heidenau'
company = 'PM Car Parts'

print('🔍 Teste Firmennamen-System:')
print('Adresse:', address)
print('Firma:', company)
print()

variants = get_address_variants(address, company)
print('Generierte Varianten:')
for i, variant in enumerate(variants, 1):
    print(f'  {i}. {variant}')

print()
print('🎯 Das bedeutet:')
print('- Nominatim kann jetzt nach "PM Car Parts" suchen')
print('- Das ist viel einfacher zu finden als die Adresse')
print('- Kombination aus Firmenname + Adresse erhöht Erfolgsrate!')
