#!/usr/bin/env python3
"""
Mechanische Freigabepruefung fuer LOCKED STRINGS, vor dem Rendern.

Aufruf:
    python3 scripts/check_locked_string.py FRCA <datei_mit_locked_strings>
    python3 scripts/check_locked_string.py FI   <datei>
    python3 scripts/check_locked_string.py NLBE <datei>
    python3 scripts/check_locked_string.py ZA   <datei>
    echo "Dis adieu!" | python3 scripts/check_locked_string.py FRCA -

Exit 0 = freigegeben. Exit 1 = BLOCKIERT, nicht rendern.

Prueft nur das mechanisch Entscheidbare. Register und Idiomatik kann dieses
Skript nicht pruefen - dafuer bleibt der Test in docs/language-rules.md 4.1 (A).
Ein bestandener Lauf heisst NICHT "ist gutes Quebecois", sondern nur
"enthaelt keinen der bekannten Frankreich-Marker".
"""
import re, sys, unicodedata

# --- FRCA ---------------------------------------------------------------

VOUS = re.compile(r'\b(vous|votre|vos)\b', re.I)

# 2. Person Plural als Leseransprache. Whitelist verhindert Falschtreffer
# bei Substantiven auf -ez (nez, assez, chez, rez).
EZ_OK = {'nez', 'assez', 'chez', 'rez'}
EZ = re.compile(r'\b([a-zà-ÿ]{3,}ez)\b', re.I)

IMPERATIF_FR = {
    'commandez': 'Commande', 'découvrez': 'Découvre', 'decouvrez': 'Découvre',
    'profitez': 'Profite', 'essayez': 'Essaie', 'achetez': 'Achète',
    'économisez': 'Économise', 'economisez': 'Économise', 'dites': 'Dis',
    'retrouvez': 'Retrouve', 'redécouvrez': 'Redécouvre', 'oubliez': 'Oublie',
    'imaginez': 'Imagine', 'choisissez': 'Choisis', 'prenez': 'Prends',
    'obtenez': 'Obtiens', 'recevez': 'Reçois', 'gardez': 'Garde',
    'offrez': 'Offre', 'faites': 'Fais', 'soyez': 'Sois', 'voyez': 'Vois',
}

# Frankreich-Beautyregister und Anglizismen. Erweiterbar - siehe
# docs/language-rules.md 4.1 (A)/(C)/(D).
VERBOTEN_FRCA = {
    'sublimer': 'raffermir / dire, was es tut', 'sublimateur': 'raffermissant',
    'repulper': 'plus ferme', 'repulpé': 'plus ferme', 'repulpe': 'plus ferme',
    "coup d'éclat": 'peau plus lumineuse', 'bonne mine': 'une peau ferme',
    'geste beauté': 'streichen', 'rituel beauté': 'streichen',
    'routine beauté': 'streichen', 'cocooning': 'streichen',
    'booster': 'renforcer', 'boosté': 'renforcé',
    'spray': 'vaporisateur', 'lifting': 'effet raffermissant',
    'peeling': 'exfoliation', 'make-up': 'maquillage', 'waterproof': 'résistant à l\'eau',
    'glow': 'éclat',
    'soldes': 'VENTE / RABAIS', 'en solde': 'en rabais',
    'réduction': 'rabais', 'remise': 'rabais', 'promo': 'rabais',
    'offre promotionnelle': 'spécial', 'livraison offerte': 'livraison gratuite',
    'e-mail': 'courriel', 'sms': 'texto', 'shopping': 'magasinage',
    'week-end': 'fin de semaine', 'parking': 'stationnement',
    'bon plan': 'bonne aubaine', 'en canada': 'au Canada',
    'nous sommes désolés': "ON S'EXCUSE",
    'vachement': '-', 'au top': '-', 'bluffant': '-', 'en un rien de temps': '-',
}

