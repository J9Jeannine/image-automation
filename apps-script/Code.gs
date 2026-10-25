// Apps-Script-Web-App in Jeannines Google-Konto ("Unbenanntes Projekt").
// Diese Datei ist die Quelle der Wahrheit fuer den Code im Script-Editor.
// 1) doPost: laedt ein Bild per URL in einen Drive-Ordner (Upload der Routine).
// 2) Nach JEDEM Upload: fillFunnelSheet() traegt L/N/O/P in den Markt-Tabs und
//    G/H/I im Tab 'Winning Products' ein.
// 3) Zusaetzlich stuendlicher Zeit-Trigger als Netz (einmalig installTrigger() ausfuehren).

const SHEET_ID = '1SkD7jrC-othtbwTYyz1VCK1HPIkEKHxc_hSAvRp2iL8';
const MARKETS = {
  FI:   '1Ey4aVRrpzrzolETnzKVxVCZQGZjm0P5K', // Translated-Ads/FI
  FRCA: '1ZeW7nKHrCMNOBH6jIKZrzNYjJWXPvQDW', // Translated-Ads/FRCA
  ZA:   '1XyBfLC5DwBBROzwwfiO25WmsyuJxRJ6f', // Translated-Ads/ZA
  'NL/BE new': '1GO1rGgSkUDMlsVhu06ACxkr4WJzrg-Mp' // Translated-Ads/NLBE
};

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  const req = JSON.parse(e.postData.contents);
  if (req.action === 'fill') {
    return json_({ sheet: fillFunnelSheet() });
  }
  const folder = DriveApp.getFolderById(req.folderId);
  const blob = UrlFetchApp.fetch(req.url).getBlob().setName(req.name);
  const file = folder.createFile(blob);
  let sheet;
  try { sheet = fillFunnelSheet(); } catch (err) { sheet = 'ERROR: ' + err; }
  return json_({
    id: file.getId(),
    link: 'https://drive.google.com/file/d/' + file.getId() + '/view',
    sheet: sheet
  });
}

function setIfEmpty_(sh, a1, value, isFormula) {
  const cell = sh.getRange(a1);
  if (String(cell.getValue() || '').trim() || cell.getFormula()) return false;
  if (isFormula) { cell.setFormula(value); } else { cell.setValue(value); }
  return true;
}

