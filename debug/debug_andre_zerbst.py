#!/usr/bin/env python3
"""
Debug: Warum wird André Zerbst als Mojibake erkannt?
"""

def debug_andre_zerbst():
    """Debug André Zerbst."""
    
    name = 'André Zerbst'
    mojibake_chars = ['┬', '├', 'á', '@', ']', 'é']
    
    print("🔍 Debug: André Zerbst")
    print("=" * 30)
    print(f"Name: {repr(name)}")
    print(f"Länge: {len(name)}")
    
    print("\nMojibake-Check:")
    for char in mojibake_chars:
        found = char in name
        print(f"  {repr(char)} in Name: {found}")
        if found:
            print(f"    Position: {name.find(char)}")
    
    print("\nZeichen-für-Zeichen:")
    for i, char in enumerate(name):
        print(f"  Position {i}: {repr(char)} (U+{ord(char):04X})")
    
    # Das Problem: 'é' ist in der Mojibake-Liste!
    print(f"\nDas Problem: 'é' ist in der Mojibake-Liste!")
    print(f"Aber 'é' ist ein GÜLTIGES Zeichen (é mit Akzent)")
    print(f"Das ist KEIN Mojibake!")

if __name__ == "__main__":
    debug_andre_zerbst()
