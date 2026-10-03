// Prüft einen Digistore24-Lizenzschlüssel serverseitig (der API-Schlüssel bleibt geheim).
//
// Offizielle API: GET https://www.digistore24.com/api/call/validateLicenseKey
//   Parameter:  purchase_id (Bestell-ID aus der Kaufbestätigung), license_key
//   Antwort:    data.is_license_valid = 'Y'|'N', data.product_id, data.paid_until (bei Abos), …
//   Doku:       https://digistore24.com/api/docs/paths/validateLicenseKey.yaml
//
// Einrichtung in Netlify unter „Site configuration → Environment variables“:
//   DS_API_KEY     = API-Schlüssel aus Digistore24 (Rechte: nur lesen)
//   DS_PRODUKT_IDS = kommagetrennte Produkt-IDs, die Pro freischalten (z. B. App-Pro-Jahr, -Monat, Praktikums-Pass, Komplettpaket)
//
// „is_license_valid“ wird von Digistore24 auf N gesetzt, wenn der Kauf erstattet oder ein Abo beendet wurde.

const JSON_KOPF = { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' };
const antwort = (daten, status = 200) => new Response(JSON.stringify(daten), { status, headers: JSON_KOPF });

export async function pruefeLizenz({ bestellung, code }, env = process.env, holen = fetch) {
  const b = String(bestellung || '').trim().toUpperCase();
  const k = String(code || '').trim();
  if (b.length < 4 || k.length < 6) return { gueltig: false, meldung: 'Bitte Bestellnummer und Lizenzschlüssel vollständig eingeben.' };
  if (!env.DS_API_KEY) return { gueltig: false, meldung: 'Die Freischaltung ist noch nicht eingerichtet. Bitte melde dich kurz per E-Mail.', fehler: 'konfiguration' };
  const erlaubt = String(env.DS_PRODUKT_IDS || '').split(',').map((s) => s.trim()).filter(Boolean);
  const url = new URL('https://www.digistore24.com/api/call/validateLicenseKey');
  url.searchParams.set('purchase_id', b);
  url.searchParams.set('license_key', k);
  let d;
  try {
    const r = await holen(url, { headers: { 'X-DS-API-KEY': env.DS_API_KEY, Accept: 'application/json' } });
    d = await r.json();
  } catch {
    return { gueltig: false, meldung: 'Digistore24 ist gerade nicht erreichbar. Bitte versuche es in ein paar Minuten noch einmal.', fehler: 'netz' };
  }
  const x = d?.data || {};
  if (d?.result !== 'success' || x.is_license_valid !== 'Y') {
    return { gueltig: false, meldung: x.is_license_key_found === 'Y' ? 'Dieser Schlüssel ist nicht mehr gültig (Abo beendet oder Kauf erstattet).' : 'Bestellnummer oder Schlüssel stimmen nicht. Bitte prüfe die Kaufbestätigung.' };
  }
  if (erlaubt.length && !erlaubt.includes(String(x.product_id))) {
    return { gueltig: false, meldung: 'Dieser Schlüssel gehört zu einem Produkt ohne App-Pro.' };
  }
  return { gueltig: true, produkt: String(x.product_id || ''), name: x.product_name || '', bis: x.paid_until || null };
}

export default async (req) => {
  if (req.method !== 'POST') return antwort({ gueltig: false, meldung: 'Nur POST erlaubt.' }, 405);
  const eingabe = await req.json().catch(() => ({}));
  return antwort(await pruefeLizenz(eingabe));
};
