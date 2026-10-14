# Sprachregeln für generierte Bilder (alle Märkte — aktuell FRCA / FI / NLBE / ZA)

**Status: blockierend.** Kein Bild wird generiert, bevor diese Regeln erfüllt sind, und
kein Bild wird hochgeladen, bevor Abschnitt 5 bestanden ist. Diese Regeln greifen **bei
der Erzeugung**, nicht als Nachbesserungsschleife. Ein Ablauf "generieren → prüfen →
neu generieren → prüfen" gilt als Fehler, nicht als Prozess.

**Diese Datei gilt sprachunabhängig.** Abschnitt 1a (echte Wörter, keine erfundenen
Komposita, keine falschen Endungen) und Abschnitt 2/3/5 gelten für **jede** Sprache —
für FRCA und FI genauso wie für jeden künftigen Markt, sobald für ihn nach Abschnitt 6
ein eigener Abschnitt 4.x angelegt wurde.

---

## 0. Warum es bisher schiefging

Das Bildmodell (Higgsfield / Nano Banana) bekam den Text der Quell-Anzeige mit und sollte
ihn beim Rendern selbst übersetzen. Das macht kein Bildmodell zuverlässig:

- es kopiert den Quelltext unverändert durch (beobachtet: bis zu 50 % eines 12er-Batches),
- besonders tückisch, wenn Quelle und Ziel "dieselbe Sprache" sind
  (Frankreich-Französisch → Québec-Französisch): der Text sieht plausibel aus und fällt
  ohne Wortliste nicht auf,
- und es erfindet Wörter, die nur aussehen wie echte Wörter — vor allem auf Verpackungen,
  Etiketten und Preisschildern, und vor allem im Finnischen.

Die Lösung ist nicht ein schärferer Hinweis im Prompt. Die Lösung ist, dem Bildmodell das
Übersetzen wegzunehmen.

---

## 1. LOCKED STRING — der Text steht vor dem Bild fest

Für jede Ad, vor dem ersten Higgsfield-Call:

1. Jeden sichtbaren Text der Ziel-Ad ausformulieren — Headline, Banner, Badge, Störer,
   Button/CTA, Preisschild, Verpackungsaufdruck, Kleingedrucktes. In der Zielsprache,
   fertig, endgültig.
2. Diese Strings als **LOCKED STRING** in `State/<product>_<market>_locked_strings.md`
   festhalten, mit einer Zeile pro Textelement, bevor gerendert wird.
3. Den LOCKED STRING wörtlich in den Higgsfield-Prompt einsetzen, in Anführungszeichen,
   gefolgt von genau diesem Block:

```
Render this text EXACTLY as written, character for character, including every accent
and special character. Do NOT translate it. Do NOT rephrase it. Do NOT correct it.
Do NOT add any other words, labels, packaging text, price tags, or background signage.
The image must contain no text other than the strings quoted above.
Ignore all text visible in the reference image.
```

Der LOCKED STRING wird von einer Textinstanz erzeugt (dieser Session / dem Skill
`image-ad-prompt-generator`), niemals vom Bildmodell.

## 1a. Nur echte, existierende Wörter — für JEDE Sprache, auch künftige

**Gilt uneingeschränkt für Finnisch, Québec-Französisch und jede weitere Sprache, die
später dazukommt — nicht nur für Märkte mit eigenem Abschnitt 4.x.**

Jedes einzelne Wort im LOCKED STRING muss ein echtes, belegtes Wort der Zielsprache sein
— kein Wort, das nur aussieht wie das Wort dieser Sprache. Das betrifft besonders:

- **Verpackungs- und Etikettentext, Preisschilder, Badges, Kleingedrucktes** — genau die
  Stellen, an denen kurze, auffällige Wörter stehen und ein falsches oder erfundenes Wort
  am meisten auffällt.
- **Komposita** (zusammengesetzte Wörter, z. B. im Finnischen): niemals mechanisch aus
  Einzelteilen zusammenbauen. Nur Komposita verwenden, die als Ganzes ein belegtes,
  gebräuchliches Wort sind.
- **Flexion/Kasus** (Endungen für Fall, Numerus, Zeit — z. B. finnischer Partitiv/Genitiv/
  Illativ, französische Verbformen): die Endung muss zur grammatischen Rolle im Satz
  passen, nicht nur "irgendeine plausible Endung" sein.
