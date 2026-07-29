# Tagesplaner

Eine lokale, einzelne HTML-Datei – keine Installation nötig.

## Starten

Doppelklick auf `index.html` (öffnet im Standardbrowser). Alle Daten (Aufgaben, Haken, Startzeit) werden im Browser via `localStorage` gespeichert und bleiben beim nächsten Öffnen erhalten.

Alternativ, falls dein Browser lokale Dateien einschränkt:

```
cd planner
python3 -m http.server 8080
```

und dann `http://localhost:8080` öffnen.

## Wie es funktioniert

- **Zeitleiste**: fixe Blöcke für Frühstück, Mittag, Abendessen und Gym, dazwischen drei Arbeitsblöcke mit je 2–3 vorgeschlagenen Aufgaben (nicht alle auf einmal, um nicht zu überfordern).
- **Start Arbeit** (oben rechts): verschiebt alle Blöcke relativ zur gewählten Startzeit — z. B. für einen frühen Starttag einfach auf 06:00 stellen.
- **Alle offenen Aufgaben**: vollständiger Rückstand nach Kategorie, aufklappbar, dort auch neue Aufgaben hinzufügen (Titel, Kategorie, geschätzte Minuten, „wichtig“).
- **Heute erledigt**: abgehakte Aufgaben bleiben dauerhaft erledigt (kein täglicher Reset), bis du sie manuell wieder aktivierst.

## Daten zurücksetzen

In der Browser-Konsole: `localStorage.clear()` und Seite neu laden — dann werden die Ausgangsaufgaben neu geladen.
