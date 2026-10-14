// Apps-Script-Web-App in Jeannines Google-Konto ("Unbenanntes Projekt").
// Diese Datei ist die Quelle der Wahrheit fuer den Code im Script-Editor.
// 1) doPost: laedt ein Bild per URL in einen Drive-Ordner (Upload der Routine).
// 2) Nach JEDEM Upload: fillFunnelSheet() traegt L/N/O/P im Funnel Sheet ein.
// 3) Zusaetzlich stuendlicher Zeit-Trigger als Netz (einmalig installTrigger() ausfuehren).
//
// WICHTIG, Fehlerbehebung 2026-10-14 (von Jeannine gemeldet):
// Die alte Fassung hat die Zeilen ALLEIN ueber den Produktnamen in Spalte G gesucht.
// Dadurch bekam JEDE Zeile mit demselben Namen den Ordner-Link, auch eine Zeile, die
// nie bearbeitet wurde und in Spalte M gar keine Quelle stehen hat. Beobachtet an
// FI!123 (smokola): die Zeile hat kein M, trotzdem standen dort L/N/O/P aus einem
// alten "Smokola"-Ordner einer frueheren Zeile. Siehe docs/sheet-writeback-SOP.md.
//
// Neue Regel: Eine Zeile wird NUR noch beschrieben, wenn die Routine fuer genau diese
// Zeile hochgeladen hat. Die Routine meldet die Zeile beim Upload im Feld "row"
// (z. B. "FI!120" oder "NL/BE new!3"). Es wird nie mehr ueber den Namen geraten.

const SHEET_ID = '1SkD7jrC-othtbwTYyz1VCK1HPIkEKHxc_hSAvRp2iL8';
const REGISTRY_KEY = 'claude_row_registry_v1';

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function registry_() {
  const raw = PropertiesService.getScriptProperties().getProperty(REGISTRY_KEY);
  if (!raw) return {};
  try { return JSON.parse(raw); } catch (err) { return {}; }
}

function registryPut_(rowRef, folderId) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const reg = registry_();
    reg[rowRef] = { folderId: folderId, ts: new Date().toISOString() };
    PropertiesService.getScriptProperties()
      .setProperty(REGISTRY_KEY, JSON.stringify(reg));
  } finally {
    lock.releaseLock();
  }
}

function doPost(e) {
  const req = JSON.parse(e.postData.contents);
  if (req.action === 'fill') {
    return json_({ sheet: fillFunnelSheet() });
  }
  // Nachtragen einer Zeile, die schon hochgeladen wurde, bevor dieses Script deployed war.
  // {"action":"register","row":"NL/BE new!3","folderId":"<Ordner-ID>"}
  if (req.action === 'register') {
    registryPut_(String(req.row), String(req.folderId));
    return json_({ registered: req.row, sheet: fillFunnelSheet() });
  }
  // Falsche Eintragung entfernen: {"action":"clear","rows":["FI!123"]}
  // Loescht L/N/O/P und nimmt die Zeile aus der Registry, damit sie nicht wiederkommt.
  if (req.action === 'clear') {
    const rows = req.rows || (req.row ? [req.row] : []);
    clearRows_(rows);
    return json_({ cleared: rows });
  }
  const folder = DriveApp.getFolderById(req.folderId);
  const blob = UrlFetchApp.fetch(req.url).getBlob().setName(req.name);
  const file = folder.createFile(blob);
  // Die Routine meldet hier, zu WELCHER Sheet-Zeile dieser Upload gehoert.
  // Ohne "row" wird nichts ins Sheet geschrieben - lieber keine Eintragung als eine falsche.
  if (req.row) {
    try { registryPut_(String(req.row), req.folderId); } catch (err) {}
  }
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

// Traegt L/N/O/P NUR fuer die Zeilen ein, die die Routine beim Upload gemeldet hat.
// Kein Raten ueber den Produktnamen mehr - siehe Kopfkommentar.
function fillFunnelSheet() {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const reg = registry_();
    const written = [];
    const skipped = [];
    Object.keys(reg).forEach(function (rowRef) {
      const m = String(rowRef).match(/^(.+)!(\d+)$/);
      if (!m) { skipped.push(rowRef + ' (Format)'); return; }
      const sh = ss.getSheetByName(m[1]);
      if (!sh) { skipped.push(rowRef + ' (Tab fehlt)'); return; }
      const r = Number(m[2]);
      if (r < 2 || r > sh.getMaxRows()) { skipped.push(rowRef + ' (Zeile)'); return; }
      const name = String(sh.getRange('G' + r).getValue() || '').trim();
      if (!name) { skipped.push(rowRef + ' (G leer)'); return; }
      const hit = reg[rowRef];
      const o = setIfEmpty_(sh, 'O' + r,
        '=HYPERLINK("https://drive.google.com/drive/folders/' + hit.folderId + '";"' + name + '")', true);
      setIfEmpty_(sh, 'L' + r, new Date(hit.ts), false);
      setIfEmpty_(sh, 'N' + r, 'claude', false);
      setIfEmpty_(sh, 'P' + r, 'in progress', false);
      if (o) written.push(rowRef + ' ' + name);
    });
    let out = written.length ? 'ok: ' + written.join(', ') : 'ok: nichts Neues';
    if (skipped.length) out += ' | uebersprungen: ' + skipped.join(', ');
    return out;
  } finally {
    lock.releaseLock();
  }
}

// Per Endpoint ({"action":"clear","rows":[...]}) oder einmal im Editor ausfuehrbar.
// Loescht L/N/O/P in genau den angegebenen Zeilen und nimmt sie aus der Registry.
// Beispiel: clearRows_(['FI!123']);
function clearRows_(rowRefs) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const reg = registry_();
  rowRefs.forEach(function (rowRef) {
    const m = String(rowRef).match(/^(.+)!(\d+)$/);
    if (!m) return;
    const sh = ss.getSheetByName(m[1]);
    if (!sh) return;
    ['L', 'N', 'O', 'P'].forEach(function (col) {
      sh.getRange(col + m[2]).clearContent();
    });
    delete reg[rowRef];
  });
  PropertiesService.getScriptProperties()
    .setProperty(REGISTRY_KEY, JSON.stringify(reg));
}

// EINMAL im Editor ausfuehren: legt einen stuendlichen Trigger fuer fillFunnelSheet an.
function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'fillFunnelSheet') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('fillFunnelSheet').timeBased().everyHours(1).create();
}