- **Diakritika/Sonderzeichen** (Akzente im Französischen, ä/ö im Finnischen, künftig
  weitere): müssen exakt zur Zielsprache passen, nicht nur ähnlich aussehen.

Wer den LOCKED STRING schreibt (diese Session, oder der Skill `image-ad-prompt-generator`)
ist dafür verantwortlich, dass jedes Wort geprüft echt ist — nicht nur plausibel klingt.
Im Zweifel: kürzeres, sicher bekanntes Wort statt eines selteneren, bei dem Unsicherheit
besteht, ob es das wirklich gibt.

Diese Regel ist unabhängig von Abschnitt 4 (Marktspezifikation). Ein neuer Markt hat sie
ab dem ersten Lauf, auch bevor jemand die marktspezifische Verbotsliste in Abschnitt 6
ergänzt hat.

## 2. Quelltext wird nie durchgereicht

Die Quell-Anzeige ist **ausschließlich** Referenz für Layout, Bildaufbau, Farbe,
Seitenverhältnis und Produktdarstellung. Kein Wort daraus geht in den Prompt — auch dann
nicht, wenn es schon "französisch" aussieht.

## 3. Textlänge

Maximal **6 Wörter pro Textelement** im Bild. Lange Strings sind genau die Stelle, an der
das Modell anfängt, Buchstaben und Wörter zu erfinden. Längere Claims gehören in die
Ad-Copy (Primary Text / Headline im Anzeigentext), nicht ins Bild.

---

## 4. Marktspezifikation

### 4.1 FRCA — Québec-Französisch

Ziel: natürliches Québec-Französisch, wie es in kanadischer Werbung geschrieben wird.
**Nicht** Frankreich-Französisch, nicht "neutrales" Französisch.

> **Diese Spezifikation gilt für JEDES Produkt und JEDE Kategorie** — Hautpflege,
> Nahrungsergänzung, Gelenke, Haushalt, Auto, Haustier, Werkzeug, Kleidung, und jede
> Kategorie, die später dazukommt. Die Tabellen unten sind **Beispiele des Prinzips,
> keine abschließenden Listen.** Ein Wort, das in keiner Tabelle steht, ist damit nicht
> erlaubt — es ist ungeprüft. Verbindlich ist der Test unter (A).

> **Warum Verbotslisten allein nie reichen:** Eine Liste kann nur prüfen, was sie kennt.
> Die ursprüngliche FRCA-Liste war eine reine Promo-Wortliste (SOLDES, courriel,
> week-end, parking). In einer Hautpflege-Ad kommt keins dieser Wörter vor — die Prüfung
> war deshalb immer bestanden und der Text trotzdem Frankreich-Französisch. Dasselbe
> passiert mit jeder Liste bei jedem neuen Produkt. **Der Test unter (A) ist die Regel,
> die Listen sind nur Abkürzungen für bekannte Fälle.**

**Zweistufig, verpflichtend:** erst den französischen Text schreiben, dann Zeile für
Zeile gegen (A) bis (E) durchgehen und neu schreiben. Erst die überarbeitete Fassung
wird LOCKED STRING.

#### (A) Der Test — gilt für jedes Wort, jedes Produkt, jede Kategorie

**Auf jeden Ausdruck im Text anwenden, bevor er LOCKED STRING wird:**

> Existiert dieser Ausdruck im Québec-Französisch für sich allein — in einem Satz, der
> mit diesem Produkt und mit der Quellsprache nichts zu tun hat? Würde eine Québécoise
> in dieser Situation genau das sagen?

Lässt sich ein Ausdruck nur damit begründen, dass er in der Quell-Ad stand oder dass er
"auf Französisch geht", ist er nicht geprüft. Neu schreiben mit einem Ausdruck, der im
Québec-Französisch eigenständig existiert.

**Registerdifferenz — der häufigste Grund, warum ein korrekter Text falsch klingt:**
Frankreich-Werbung ist abstrakt, lyrisch und gefühlsbeschreibend. Québec-Werbung ist
einfach, konkret und direkt. **Faustregel: sagt der Satz, was das Produkt TUT, oder
beschreibt er ein Gefühl? Québec sagt, was es tut.** Das gilt für Hautcreme genauso wie
für Hundefutter, Gelenkkapseln oder einen Staubsauger.

Beispiel Kosmetik — **Muster, keine vollständige Liste:**