# Grossbuchstaben-Woerter, die einen Akzent tragen MUESSEN.
AKZENT_CAPS = {
    'ECONOMISE': 'ÉCONOMISE', 'ECONOMISEZ': 'ÉCONOMISE', 'DECOUVRE': 'DÉCOUVRE',
    'SPECIAL': 'SPÉCIAL', 'ELASTICITE': 'ÉLASTICITÉ', 'FERMETE': 'FERMETÉ',
    'RELACHEE': 'RELÂCHÉE', 'RELACHE': 'RELÂCHÉ', 'BEAUTE': 'BEAUTÉ',
    'QUALITE': 'QUALITÉ', 'GARANTIE': None, 'ETE': 'ÉTÉ', 'DEJA': 'DÉJÀ',
    'RESULTATS': 'RÉSULTATS', 'REDUIT': 'RÉDUIT', 'TESTE': 'TESTÉ',
    'LIMITEES': 'LIMITÉES', 'QUANTITES': 'QUANTITÉS', 'SANTE': 'SANTÉ',
}

PREIS_FRCA_OK = re.compile(r'\b\d{1,3}(?: \d{3})*,\d{2} \$')
PREIS_VERDAECHTIG = re.compile(r'(\$\s?\d)|(\d[.,]\d{2}\$)|(\d+\.\d{2}\s?\$)')

# --- FI -----------------------------------------------------------------

FI_UMLAUT = {
    'SAASTA': 'SÄÄSTÄ', 'SAASTA!': 'SÄÄSTÄ', 'ERA': 'ERÄ', 'RAJOITETTU ERA': 'RAJOITETTU ERÄ',
    'PAIVA': 'PÄIVÄ', 'PAIVAA': 'PÄIVÄÄ', 'TAYDELLINEN': 'TÄYDELLINEN',
    'ALE': None, 'TARJOUS': None, 'OSTA': None,
}
PREIS_FI_OK = re.compile(r'\b\d{1,3}(?: \d{3})*,\d{2} €')


# --- NLBE ---------------------------------------------------------------
# docs/language-rules.md 4.3. Anrede je/jouw (Jeannine, 2026-10-14).

U_NLBE = re.compile(r'\b(u|uw|uzelf)\b', re.I)

# Laender-Marker: fallen im jeweils anderen Land auf (4.3 C).
VERBOTEN_NLBE = {
    'uitverkoop': 'KORTING / ACTIE', 'koopjes': 'KORTING / ACTIE',
    'solden': 'KORTING / ACTIE', 'hartstikke': 'streichen',
    'gezellig': 'streichen', 'superhandig': 'streichen',
    'lekker slapen': 'goed slapen', 'drogist': 'apotheek',
    'fysiotherapeut': 'umschreiben', 'kinesist': 'umschreiben',
    'confituur': '-', 'pinnen': 'streichen', 'pinpas': 'streichen',
    'ideal': 'streichen (iDEAL gibt es in Belgien nicht)',
    'zetel': 'bank', 'frigo': 'koelkast', 'microgolf': 'magnetron',
    'kleedje': 'jurk', 'gij': 'je', 'ge': 'je',
    'ontgrendel': 'Floskel streichen', 'zeg vaarwel': 'Floskel streichen',
    'binnen 24 uur': 'Levering in 1 tot 3 werkdagen',
}
PREIS_NLBE_OK = re.compile(r'€ \d{1,3}(?:\.\d{3})*,\d{2}(?!\d)')

# --- ZA -----------------------------------------------------------------
# docs/language-rules.md 4.4. Britische Schreibweise (GCIS), Preis R299.99.

US_SPELLING = {
    'color': 'colour', 'colors': 'colours', 'favorite': 'favourite',
    'flavor': 'flavour', 'odor': 'odour', 'behavior': 'behaviour',
    'center': 'centre', 'liter': 'litre', 'liters': 'litres', 'meter': 'metre',
    'organize': 'organise', 'realize': 'realise', 'minimize': 'minimise',
    'optimize': 'optimise', 'moisturizer': 'moisturiser', 'moisturize': 'moisturise',
    'moisturizing': 'moisturising', 'analyze': 'analyse', 'gray': 'grey',
}
VERBOTEN_ZA = {
    'free shipping': 'FREE DELIVERY', 'shipping': 'delivery',
    'cell phone': 'cellphone', 'mobile phone': 'cellphone',
    'drugstore': 'pharmacy', 'zip code': 'postal code', 'vacation': 'holiday',
    'lbs': 'kg', 'pounds': 'kg', 'inches': 'cm', 'fahrenheit': '°C', '°f': '°C',
    'zar': "'R' vor dem Betrag",
}
PREIS_ZA_OK = re.compile(r'(?<![\w])R\d{1,4}(?:\.\d{2})?(?![\d,])')


