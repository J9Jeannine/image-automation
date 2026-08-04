# Sheet-Rückschreiben — SOP (verbindlich bei JEDEM Lauf)

Diese Datei ist die vollständige Anleitung für den letzten Schritt jedes Laufs: das
Zurückschreiben des Ergebnisses in das **Funnel Sheet**. Sie gilt für jede Session,
automatisch (Trigger) wie manuell.

> **Kurzfassung für eilige Leser:** Nachdem die Bilder im Drive-Tages-/Produktordner
> liegen, für **jede in diesem Lauf verarbeitete Zeile** vier Zellen setzen:
> **L = Lauf-Datum**, **N = `claude`**, **O = `=HYPERLINK("<Ordner-URL>";"<Produktname>")`**,
> **P = `in progress`**.
> Danach zurücklesen und im Abschlussbericht bestätigen.

---

## Warum es diese Datei gibt

Läufe haben die Bilder erzeugt und den Drive-Ordner angelegt — und dann aufgehört. Der
Ordnerlink und der Bearbeiter kamen nie im Sheet an, also musste das Team jedes fertige
Produkt im Chat suchen.

Die Fähigkeit war immer da: derselbe Service-Account, der die Bilder hochlädt, darf auch
Zellen schreiben. Es fehlte nur die **Anweisung**. Ein früherer Lauf hat es getan, aber
den Fakt nur in seiner eigenen Ergebnisdatei vermerkt
(`State/processed_comments.json` → `sheet_link_written`) — und die liest ein späterer Lauf
als *Daten*, nicht als *Auftrag*. Deshalb steht es jetzt hier, in der Anweisung.

---

## Die vier Zellen

Alle Angaben beziehen sich auf die Zeile des verarbeiteten Produkts im jeweiligen Tab
(`FI` oder `FRCA`).

### Spalte L — Datum („Date Completed")

Das **Datum des Laufs**, an dem die Bilder in den Drive-Ordner gelegt wurden.

```
4-8-2026
```

Die Spalte enthält **echte Datumswerte**, keinen Text: das Zahlenformat ist `d-m-yyyy`,
intern liegt eine Serienzahl (z. B. `46238` für den 04.08.2026). Mit
`valueInputOption: "USER_ENTERED"` und der Schreibweise `T-M-JJJJ` parst Sheets den Wert
korrekt als Datum und übernimmt automatisch das Format der Spalte.

Nach dem Schreiben **prüfen, dass wirklich ein Datum entstanden ist**: der Wert mit
`valueRenderOption=UNFORMATTED_VALUE` muss eine **Zahl** sein. Kommt der eingegebene
String zurück, wurde er als Text gespeichert — dann sortiert und filtert die Spalte nicht
mehr richtig und der Wert muss korrigiert werden.

### Spalte N — Bearbeiter

```
claude
```

Exakt so, **kleingeschrieben**. Es ist ein Dropdown; `Claude` oder `CLAUDE` sind keine
gültigen Werte.

### Spalte O — Link auf den Ergebnis-Ordner

```
=HYPERLINK("https://drive.google.com/drive/folders/<ORDNER-ID>";"<Produktname aus Spalte G>")
```

Zwei Dinge, die leicht schiefgehen:

- **Semikolon** als Argumenttrenner, nicht Komma. Das Sheet läuft in einer Locale, in der
  das Komma als Dezimaltrennzeichen gilt; mit Komma wirft die Formel einen Fehler.
- Der Anzeigetext ist der **Produktname aus Spalte G, verbatim** — also `IntimaFix` im
  FI-Tab und `IntimaFit` im FRCA-Tab, auch wenn sich die beiden Tabs widersprechen. Nicht
  eigenmächtig vereinheitlichen, sondern die Abweichung im Bericht melden.

### Spalte P — Status

```
in progress
```

Exakt so, **`in` kleingeschrieben**. Die gültigen Dropdown-Werte der Spalte sind:

| Gültige Werte in Spalte P |
|---|
| `Comment Added` |
| `Fixed` |
| `Ready` |
| `For proofreading` |
| `in progress` |
| `For checking` |
| `in correction ` (mit Leerzeichen am Ende) |

**Niemals `Ready` setzen.** Ein Lauf liefert praktisch nie alle Ads einer Zeile — mal sind
es 3, mal 8, selten die vollen 10. `Ready` bedeutet im Team „vollständig und abgenommen",
und diese Entscheidung trifft der Mensch, der die fehlenden Ads ergänzt. Der Lauf meldet
nur „ich habe geliefert, es ist in Arbeit" — das ist `in progress`.

---

## Wann geschrieben wird — und wann nicht

**Schreiben** für jede Zeile, die in *diesem* Lauf tatsächlich Bilder produziert hat und
deren Dateien im Drive-Ordner verifiziert liegen.

