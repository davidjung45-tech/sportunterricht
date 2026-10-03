import { describe, it, expect } from 'vitest';
import { pruefeLizenz } from '../netlify/functions/lizenz.mjs';

const ENV = { DS_API_KEY: 'test', DS_PRODUKT_IDS: '111, 222' };
const fake = (data, result = 'success') => async (url) => {
  fake.letzteUrl = String(url);
  return { json: async () => ({ result, data }) };
};

describe('Lizenzprüfung (Digistore24 validateLicenseKey)', () => {
  it('schickt purchase_id und license_key wie in der offiziellen API', async () => {
    await pruefeLizenz({ bestellung: 'abc123', code: 'KEY-1234' }, ENV, fake({ is_license_valid: 'Y', product_id: 111 }));
    const u = new URL(fake.letzteUrl);
    expect(u.pathname).toBe('/api/call/validateLicenseKey');
    expect(u.searchParams.get('purchase_id')).toBe('ABC123');
    expect(u.searchParams.get('license_key')).toBe('KEY-1234');
  });
  it('akzeptiert gültige Schlüssel für freigegebene Produkte und liefert paid_until', async () => {
    const r = await pruefeLizenz({ bestellung: 'ABC123', code: 'KEY-1234' }, ENV, fake({ is_license_valid: 'Y', product_id: 222, paid_until: '2027-09-30' }));
    expect(r).toMatchObject({ gueltig: true, produkt: '222', bis: '2027-09-30' });
  });
  it('lehnt beendete Abos, falsche Produkte und unvollständige Eingaben ab', async () => {
    expect((await pruefeLizenz({ bestellung: 'ABC123', code: 'KEY-1234' }, ENV, fake({ is_license_valid: 'N', is_license_key_found: 'Y' }))).meldung).toMatch(/nicht mehr gültig/);
    expect((await pruefeLizenz({ bestellung: 'ABC123', code: 'KEY-1234' }, ENV, fake({ is_license_valid: 'Y', product_id: 999 }))).gueltig).toBe(false);
    expect((await pruefeLizenz({ bestellung: '', code: 'KEY-1234' }, ENV, fake({}))).gueltig).toBe(false);
  });
  it('meldet fehlende Einrichtung und Netzfehler, ohne Pro wegzunehmen', async () => {
    expect((await pruefeLizenz({ bestellung: 'ABC123', code: 'KEY-1234' }, {}, fake({}))).fehler).toBe('konfiguration');
    const kaputt = async () => { throw new Error('offline'); };
    expect((await pruefeLizenz({ bestellung: 'ABC123', code: 'KEY-1234' }, ENV, kaputt)).fehler).toBe('netz');
  });
});
