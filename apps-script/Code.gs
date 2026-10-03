// Apps-Script-Web-App in Jeannines Google-Konto ("Unbenanntes Projekt").
// Diese Datei ist die Quelle der Wahrheit fuer den Code im Script-Editor.
// 1) doPost: laedt ein Bild per URL in einen Drive-Ordner (Upload der Routine).
// 2) Nach JEDEM Upload: fillFunnelSheet() traegt L/N/O/P im Funnel Sheet ein.
// 3) Zusaetzlich stuendlicher Zeit-Trigger als Netz (einmalig installTrigger() ausfuehren).

const SHEET_ID = '1SkD7jrC-othtbwTYyz1VCK1HPIkEKHxc_hSAvRp2iL8';
const MARKETS = {
  FI:   '1Ey4aVRrpzrzolETnzKVxVCZQGZjm0P5K', // Translated-Ads/FI
  FRCA: '1ZeW7nKHrCMNOBH6jIKZrzNYjJWXPvQDW'  // Translated-Ads/FRCA
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