| verboten (Frankreich-Werberegister) | erforderlich (Québec, schlicht) |
|---|---|
| sublimer, sublimateur | raffermir, raffermissant |
| repulper, repulpé | plus ferme, rebondi |
| geste beauté, rituel beauté, routine beauté | streichen — direkt sagen, was es tut |
| révéler l'éclat, coup d'éclat, éclat sublimé | peau plus lumineuse |
| une peau de rêve, peau divine, bonne mine | une peau ferme |
| booster, boosté | renforcer, renforcé |
| cocooning, peau nette | streichen |

Dasselbe Muster in anderen Kategorien: `une expérience unique` → sagen, was es kann ·
`révolutionne ton quotidien` → sagen, was es macht · `le secret des pros` → streichen.

#### (B) Anrede: immer `tu`, nie `vous` — produktunabhängig

Das Verb wird mitkonjugiert — nur das Pronomen zu tauschen ist ein Fehler.

| verboten | erforderlich |
|---|---|
| Vous / Votre / Vos (als Leseransprache) | Tu / Ton / Ta / Tes |
| Commandez / Découvrez / Profitez / Essayez / Achetez / Économisez | Commande / Découvre / Profite / Essaie / Achète / Économise |
| Dites adieu / Retrouvez / Redécouvrez / Oubliez | Dis adieu / Retrouve / Redécouvre / Oublie |
| votre peau, vos articulations, votre maison | ta peau, tes articulations, ta maison |

#### (C) Kategorie-Vokabular — VERPFLICHTENDER SCHRITT, nicht nur eine Liste

**Vor dem Schreiben, für jedes Produkt neu:** Produktkategorie bestimmen und deren
eigene Begriffe gegen die québecer Handelsüblichkeit prüfen — Produktbezeichnungen,
Körperteile, Symptome, Materialien, Werkzeuge, Geräte, Kleidung, Räume, Fahrzeuge,
Tiere. Existieren ein Frankreich-Wort und ein Québec-Wort, gilt das Wort, das auf
kanadischen Handelsseiten steht.

**Grundregel: Québec ist bei Anglizismen strenger als Frankreich.** Was in Paris normal
ist, wirkt in Montréal nachlässig. Im Zweifel das französische Wort.

Beispiele des Prinzips — **ausdrücklich keine abschließende Liste:**

| Kategorie | Frankreich / Anglizismus → Québec |
|---|---|
| Kosmetik / Hautpflege | spray → vaporisateur · lifting → effet raffermissant · peeling → exfoliation · patch → timbre · make-up → maquillage · waterproof → résistant à l'eau · glow → éclat · soin de la peau → soins de la peau · patte-d'oie → pattes-d'oie (immer Plural) |
| Gelenke / Körper | articulations · douleurs articulaires · genoux · hanches · dos |
| Zahnpflege | soins dentaires · prothèse dentaire · dentier · gencives |
| Haushalt / Geräte | washing machine → laveuse · dryer → sécheuse · vacuum → balayeuse |
| Kleidung | chaussures → souliers · socks → bas · pull → chandail |
| Auto | voiture (informell: char) · carburant → gaz · pneus d'hiver |
| Haus / Garten | basement → sous-sol · porch → galerie · Schneeräumen → déneigement |
| Haustier | nourriture pour chien / chat · vétérinaire · laisse · niche |
| Gesundheit allgemein | aux urgences → à l'urgence · Dr / Dre / Mme (ohne Punkt) |

Steht die Kategorie des Produkts nicht in dieser Tabelle, ist das **kein Freibrief** —
dann gilt (A) und der Prüfschritt oben. Neue Kategorien nach (G) ergänzen.

#### (D) Promo- und Shop-Vokabular — produktunabhängig

| verboten (Frankreich / neutral) | erforderlich (Québec) |
|---|---|
| SOLDES, SOLDES D'HIVER / D'ÉTÉ | VENTE, VENTE D'HIVER / D'ÉTÉ, RABAIS, AUBAINE, LIQUIDATION |
| en solde | en rabais, en spécial |
| réduction, remise, promo | rabais |
| offre promotionnelle | spécial |
| livraison offerte | livraison gratuite |
| Nous sommes désolés | ON S'EXCUSE |
| e-mail, mail | courriel |
| SMS | texto |
| shopping, faire du shopping | magasinage, magasiner |
| week-end | fin de semaine |
| parking | stationnement |
| bon plan | bonne aubaine |
| en Canada | au Canada |