// Liest alle Ordner "<YYYY-MM-DD> - <Produkt>" unter Translated-Ads/<Markt> und traegt
// fuer jede Zeile, deren Spalte G den Produktnamen hat, L/N/O/P ein -- nur leere Zellen.
function fillFunnelSheet() {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const written = [];
    Object.keys(MARKETS).forEach(function (tab) {
      const sh = ss.getSheetByName(tab);
      if (!sh) return;
      const folders = {};
      const it = DriveApp.getFolderById(MARKETS[tab]).getFolders();
      while (it.hasNext()) {
        const f = it.next();
        const m = f.getName().match(/^(\d{4})-(\d{2})-(\d{2})\s*-\s*(.+)$/);
        if (!m) continue;
        const key = m[4].trim().toLowerCase();
        const iso = m[1] + m[2] + m[3];
        if (folders[key] && folders[key].iso > iso) continue; // neuester Ordner gewinnt
        folders[key] = { id: f.getId(), iso: iso,
          date: new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])) };
      }
      const last = sh.getLastRow();
      const names = sh.getRange('G1:G' + last).getValues();
      for (let i = 1; i < last; i++) { // Zeile 1 = Kopfzeile
        const name = String(names[i][0] || '').trim();
        if (!name) continue;
        const hit = folders[name.toLowerCase()];
        if (!hit) continue;
        const r = i + 1;
        const o = setIfEmpty_(sh, 'O' + r,
          '=HYPERLINK("https://drive.google.com/drive/folders/' + hit.id + '";"' + name + '")', true);
        setIfEmpty_(sh, 'L' + r, hit.date, false);
        setIfEmpty_(sh, 'N' + r, 'claude', false);
        setIfEmpty_(sh, 'P' + r, 'in progress', false);
        if (o) written.push(tab + '!' + r + ' ' + name);
      }
    });

    // --- Tab "Winning Products" -------------------------------------------
    // Eigene Spalten (NICHT die der Markt-Tabs): C = Produkt, G = Bearbeiter,
    // H = Link auf den Set-Ordner, I = Lauf-Datum. Erste Datenzeile = 3.
    // Die Set-Ordner liegen eine Ebene tiefer als die Tagesordner:
    //   Translated-Ads/<Markt>/<YYYY-MM-DD> - <Produkt>/<Produkt> Set <N>
    // Spalte A (Markt) wird bewusst NICHT gebraucht: gesucht wird ueber den
    // Produktnamen in allen Markt-Baeumen. Damit funktioniert die Zeile auch,
    // wenn A noch leer ist.
    const wp = ss.getSheetByName('Winning Products');
    if (wp && wp.getLastRow() >= 3) {
      const wpLast = wp.getLastRow();
      const wpRows = wp.getRange('A3:I' + wpLast).getValues();

      // Schon verlinkte Set-Ordner einsammeln, damit kein Ordner zweimal
      // in verschiedenen Zeilen landet.
      const used = {};
      const wpH = wp.getRange('H3:H' + wpLast).getFormulas();
      for (let i = 0; i < wpH.length; i++) {
        const m = String(wpH[i][0] || '').match(/folders\/([-\w]+)/);
        if (m) used[m[1]] = true;
      }

      // Alle Set-Ordner je Produkt aus allen Markt-Baeumen sammeln.
      const sets = {};
      Object.keys(MARKETS).forEach(function (tab) {
        const days = DriveApp.getFolderById(MARKETS[tab]).getFolders();
        while (days.hasNext()) {
          const day = days.next();
          const dm = day.getName().match(/^(\d{4})-(\d{2})-(\d{2})\s*-\s*(.+)$/);
          if (!dm) continue;
          const prod = dm[4].trim().toLowerCase();
          const subs = day.getFolders();
          while (subs.hasNext()) {
            const s = subs.next();
            const sm = s.getName().match(/^(.+?)\s+Set\s+(\d+)$/i);
            if (!sm) continue;
            (sets[prod] = sets[prod] || []).push({
              id: s.getId(),
              n: Number(sm[2]),
              date: new Date(Number(dm[1]), Number(dm[2]) - 1, Number(dm[3]))
            });
          }
        }
      });
      Object.keys(sets).forEach(function (k) {
        sets[k].sort(function (a, b) { return a.n - b.n; });
      });

      for (let i = 0; i < wpRows.length; i++) {
        const prod = String(wpRows[i][2] || '').trim(); // Spalte C
        if (!prod) continue;
        const cand = sets[prod.toLowerCase()];
        if (!cand) continue;
        let pick = null;
        for (let j = 0; j < cand.length; j++) {
          if (!used[cand[j].id]) { pick = cand[j]; break; }
        }
        if (!pick) continue;
        const r = i + 3;
        const ok = setIfEmpty_(wp, 'H' + r,
          '=HYPERLINK("https://drive.google.com/drive/folders/' + pick.id +
          '";"' + prod + ' Set ' + pick.n + '")', true);
        if (!ok) continue;
        used[pick.id] = true;
        setIfEmpty_(wp, 'G' + r, 'claude', false);
        setIfEmpty_(wp, 'I' + r, pick.date, false);
        written.push('Winning Products!' + r + ' ' + prod + ' Set ' + pick.n);
      }
    }

    return written.length ? 'ok: ' + written.join(', ') : 'ok: nichts Neues';
  } finally {
    lock.releaseLock();
  }
}

// EINMAL im Editor ausfuehren: legt einen stuendlichen Trigger fuer fillFunnelSheet an.
function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'fillFunnelSheet') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('fillFunnelSheet').timeBased().everyHours(1).create();
}
