from repositories.geo_repo import get_address_variants

# Teste das neue System mit Firmennamen
address = 'Rundteil 7b, 01728 Bannewitz OT Possendorf'
company = 'Klassische Automobile Schwarz'

print('🔍 Teste neue Firmennamen-Unterstützung:')
print(f'Adresse: {address}')
print(f'Firma: {company}')
print()

variants = get_address_variants(address, company)
print(f'📋 Generierte Varianten ({len(variants)}):')
for i, variant in enumerate(variants, 1):
    print(f'  {i}. {variant}')

print()
print('🎯 Das bedeutet:')
print('- Nominatim kann jetzt nach "Klassische Automobile Schwarz" suchen')
print('- Das ist viel einfacher zu finden als "Rundteil 7b, 01728 Bannewitz OT Possendorf"')
print('- Kombination aus Firmenname + Adresse erhöht Erfolgsrate erheblich!')