def pruefe_frca(text):
    err, warn = [], []
    for m in re.finditer(r'\s+([!?;])', text):
        err.append(f"Leerzeichen vor '{m.group(1)}' — Frankreich-Satz. Québec: kein Leerzeichen.")
    for m in re.finditer(r'(?<![\s\d])([:%])', text):
        err.append(f"Kein Leerzeichen vor '{m.group(1)}' — Québec setzt hier eines.")
    for m in VOUS.finditer(text):
        err.append(f"'{m.group(0)}' als Leseransprache — FRCA duzt: tu / ton / ta / tes.")
    for m in EZ.finditer(text):
        w = m.group(1).lower()
        if w in EZ_OK:
            continue
        ziel = IMPERATIF_FR.get(w)
        err.append(f"'{m.group(1)}' ist 2. Person Plural" + (f" — FRCA: {ziel}." if ziel else " — FRCA duzt."))
    low = text.lower()
    for bad, good in VERBOTEN_FRCA.items():
        if re.search(r'(?<![a-zà-ÿ])' + re.escape(bad) + r'(?![a-zà-ÿ])', low):
            err.append(f"'{bad}' ist Frankreich-Französisch — Québec: {good}")
    for w in re.findall(r'\b[A-ZÀ-ÿ]{3,}\b', text):
        ziel = AKZENT_CAPS.get(w)
        if ziel:
            err.append(f"'{w}' ohne Akzent — richtig: {ziel}. Akzente bleiben auch in Grossbuchstaben.")
    if PREIS_VERDAECHTIG.search(text) and not PREIS_FRCA_OK.search(text):
        err.append("Preisformat falsch — CAD ist '<Betrag> $' mit Dezimalkomma, z. B. 29,95 $. Nie $29.95 / 29,95$.")
    for el in [l for l in text.splitlines() if l.strip()]:
        n = len(re.findall(r"[\wÀ-ÿ'’-]+", el))
        if n > 6:
            warn.append(f"{n} Wörter in einem Textelement (max. 6): {el.strip()[:60]}")
    return err, warn


def pruefe_fi(text):
    err, warn = [], []
    for w in re.findall(r'\b[A-ZÄÖ]{3,}\b', text):
        ziel = FI_UMLAUT.get(w)
        if ziel:
            err.append(f"'{w}' ohne Umlaut — richtig: {ziel}.")
    if re.search(r'(€\s?\d)|(\d+\.\d{2})', text) and not PREIS_FI_OK.search(text):
        err.append("Preisformat falsch — EUR ist '<Betrag> €' mit Dezimalkomma, z. B. 29,95 €.")
    for el in [l for l in text.splitlines() if l.strip()]:
        n = len(re.findall(r'[\wÄÖäö-]+', el))
        if n > 6:
            warn.append(f"{n} Wörter in einem Textelement (max. 6): {el.strip()[:60]}")
    return err, warn


def _woerter_pro_element(text, warn):
    for el in [l for l in text.splitlines() if l.strip()]:
        n = len(re.findall(r"[\wÀ-ÿ'’-]+", el))
        if n > 6:
            warn.append(f"{n} Wörter in einem Textelement (max. 6): {el.strip()[:60]}")


def _verbotsliste(text, liste, err, markt):
    low = text.lower()
    for bad, good in liste.items():
        if re.search(r'(?<![\wÀ-ÿ])' + re.escape(bad) + r'(?![\wÀ-ÿ])', low):
            err.append(f"'{bad}' ist in {markt} verboten — stattdessen: {good}")