Nie Frankreich-Registermarker verwenden: vachement, truc, hyper, super sympa, au top,
canon, bluffant, en un rien de temps.

#### (E) Québec-Typografie — produktunabhängig, hier ist Frankreich am sichtbarsten

Zeichen für Zeichen zu prüfen. Zuverlässigster FR-FR-Marker in kurzen Bildtexten.

- **Kein Leerzeichen vor `!` `?` `;`** → `Dis adieu à la peau relâchée!`
  Niemals `relâchée !` — das ist Frankreich-Satz.
- **Leerzeichen vor `:` und `%`** → `Ce qui disparaît avant l'été :` · `98 %`
- **Preis:** Der Betrag kommt **immer aus Spalte J** der jeweiligen Zeile — niemals aus
  dieser Datei, niemals aus der Quell-Ad. Nur das *Format* ist hier festgelegt:
  Zahl mit Dezimal**komma**, Leerzeichen, Dollarzeichen → `<Betrag> $`.
  Richtig: `29,95 $` · `119,00 $` · `9,99 $`. Falsch: `$29.95` · `29,95$` · `29.95 $`.
  Die Zahlen in dieser Datei sind Formatbeispiele, keine Preise.
- Dezimalkomma: `4,8`. Tausender mit Leerzeichen: `20 428`.
- Uhrzeit `23 h 59`. Datum `20 février 26`, Monat klein.
- Anführungszeichen: « Guillemets mit Innenabstand ».
- Akzente sind Pflicht und müssen korrekt sein: `É È À Ç Ê Î Ô Û`.
  Großbuchstaben behalten ihren Akzent (`ÉCONOMISE`, nicht `ECONOMISE`).

#### (F) Bewährte kurze Bausteine — produktunabhängig

Enthalten bewusst **keine** Produktversprechen. Claims kommen aus Spalte G/J und der
Quell-Ad, nie aus dieser Liste:

`COMMANDE MAINTENANT` · `LIVRAISON GRATUITE` · `ÉCONOMISE 50 %` · `ESSAIE-LE 30 JOURS` ·
`SPÉCIAL` · `EN RABAIS` · `QUANTITÉS LIMITÉES` · `SATISFACTION GARANTIE` ·
`VENTE D'HIVER` · `SEULEMENT AUJOURD'HUI`

#### (G) Neue Produktkategorie

Bevor für ein Produkt einer Kategorie generiert wird, die in (C) nicht vorkommt: den
Prüfschritt aus (C) durchführen und die gefundenen Paare als neue Zeile in (C)
ergänzen. Der Lauf wird dadurch nicht blockiert — (A) trägt die Prüfung —, aber die
Zeile gehört nachgetragen, damit die nächste Ad davon profitiert.

### 4.2 FI — Finnisch

Ziel: natürliches Finnisch, wie es ein finnischer Muttersprachler in Werbung schreibt.

- **Keine erfundenen Wörter.** Jedes Wort — besonders jedes Kompositum — muss ein echtes,
  belegtes finnisches Wort sein. Komposita nicht maschinell zusammenstückeln.
- Kasusendungen (Partitiv / Genitiv / Illativ) müssen im LOCKED STRING korrekt sein;
  das Bildmodell darf keine Endung verändern.
- Keine englischen Lehnwörter, wo ein normales finnisches Wort existiert
  (`sale` → `ALE`, `deal`/`offer` → `TARJOUS`, `shoppailu` → `ostokset`).
- `ä` und `ö` müssen im Render korrekt erscheinen — ein gerendertes `a` statt `ä` ist ein
  abgelehntes Bild, kein Detail.
- Preisformat EUR: Zahl, Dezimal**komma**, Leerzeichen, Eurozeichen — `49,99 €`.
  Prozent mit Leerzeichen: `50 %`.

Bewährte kurze Bausteine: `OSTA NYT`, `ILMAINEN TOIMITUS`, `SÄÄSTÄ 50 %`, `TARJOUS`,
`RAJOITETTU ERÄ`, `VAIN NYT`.

### 4.3 NLBE — Niederländisch für Niederlande UND Belgien (Flandern) gemeinsam