**Nicht anfassen:**

- **Blockierte Zeilen.** Konnten keine Ad-Bilder geladen werden (abgelaufene
  fbcdn-Links, nur `facebook.com/ads/library`-Permalinks), entsteht kein Ordner. Ein Link
  auf einen nicht existierenden oder leeren Ordner ist schlimmer als eine leere Zelle.
- **Zeilen mit einer anderen Person in Spalte N.** Steht dort z. B. `Jess Mark` oder
  `dens`, gehört die Zeile jemand anderem — nicht überschreiben.
- **Zeilen aus früheren Läufen**, die schon einen gültigen Link tragen. Nur schreiben, was
  dieser Lauf erzeugt hat.

Teil-Lieferungen (z. B. 3 von 6 Ads gerendert, Rest als Original übernommen oder bewusst
ausgelassen) **werden** geschrieben — genau dafür ist `in progress` da. Was gefehlt hat
und warum, gehört in die `ad_copy.md` im Ordner und in den Abschlussbericht.

---

## Technisch: wie geschrieben wird

Der Drive-MCP kann **keine Zellen** schreiben. Dafür die **Sheets API** mit demselben
Service-Account nutzen, der auch die Bilder hochlädt.

**Scope:** zusätzlich zu `https://www.googleapis.com/auth/drive` auch
`https://www.googleapis.com/auth/spreadsheets` in den JWT-Claim aufnehmen. Ein Token, das
nur den Drive-Scope trägt, bekommt bei `values:batchUpdate` einen 403.

Token minten wie in [`drive-upload-method.md`](drive-upload-method.md) Schritt 2
beschrieben (JWT RS256, Signatur per `openssl` — das `cryptography`-Python-Modul ist in
der Sandbox defekt), dann:

```bash
curl -s -X POST \
  "https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values:batchUpdate" \
  -H "Authorization: Bearer ${SA_TOKEN}" \
  -H "Content-Type: application/json" \
  --data @- <<'JSON'
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    { "range": "FI!L60", "values": [["4-8-2026"]] },
    { "range": "FI!N60", "values": [["claude"]] },
    { "range": "FI!O60", "values": [["=HYPERLINK(\"https://drive.google.com/drive/folders/1AUOcq...\";\"IntimaFix\")"]] },
    { "range": "FI!P60", "values": [["in progress"]] }
  ]
}
JSON
```

`valueInputOption` **muss** `USER_ENTERED` sein — mit `RAW` landet die Formel als
sichtbarer Text in der Zelle statt als Link.

## Verifizieren (Pflicht)

Nach dem Schreiben zurücklesen und beides prüfen:

```bash
# Formel-Ansicht: steht die HYPERLINK-Formel wirklich drin?
curl -s -H "Authorization: Bearer ${SA_TOKEN}" \
  "https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/FI%21L60%3AP60?valueRenderOption=FORMULA"

# Anzeige-Ansicht: wird der Produktname als Linktext angezeigt?
curl -s -H "Authorization: Bearer ${SA_TOKEN}" \
  "https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/FI%21L60%3AP60"

# Rohwert-Ansicht: ist das Datum in L eine ZAHL (Serienzahl) und kein Text?
curl -s -H "Authorization: Bearer ${SA_TOKEN}" \
  "https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/FI%21L60?valueRenderOption=UNFORMATTED_VALUE"
```

Erwartet: `L` = Lauf-Datum, in der Anzeige `4-8-2026` und im Rohwert eine Zahl (z. B.
`46238`); `N` = `claude`; `O` = HYPERLINK-Formel bzw. der Produktname in der Anzeige;
`P` = `in progress`. Weicht etwas ab, erneut schreiben — keine halb gesetzte Zeile stehen
lassen.

Zum Schluss in `State/processed_comments.json` die geschriebene Zelle als
`sheet_link_written` vermerken (z. B. `"FI!O60"`), damit ein späterer Lauf sieht, dass die
Zeile fertig zurückgemeldet wurde.

---

## Checkliste

- [ ] Bilder liegen als echte Dateien im Tages-/Produktordner und sind verifiziert
      (Größe + vollständige Dekodierung, siehe `drive-upload-SOP.md`)
- [ ] Spalte **L** = Lauf-Datum, als **Datum** gespeichert (Rohwert ist eine Zahl)
- [ ] Spalte **N** = `claude` (klein)
- [ ] Spalte **O** = `=HYPERLINK("<URL>";"<Produktname aus G>")` — **Semikolon**
- [ ] Spalte **P** = `in progress` (klein, **nie** `Ready`)
- [ ] Blockierte Zeilen und fremde Bearbeiter unangetastet
- [ ] Zellen zurückgelesen und bestätigt
- [ ] `sheet_link_written` im State vermerkt
- [ ] Im Abschlussbericht steht, welche Zellen gesetzt wurden
