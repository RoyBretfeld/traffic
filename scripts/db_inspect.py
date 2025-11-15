from __future__ import annotations

import sqlite3
from pathlib import Path


def main() -> None:
    db = Path("data/traffic.db")
    if not db.exists():
        print("DB nicht gefunden:", db)
        return
    con = sqlite3.connect(db)
    cur = con.cursor()
    kunden_count = cur.execute("select count(*) from kunden").fetchone()[0]
    touren_count = cur.execute("select count(*) from touren").fetchone()[0]
    beispiele = cur.execute("select id,name,adresse from kunden limit 5").fetchall()
    print("DB:", db.resolve())
    print("kunden:", kunden_count)
    print("touren:", touren_count)
    print("beispiele:", beispiele)


if __name__ == "__main__":
    main()