def pruefe_nlbe(text):
    err, warn = [], []
    for m in U_NLBE.finditer(text):
        err.append(f"'{m.group(0)}' als Leseransprache — NLBE duzt: je / jouw / jezelf.")
    _verbotsliste(text, VERBOTEN_NLBE, err, 'NLBE')
    if '$' in text:
        err.append("'$' in NLBE — Währung ist Euro: '€ 29,95'.")
    if re.search(r'\d,-', text):
        err.append("',-' ist nur in NL üblich — ganze Beträge als '€ 24,00'.")
    if re.search(r'\d\s?€', text) or re.search(r'€\d', text) or re.search(r'€ ?\d+\.\d{2}(?!\d)', text):
        err.append("Preisformat falsch — NLBE ist '€ <Betrag>' mit Leerzeichen und Dezimalkomma, z. B. € 29,95.")
    elif '€' in text and not PREIS_NLBE_OK.search(text):
        err.append("Preisformat falsch — NLBE ist '€ 29,95' (Zeichen vorne, Leerzeichen, Komma, 2 Dezimalen).")
    if re.search(r'\d %', text):
        err.append("Leerzeichen vor '%' — NLBE schreibt '50%'.")
    if re.search(r'\s[!?:]', text):
        err.append("Leerzeichen vor '!' '?' ':' — im Niederländischen kein Leerzeichen.")
    _woerter_pro_element(text, warn)
    return err, warn


def pruefe_za(text):
    err, warn = [], []
    low = text.lower()
    for w in re.findall(r"[a-z]+", low):
        if w in US_SPELLING:
            err.append(f"'{w}' ist US-Schreibweise — ZA: {US_SPELLING[w]}.")
    _verbotsliste(text, VERBOTEN_ZA, err, 'ZA')
    if '$' in text or '€' in text:
        err.append("'$'/'€' in ZA — Währung ist Rand: 'R299.99'.")
    if re.search(r'\bR\s\d', text):
        err.append("Leerzeichen nach 'R' — ZA: 'R299.99' ohne Leerzeichen.")
    if re.search(r'\bR\d+,\d{2}\b', text):
        err.append("Dezimalkomma im Preis — ZA-Shops schreiben Punkt: 'R299.99'.")
    if re.search(r'\d %', text):
        err.append("Leerzeichen vor '%' — ZA schreibt '50%'.")
    if re.search(r'\s[!?:]', text):
        err.append("Leerzeichen vor '!' '?' ':' — im Englischen kein Leerzeichen.")
    if re.search(r'\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}\b', text):
        err.append("US-Datum — ZA schreibt '14 October', nicht 'October 14'.")
    _woerter_pro_element(text, warn)
    return err, warn


def main():
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(2)
    markt = sys.argv[1].upper()
    text = sys.stdin.read() if sys.argv[2] == '-' else open(sys.argv[2], encoding='utf-8').read()
    if markt == 'FRCA':
        err, warn = pruefe_frca(text)
    elif markt == 'FI':
        err, warn = pruefe_fi(text)
    elif markt == 'NLBE':
        err, warn = pruefe_nlbe(text)
    elif markt == 'ZA':
        err, warn = pruefe_za(text)
    else:
        print(f"Unbekannter Markt '{markt}'. Vor dem ersten Lauf einen Abschnitt 4.x in "
              f"docs/language-rules.md UND eine Pruefung hier anlegen (Abschnitt 6/G).")
        sys.exit(1)
    for w in warn:
        print(f"WARNUNG  {w}")
    if err:
        print(f"\nBLOCKIERT — {len(err)} Fehler im LOCKED STRING ({markt}). Nicht rendern.\n")
        for e in err:
            print(f"  FEHLER  {e}")
        print("\nLOCKED STRING korrigieren und erneut pruefen. Vollstaendige Regeln: "
              "docs/language-rules.md Abschnitt 4.")
        sys.exit(1)
    print(f"OK — mechanische Pruefung {markt} bestanden ({len(warn)} Warnung(en)).")
    abschnitt = {'FRCA': '4.1 (A)', 'FI': '4.2', 'NLBE': '4.3 (A)', 'ZA': '4.4 (A)'}[markt]
    print("ACHTUNG: das prueft nur bekannte Marker. Register und Idiomatik sind damit "
          f"NICHT geprueft — dafuer gilt der Test in docs/language-rules.md {abschnitt}.")
    sys.exit(0)

if __name__ == '__main__':
    main()