Angelegt 2026-10-14. Grundlage: Creative-Research-Master-Doc, Abschnitt
„NETHERLANDS + BELGIUM (NL+BE) — treated as one market" (Google Drive), Taaladvies
der Flämischen Regierung (Eurozeichen, Prozentzeichen), Anrede-Entscheidung von
Jeannine am 2026-10-14.

Ziel: **ein** neutrales Standard-Niederländisch, das in den Niederlanden UND in
Flandern natürlich klingt. Nicht Holland-Niederländisch, nicht Flämisch. Eine Ad läuft
in beiden Ländern, deshalb ist jedes Wort, das nur in einem der beiden Länder üblich
ist, ein Fehler — genau wie Frankreich-Französisch bei FRCA. Der Fehler ist unsichtbar,
weil beide Varianten gültiges Niederländisch sind. Deshalb gilt 4a (Freigabe) auch hier.

> Die Tabellen sind **Beispiele des Prinzips, keine abschließenden Listen.**
> Verbindlich ist der Test unter (A), für jedes Produkt und jede Kategorie.

#### (A) Der Test — gilt für jedes Wort, jedes Produkt, jede Kategorie

> Würde eine Frau aus Gent diesen Ausdruck genauso schreiben wie eine Frau aus Utrecht —
> und würde keine der beiden ihn als „typisch Holland" oder „typisch Flämisch" lesen?

Fällt ein Ausdruck nur in einem der beiden Länder auf, wird er durch das neutrale Wort
ersetzt (Spalte rechts in (C)). Gibt es kein neutrales Wort: Satz umbauen.

#### (B) Anrede: immer `je / jouw`, nie `u / uw` — produktunabhängig

