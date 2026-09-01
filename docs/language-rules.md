# Sprachregeln für generierte Bilder (alle Märkte — aktuell FRCA / FI)

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
2. Diese Strings als **LOCKED STRING** in `<product_name>_<market_code>_ad_copy.md`
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

Ziel: natürliches Québec-Französisch, wie es in kanadischer Einzelhandels- und
Beautywerbung geschrieben wird. **Nicht** Frankreich-Französisch, nicht "neutrales"
Französisch.

> **Warum die Verbotsliste allein bisher nicht gereicht hat:** Die Liste unter (D) ist
> eine Promo-Wortliste (SOLDES, courriel, week-end, parking). In einer Hautpflege- oder
> Kosmetik-Ad kommt **kein einziges** dieser Wörter je vor. Die Prüfung war deshalb
> immer bestanden — und der Text trotzdem Frankreich-Französisch, weil nirgends stand,
> wie man Québécois *schreibt*. Die Abschnitte (A), (C) und (E) schließen genau diese
> Lücke. Sie sind der Kern dieser Marktspezifikation, nicht die Verbotsliste.

**Zweistufig, verpflichtend:** erst den französischen Text schreiben, dann Zeile für
Zeile gegen (A) bis (E) durchgehen und neu schreiben. Erst die überarbeitete Fassung
wird LOCKED STRING.

#### (A) Register — die wichtigste Regel

Frankreich-Beautywerbung ist abstrakt und lyrisch. Québec-Werbung ist einfach, konkret
und direkt. Diese Registerdifferenz ist der Grund, warum ein Text "korrekt" sein kann
und trotzdem sofort als Frankreich-Text erkannt wird.

| verboten (Frankreich-Beautyregister) | erforderlich (Québec, schlicht) |
|---|---|
| sublimer, sublimateur | raffermir, raffermissant |
| repulper, repulpé | plus ferme, rebondi |
| geste beauté, rituel beauté, routine beauté | streichen — direkt sagen, was es tut |
| révéler l'éclat, coup d'éclat, éclat sublimé | peau plus lumineuse |
| une peau de rêve, peau divine, bonne mine | une peau ferme |
| booster, boosté | renforcer, renforcé |
| cocooning, peau nette | streichen |

Faustregel: sagt der Satz, **was das Produkt tut**, oder beschreibt er ein Gefühl?
Québec sagt, was es tut.

#### (B) Anrede: immer `tu`, nie `vous`

Das Verb wird mitkonjugiert — nur das Pronomen zu tauschen ist ein Fehler.

| verboten | erforderlich |
|---|---|
| Vous / Votre / Vos (als Leseransprache) | Tu / Ton / Ta / Tes |
| Commandez / Découvrez / Profitez / Essayez / Achetez / Économisez | Commande / Découvre / Profite / Essaie / Achète / Économise |
| Dites adieu / Retrouvez / Redécouvrez | Dis adieu / Retrouve / Redécouvre |
| votre peau, vos bras | ta peau, tes bras |

#### (C) Kategorie-Vokabular (Kosmetik / Körperpflege)

Québec ist bei Anglizismen **strenger** als Frankreich. Was in Paris normal ist, wirkt
in Montréal nachlässig.

| verboten (Frankreich / Anglizismus) | erforderlich (Québec) |
|---|---|
| spray | vaporisateur |
| lifting, effet lift | effet raffermissant |
| peeling | exfoliation |
| patch | timbre |
| make-up | maquillage |
| waterproof | résistant à l'eau |
| glow | éclat |
| soin de la peau (Singular) | soins de la peau |
| patte-d'oie (Singular) | pattes-d'oie (immer Plural) |

#### (D) Promo-Vokabular

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

#### (E) Québec-Typografie — hier ist Frankreich am sichtbarsten

Diese Punkte sind Zeichen-für-Zeichen zu prüfen. Sie sind der zuverlässigste
FR-FR-Marker in kurzen Bildtexten und der häufigste Fehler bisher.

- **Kein Leerzeichen vor `!` `?` `;`** → `Dis adieu à la peau relâchée!`
  Niemals `relâchée !` — das ist Frankreich-Satz.
- **Leerzeichen vor `:` und `%`** → `Ce qui disparaît avant l'été :` · `98 %`
- Preisformat CAD: Zahl, Leerzeichen, Dollarzeichen, Dezimal**komma** — `49,99 $`.
  Niemals `$49.99`, niemals `49,99$`.
- Dezimalkomma: `4,8`. Tausender mit Leerzeichen: `20 428`.
- Uhrzeit `23 h 59`. Datum `20 février 26`, Monat klein.
- Anführungszeichen: « Guillemets mit Innenabstand ».
- Akzente sind Pflicht und müssen korrekt sein: `É È À Ç Ê Î Ô Û`.
  Großbuchstaben behalten ihren Akzent (`ÉCONOMISE`, nicht `ECONOMISE`).

#### (F) Bewährte kurze Bausteine

Neutral formuliert, ohne Produktversprechen — Claims kommen aus Spalte G/J und der
Quell-Ad, nicht aus dieser Liste:

`PEAU PLUS FERME` · `SANS CHIRURGIE` · `RAFFERMIT ET HYDRATE` · `DIS ADIEU À LA PEAU
RELÂCHÉE` · `COMMANDE MAINTENANT` · `LIVRAISON GRATUITE` · `ÉCONOMISE 50 %` ·
`ESSAIE-LE 30 JOURS` · `SPÉCIAL` · `EN RABAIS`

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

Bei jedem weiteren Markt mit eigener Landesvariante (NL/BE, UK/US, DE/AT/CH …) vor dem
ersten Lauf einen eigenen Abschnitt 4.x mit Anrede, Verbots-/Pflichtliste und
Zahlenformat anlegen. Ohne diesen Abschnitt wird für den Markt nicht generiert.

Abschnitt 1a (echte Wörter) gilt dabei automatisch mit — sie muss nicht pro Markt neu
festgelegt werden, sondern ist Teil der Grundregeln dieser Datei für jede Sprache.