Festgelegt von Jeannine am 2026-10-14 (entspricht den bestehenden NLBE-Ads, z. B.
`2_GlowTan_NLBE`: „geeft je … terwijl je slaapt").

| verboten | erforderlich |
|---|---|
| u, uw, uzelf (als Leseransprache) | je, jij, jouw, jezelf |
| Bestelt u / Probeert u / Ontdekt u | Bestel / Probeer / Ontdek (Imperativ = Verbstamm) |
| uw huid, uw gewrichten, uw hond | je huid, je gewrichten, je hond |

**Häufigster Fehler: Mischung.** Headline mit `je`, CTA mit `u` liest sich sofort wie
eine Übersetzung. Eine Ad, eine Anredeform.

#### (C) Länder-Marker — verboten, weil sie im jeweils anderen Land auffallen

| nur Niederlande (fällt in Flandern auf) | nur Flandern (fällt in NL auf) | neutral, erforderlich |
|---|---|---|
| uitverkoop, koopjes | solden | KORTING, ACTIE |
| lekker (außer für Essen), lekker slapen | — | goed slapen |
| gezellig, hartstikke, superhandig, top! | — | streichen, sagen was es tut |
| drogist | — | apotheek |
| fysiotherapeut | kinesist | streichen oder umschreiben |
| jam | confituur | — |
| pinnen, pinpas, iDEAL | — | streichen (kein Zahlungsmittel im Bild) |
| — | zetel, frigo, microgolf, kleedje | bank, koelkast, magnetron, jurk |
| — | gij, ge | je |
| Namen/Städte nur NL (Amsterdam, Kees, Sanne) | Namen/Städte nur BE | ein Name aus jedem Land über das Set verteilt (z. B. „Rita, 61, uit Gent" / „Marja, 58, uit Zwolle") |

Kategorie-Vokabular, das in beiden Ländern passt: `apotheek` · `voedingssupplement` ·
`gratis levering` · `bestellen` · `winkelmandje` · `gewrichten` · `huid`.

#### (D) Übersetzungs-Artefakte — die sichtbarsten Fehler in Bild-Ads

- **Komposita zusammenschreiben:** `gewrichts ondersteuning` → `gewrichtsondersteuning`.
  Der häufigste Fehler in Bild-Ads. Zusätzlich gilt 1a: nur Komposita, die als Ganzes
  belegt sind.
- **Kein englischer Title Case:** `Natuurlijke Ondersteuning Voor Je Gewrichten` ist falsch.
  Richtig: `Natuurlijke ondersteuning voor je gewrichten` — oder komplett in Großbuchstaben.
- **Adjektivendung prüfen:** `een natuurlijk supplement` (het-Wort) ✓ ·
  `een natuurlijke supplement` ✗.
- **Wörtlich übersetzte Werbefloskeln streichen:** `Ontgrendel de kracht van…`,
  `Zeg vaarwel tegen…`, `Het geheim dat artsen niet willen dat je weet`.
- **Zeitangaben explizit:** nicht `binnen 24 uur` (in Flandern = „frühestens nach 24 h"),
  sondern `Levering in 1 tot 3 werkdagen`.
- **Englischer Text aus der Quell-Ad** (`DIT BESPAARDE MIJ $900`, `FRESH BREATH`) wird
  nicht übernommen — Regel 2. Kein `$` in NLBE.

#### (E) Typografie und Zahlen — produktunabhängig

- **Preis:** Der Betrag kommt **immer aus Spalte J** — nur das Format steht hier.
  Eurozeichen **vor** dem Betrag, Leerzeichen, Dezimal**komma**: `€ 29,95` · `€ 49,00`.
  Spalte J im Tab `NL/BE new` steht mit Punkt (`39.95`) — Punkt durch Komma ersetzen:
  `39.95` → `€ 39,95`.
  Falsch: `29,95 €` · `€29,95` · `€ 29.95` · `€ 24,-`.
  Ganze Beträge immer mit `,00` — `€ 24,-` ist nur in NL üblich, in Belgien unüblich
  (Taaladvies), `,00` ist in beiden korrekt.
- **Prozent ohne Leerzeichen:** `50%` (anders als FRCA/FI!). In der Praxis wird Zahl und
  `%` zusammengeschrieben (Taaladvies).
- **Kein Leerzeichen vor `!` `?` `:`** → `Bestel nu!`
- **Datum:** Monat ausschreiben — `14 oktober` (BE schreibt 14/10, NL 14-10; ausgeschrieben
  ist in beiden eindeutig).
- **Akzente:** `één` (betont), `creëert`, `geïrriteerd` — Trema und Akzente sind Pflicht,
  auch in Großbuchstaben: `ÉÉN`.

#### (F) Claims — Gesundheit / Gewicht (aus dem Master-Doc, NL+BE)

Die belgische Werbeselbstkontrolle JEP stoppt auch Facebook-Ads. Im Bild **verboten**:
Kilo-, Zentimeter- oder Zeitangaben zum Abnehmen (`4 kg in 30 dagen`, `2 maten kleiner`),
Vorher/Nachher bei Gewicht und Körperform, Arzt-Empfehlungen, Krankheitsnamen,
Prozentzahlen aus eigenen „Studien". Steht so etwas in der Quell-Ad: weglassen, nicht
übersetzen.

#### (G) Bewährte kurze Bausteine

`BESTEL NU` · `GRATIS LEVERING` · `50% KORTING` · `ACTIE` · `OP VOORRAAD` ·
`30 DAGEN RETOURRECHT` · `BEPERKTE VOORRAAD` · `ALLEEN VANDAAG`

#### (H) Neue Produktkategorie

Wie 4.1 (G): Kategorie-Wörter vor dem Schreiben gegen (A) prüfen, gefundene Länder-Paare
als neue Zeile in (C) nachtragen.

### 4.4 ZA — Südafrikanisches Englisch

Angelegt 2026-10-14. Grundlage: GCIS Editorial Style Guide (Regierung Südafrika),
Oxford University Press Southern Africa (SA-Wortbedeutungen), Preis-Schreibweise
gemessen am 2026-10-14 auf clicks.co.za und dischem.co.za, Ton-Entscheidung von
Jeannine am 2026-10-14.

Ziel: Englisch, wie es in Südafrika geschrieben wird. **Nicht** US-Englisch. Der Fehler
ist unsichtbar wie bei FRCA — US-Englisch ist gültiges Englisch —, deshalb gilt 4a
(Freigabe) auch hier.

**Ton:** wie in der Quell-Ad (Jeannine, 2026-10-14). Lokalisiert werden Rechtschreibung,
Wörter, Einheiten, Währung und Format — nicht der Stil. Ausnahme: Kein südafrikanischer
Slang (`lekker`, `howzit`, `eish`, `jol`), der nicht inhaltlich gebraucht wird — eingebauter
Slang wirkt in einer Shop-Ad aufgesetzt.

#### (A) Der Test — gilt für jedes Wort

> Würde ein südafrikanischer Shop (Clicks, Dis-Chem, Takealot) dieses Wort, diese
> Schreibweise, diese Einheit genau so verwenden?

#### (B) Rechtschreibung: britisch, `-ise` — nie amerikanisch

Laut GCIS Editorial Style Guide: britische Schreibweise, `-ise` statt `-ize`.

| verboten (US) | erforderlich (ZA) |
|---|---|
| color, favorite, flavor, odor, behavior | colour, favourite, flavour, odour, behaviour |
| center, liter, meter | centre, litre, metre |
| organize, realize, minimize, optimize | organise, realise, minimise, optimise |
| moisturizer, moisturize | moisturiser, moisturise |
| analyze, paralyze | analyse, paralyse |
| gray | grey |
| program (außer Computer) | programme |

#### (C) Wörter und Einheiten

| US / UK | ZA |
|---|---|
| free shipping | FREE DELIVERY |
| shipping | delivery |
| cell phone, mobile phone | cellphone |
| drugstore | pharmacy |
| zip code | postal code |
| vacation | holiday |
| fall (Jahreszeit) | autumn |
| lbs, pounds, oz, inches, feet, °F | kg, g, ml, cm, m, °C |

**Wörter mit anderer Bedeutung in Südafrika — nicht im US-Sinn verwenden:**
`robot` = Ampel · `packet` = Plastiktüte · `just now` = gleich/später · `bond` = Hypothek ·
`café` = Kiosk/Eckladen (Oxford SA).

**Jahreszeiten:** Südhalbkugel. Oktober–März ist Sommer. `SUMMER SALE` im Juli ist
falsch; saisonale Aussagen aus einer europäischen/US-Quell-Ad nicht übernehmen.

#### (D) Typografie und Zahlen

- **Preis:** Der Betrag kommt **immer aus Spalte J** — nur das Format steht hier.
  `R` direkt vor dem Betrag, **kein Leerzeichen**, Dezimal**punkt**: `R299.99`.
  Spalte J im Tab ZA steht ohne Währungszeichen mit Punkt (`599.00`) — so übernehmen und
  nur `R` davorsetzen: `599.00` → `R599.00`.
  Falsch: `R 299,99` · `ZAR 299` · `299 R` · `$29.99`.
  Begründung: Die Regierung schreibt offiziell `R300,45` (Komma), die großen Händler
  aber Punkt — gemessen am 2026-10-14: Clicks `R299.99`, Dis-Chem `R 249.99`. Für
  Shop-Ads gilt, was die Käuferin im Shop sieht: Punkt. Kein Leerzeichen nach `R`
  (GCIS: „R500"). Kein Tausendertrenner bei Beträgen unter R10 000.
- **Prozent ohne Leerzeichen:** `50%` (GCIS).
- **Datum:** `14 October` / `14 October 2026` — nie `October 14`.
- **Kein Leerzeichen vor `!` `?` `:`**.

#### (E) Bewährte kurze Bausteine

`ORDER NOW` · `FREE DELIVERY` · `SAVE 50%` · `LIMITED STOCK` · `TODAY ONLY` ·
`30-DAY MONEY-BACK GUARANTEE` · `3 FOR 2`

#### (F) Offene Lücke

Südafrikanische Werberegeln für Gesundheits-Claims (Advertising Regulatory Board,
SAHPRA) sind **noch nicht recherchiert**. Bis dahin gilt für ZA dieselbe Vorsicht wie
4.3 (F): keine Kilo-/Zeitangaben zum Abnehmen, keine Krankheitsnamen, keine
Arzt-Empfehlungen im Bild.

---

## 4a. FREIGABE VOR DEM RENDERN — blockierend

**Das ist die Stelle, an der FRCA bisher durchgerutscht ist.** Die Prüfung in
Abschnitt 5 findet *nach* dem Rendern statt und vergleicht das Bild mit dem LOCKED
STRING. Sie kann deshalb nur finden, ob das Bildmodell den Text verfälscht hat — **nie,
ob der LOCKED STRING selbst schon Frankreich-Französisch war.** Ein sauber gerenderter
Frankreich-Satz bestand jede bisherige Kontrolle.

Der Unterschied zu FI ist genau hier: finnischer Text ist erkennbar finnisch oder gar
nicht. Frankreich-Französisch dagegen **ist** gültiges Französisch — der Fehler ist
unsichtbar, solange niemand gezielt danach sucht. Deshalb braucht FRCA eine eigene
Freigabe, FI nicht. **Dasselbe gilt für NLBE und ZA:** Holland- oder Flandern-Niederländisch
ist gültiges Niederländisch, US-Englisch ist gültiges Englisch — beide brauchen die
Freigabe (2) genauso wie FRCA.

**Vor dem ERSTEN `generate_image`-Call einer Ad sind beide Schritte Pflicht:**

**(1) Maschinelle Prüfung — blockierend, kein Ermessen**

```
python3 scripts/check_locked_string.py <MARKET_CODE> <pfad_zur_locked_strings.md>
```

Exit-Code 1 = **nicht rendern.** LOCKED STRING korrigieren, erneut laufen lassen.
Erst bei Exit 0 darf gerendert werden. Das Skript prüft mechanisch (je nach Markt):
Leerzeichen vor `!` `?` `;` · fehlendes Leerzeichen vor `:` `%` · `vous/votre/vos` ·
2.-Person-Plural-Verbformen · Wörter aus den Verbotslisten in Abschnitt 4 ·
fehlende Akzente in Großbuchstaben · falsches Preisformat · Textelemente über 6 Wörter.

**(2) Register-Freigabe — Urteilsschritt, muss protokolliert werden**

Das Skript kann Register und Idiomatik **nicht** prüfen. Deshalb zusätzlich, in der
`State/<product>_<market>_locked_strings.md`, für jedes Textelement eine Zeile schreiben:

```
FREIGABE 4.1(A): "<Textelement>" — existiert im Québec-Französisch eigenständig? JA, weil <Begründung in einem Halbsatz>
```

Für NLBE und ZA mit dem Test ihres eigenen Abschnitts:

```
FREIGABE 4.3(A): "<Textelement>" — in NL UND Flandern neutral, Anrede je? JA, weil <Begründung in einem Halbsatz>
FREIGABE 4.4(A): "<Textelement>" — so in einem südafrikanischen Shop, britische Schreibweise? JA, weil <Begründung in einem Halbsatz>
```

**Fehlt dieser Block in der locked_strings.md, ist die Ad nicht freigegeben und darf nicht
gerendert werden.** Eine pauschale Zeile wie „alles geprüft" ist keine Freigabe — es
braucht eine Zeile pro Textelement. Der Grund: eine Selbstprüfung ohne schriftliches
Ergebnis findet nichts; erst das Ausformulieren zwingt zum tatsächlichen Hinsehen.

Im Abschlussbericht des Laufs steht pro Zeile, ob (1) bestanden hat und dass (2)
protokolliert wurde.

---

## 5. Prüfung vor dem Upload (Sicherheitsnetz, nicht die Lösung)

Für **jedes einzelne** Bild, nicht stichprobenartig:

1. Das Ergebnisbild mit dem `Read`-Tool ansehen — nicht auf OCR-Snippets aus der
   Drive-Suche verlassen.
2. Jedes sichtbare Wort abtippen (Transkription) und gegen den LOCKED STRING
   diffen — Zeichen für Zeichen, inklusive Akzente und `ä`/`ö`.
3. Zusätzlich gegen die Verbotsliste aus Abschnitt 4 prüfen.
4. Abweichung = Bild wird **nicht** hochgeladen. Neu generieren, dabei den LOCKED STRING
   kürzen (weniger Wörter, größere Schrift), bis der Render exakt passt.
5. Die Transkription jedes hochgeladenen Bildes in der State-Datei protokollieren.

Ein Hinweis im Prompt ist **kein** Nachweis. Nur die Transkription zählt.

## 6. Neue Märkte

Bei jedem weiteren Markt mit eigener Landesvariante (SE, UK/US, DE/AT/CH …) vor dem
ersten Lauf einen eigenen Abschnitt 4.x mit Anrede, Verbots-/Pflichtliste und
Zahlenformat anlegen. Ohne diesen Abschnitt wird für den Markt nicht generiert.
Zusätzlich braucht der Markt eine Prüffunktion in `scripts/check_locked_string.py`,
einen Eintrag unter `language_rules` und einen Drive-Ordner unter
`drive.translated_ads_subfolders` in `config/automation.config.json`.
Bereits angelegt: 4.1 FRCA, 4.2 FI, 4.3 NLBE, 4.4 ZA.

Abschnitt 1a (echte Wörter) gilt dabei automatisch mit — sie muss nicht pro Markt neu
festgelegt werden, sondern ist Teil der Grundregeln dieser Datei für jede Sprache.
