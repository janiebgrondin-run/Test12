require('dotenv').config();
const express = require('express');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const DB_FILE = path.join(__dirname, 'alerts.json');

const FLIGHT = process.env.FLIGHT_NUMBER || 'TS691';
const PHONE = process.env.ALERT_PHONE || '+14182627032';
const INTERVAL_MS = (parseFloat(process.env.CHECK_INTERVAL_HOURS) || 2) * 3600 * 1000;
const DEMO_MODE = process.env.DEMO_MODE === 'true';

// TS691 ATH → YUL flight constants
const PERSON_NAME  = 'Gabrielle';
const DIST_KM      = 7426;
const DIST_MI      = 4615;
const FLIGHT_DUR   = '~10h 30min';

// ── Database (JSON file) ─────────────────────────────────────────────────────

function readDB() {
  if (!fs.existsSync(DB_FILE)) return { alerts: [], lastCheck: null, flight: null };
  try { return JSON.parse(fs.readFileSync(DB_FILE)); } catch { return { alerts: [], lastCheck: null, flight: null }; }
}

function writeDB(data) {
  fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
}

// ── Flight data ──────────────────────────────────────────────────────────────

async function fetchFlight() {
  if (DEMO_MODE) return mockFlight();

  // 1️⃣  AviationStack — full schedule + status (free API key required)
  if (process.env.AVIATION_API_KEY) {
    try {
      const { data } = await axios.get('http://api.aviationstack.com/v1/flights', {
        params: { access_key: process.env.AVIATION_API_KEY, flight_iata: FLIGHT },
        timeout: 10000
      });
      if (data?.data?.[0]) { console.log('✅ Source: AviationStack (live)'); return data.data[0]; }
    } catch (e) { console.log('AviationStack erreur:', e.message); }
  }

  // 2️⃣  ADSB.fi — 100% gratuit, sans clé, données ADS-B en temps réel
  try {
    const icao = 'TSC691';
    const { data } = await axios.get(`https://api.adsb.fi/v1/callsign/${icao}`, { timeout: 8000 });
    if (data?.ac?.length > 0) {
      console.log('✅ Source: ADSB.fi (live ADS-B)');
      return buildFromADSB(data.ac[0]);
    }
    console.log('ℹ️  ADSB.fi: aucun vol TSC691 en cours (pas encore en vol)');
  } catch (e) { console.log('ADSB.fi erreur:', e.message); }

  // 3️⃣  Scheduled fallback
  console.log('ℹ️  Utilisation de l\'horaire estimé');
  return mockFlight();
}

function buildFromADSB(ac) {
  const onGround = ac.alt_baro === 'ground' || !!ac.on_ground;
  const altFt = typeof ac.alt_baro === 'number' ? ac.alt_baro : null;
  const now = Date.now();
  const depUTC = new Date(now); depUTC.setUTCHours(14, 0, 0, 0);
  if (depUTC.getTime() > now) depUTC.setUTCDate(depUTC.getUTCDate() - 1);
  const arrEstimate = new Date(depUTC.getTime() + 10.5 * 3600000).toISOString();
  return {
    flight_status: onGround ? 'landed' : 'active',
    departure: {
      airport: 'Athens International Airport "Eleftherios Venizelos"',
      iata: 'ATH', timezone: 'Europe/Athens',
      scheduled: new Date(depUTC).toISOString(), actual: new Date(depUTC).toISOString()
    },
    arrival: {
      airport: 'Montréal-Pierre Elliott Trudeau International Airport',
      iata: 'YUL', timezone: 'America/Toronto',
      scheduled: arrEstimate, estimated: arrEstimate
    },
    flight: { iata: 'TS691', icao: 'TSC691', number: '691' },
    airline: { name: 'Air Transat', iata: 'TS', icao: 'TSC' },
    aircraft: { registration: ac.r || 'C-GTSI', iata: ac.t || 'A332' },
    live: {
      latitude: ac.lat || null,
      longitude: ac.lon || null,
      altitude_ft: altFt,
      speed_kmh: ac.gs ? Math.round(ac.gs * 1.852) : null,
      heading: ac.track ? Math.round(ac.track) : null,
      source: 'adsb.fi'
    }
  };
}

function mockFlight() {
  const now = Date.now();
  const depUTC = new Date(now);
  depUTC.setUTCHours(14, 0, 0, 0);
  if (depUTC.getTime() < now) depUTC.setUTCDate(depUTC.getUTCDate() + 1);
  const depTime = depUTC.getTime();
  const arrTime = depTime + 10.5 * 3600000;
  return {
    flight_status: depTime - now < 3600000 ? 'boarding' : 'scheduled',
    departure: {
      airport: 'Athens International Airport "Eleftherios Venizelos"',
      iata: 'ATH', timezone: 'Europe/Athens',
      scheduled: new Date(depTime).toISOString()
    },
    arrival: {
      airport: 'Montréal-Pierre Elliott Trudeau International Airport',
      iata: 'YUL', timezone: 'America/Toronto',
      scheduled: new Date(arrTime).toISOString(),
      estimated: new Date(arrTime).toISOString()
    },
    flight: { iata: 'TS691', icao: 'TSC691', number: '691' },
    airline: { name: 'Air Transat', iata: 'TS', icao: 'TSC' },
    aircraft: { registration: 'C-GTSI', iata: 'A332', icao: 'A332' }
  };
}

// ── SMS / WhatsApp ───────────────────────────────────────────────────────────

async function sendAlert(message) {
  const sid = process.env.TWILIO_ACCOUNT_SID;
  const token = process.env.TWILIO_AUTH_TOKEN;
  const from = process.env.TWILIO_PHONE_NUMBER;

  if (!sid || !token || !from || DEMO_MODE) {
    console.log(`📵 [MODE DÉMO] SMS → ${PHONE}:\n${message}\n`);
    return { demo: true };
  }

  const client = require('twilio')(sid, token);
  const useWA = process.env.WHATSAPP_ENABLED === 'true';

  return client.messages.create({
    body: message,
    from: useWA ? `whatsapp:${from}` : from,
    to: useWA ? `whatsapp:${PHONE}` : PHONE
  });
}

// ── Status helpers ───────────────────────────────────────────────────────────

const STATUS_LABELS = {
  scheduled: 'Prévu', active: 'En Route', boarding: 'Embarquement',
  landed: 'Atterri', post_landed: '💋 Bisou!', cancelled: 'Annulé', diverted: 'Détourné', unknown: 'Inconnu'
};

function fmtTime(iso, tz = 'America/Toronto') {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('fr-CA', {
    timeZone: tz, hour: '2-digit', minute: '2-digit',
    day: 'numeric', month: 'short'
  });
}

function formatDuration(ms) {
  const totalMin = Math.round(ms / 60000);
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return `${h}h ${m.toString().padStart(2,'0')}min`;
}

function alreadySentToday(db, status) {
  const today = new Date().toDateString();
  return db.alerts.some(a => a.status === status && new Date(a.timestamp).toDateString() === today && a.sent);
}

// ── Core polling function ────────────────────────────────────────────────────

async function checkFlight() {
  const ts = new Date().toISOString();
  console.log(`\n[${ts}] 🔄 Vérification ${FLIGHT}...`);

  const db = readDB();
  db.lastCheck = ts;

  try {
    const f = await fetchFlight();
    db.flight = f;

    if (!f) { writeDB(db); console.log('Aucune donnée.'); return f; }

    fs.writeFileSync(
      path.join(__dirname, 'flight-data.json'),
      JSON.stringify({ flight: f, lastUpdated: ts, source: process.env.AVIATION_API_KEY ? 'live' : 'demo' }, null, 2)
    );

    const status = f.flight_status;
    const eta = f.arrival?.estimated || f.arrival?.scheduled;

    const depLocalStr  = fmtTime(f.departure?.actual || f.departure?.scheduled, 'Europe/Athens');
    const etaMtlStr    = fmtTime(eta, 'America/Toronto');
    const depActual    = f.departure?.actual || f.departure?.scheduled;
    const arrActual    = f.arrival?.actual || eta;
    const durationMs   = arrActual && depActual ? new Date(arrActual) - new Date(depActual) : null;
    const durStr       = durationMs ? formatDuration(durationMs) : FLIGHT_DUR;

    const ALERT_MESSAGES = {
      boarding: [
        `🛫 ${PERSON_NAME} embarque! Vol TS691`,
        `━━━━━━━━━━━━━━━━━━━━`,
        `📍 Athens (ATH) → Montréal (YUL)`,
        `🕐 Départ local Athènes: ${depLocalStr}`,
        `📏 Distance: ${DIST_KM.toLocaleString('fr-CA')} km (${DIST_MI.toLocaleString('fr-CA')} mi)`,
        `⏱ Durée estimée: ${FLIGHT_DUR}`,
        `🛬 Arrivée prévue MTL: ${etaMtlStr}`,
        `✈️ Air Transat · Airbus A330`
      ].join('\n'),

      active: [
        `✈️ ${PERSON_NAME} est en route! Vol TS691`,
        `━━━━━━━━━━━━━━━━━━━━`,
        `📍 Athens (ATH) → Montréal (YUL)`,
        `🕐 Partie d'Athènes: ${depLocalStr}`,
        `📏 Distance totale: ${DIST_KM.toLocaleString('fr-CA')} km`,
        `⏱ Durée de vol: ${durStr}`,
        `🛬 Arrivée prévue MTL: ${etaMtlStr}`,
        `✈️ Air Transat TS691`
      ].join('\n'),

      landed: [
        `🏁 ${PERSON_NAME} est arrivée à Montréal! 🎉`,
        `━━━━━━━━━━━━━━━━━━━━`,
        `📍 Athens → Montréal-Trudeau (YUL)`,
        `🛬 Atterrissage: ${fmtTime(f.arrival?.actual || eta, 'America/Toronto')}`,
        `📏 Distance parcourue: ${DIST_KM.toLocaleString('fr-CA')} km`,
        `⏱ Durée du vol: ${durStr}`,
        `🎉 Bienvenue à Montréal!`
      ].join('\n')
    };

    if (ALERT_MESSAGES[status] && !alreadySentToday(db, status)) {
      const msg = ALERT_MESSAGES[status];
      let sent = false, error = null;

      try { await sendAlert(msg); sent = true; console.log(`✅ Alerte envoyée: ${status}`); }
      catch (e) { error = e.message; console.error(`❌ SMS erreur: ${e.message}`); }

      db.alerts.unshift({
        id: String(Date.now()),
        timestamp: ts,
        status,
        statusLabel: STATUS_LABELS[status] || status,
        flight: FLIGHT,
        phone: PHONE,
        message: msg,
        sent,
        error
      });
    } else {
      console.log(`ℹ️  Statut: ${STATUS_LABELS[status] || status} — pas de nouvelle alerte`);
    }

    // 💋 Post-landing kiss alert — fires ~15 min after wheels down
    if (status === 'landed') {
      const arrISO = f.arrival?.actual || f.arrival?.estimated || f.arrival?.scheduled;
      const minsAfterLanding = arrISO ? (Date.now() - new Date(arrISO)) / 60000 : 0;
      if (minsAfterLanding >= 15 && !alreadySentToday(db, 'post_landed')) {
        const kissMsg = [
          `💋 Vous pouvez embrasser Gabrielle!`,
          `━━━━━━━━━━━━━━━━━━━━`,
          `✈️ Vol TS691 · Athens → Montréal`,
          `🛬 Atterrie depuis ~${Math.round(minsAfterLanding)} min`,
          `📍 Aéroport Montréal-Trudeau (YUL)`,
          `💕 Bienvenue à Montréal, Gabrielle!`
        ].join('\n');

        let sent = false, error = null;
        try { await sendAlert(kissMsg); sent = true; console.log('✅ Alerte bisou envoyée!'); }
        catch (e) { error = e.message; console.error(`❌ SMS bisou erreur: ${e.message}`); }

        db.alerts.unshift({
          id: String(Date.now()),
          timestamp: ts,
          status: 'post_landed',
          statusLabel: '💋 Bisou!',
          flight: FLIGHT,
          phone: PHONE,
          message: kissMsg,
          sent,
          error
        });
      }
    }

    writeDB(db);
    return f;
  } catch (err) {
    console.error('Erreur:', err.message);
    db.lastError = { timestamp: ts, message: err.message };
    writeDB(db);
    return null;
  }
}

// ── HTTP server ──────────────────────────────────────────────────────────────

app.use(express.json());
app.use(express.static(__dirname));

app.get('/api/status', (req, res) => {
  const db = readDB();
  res.json({
    flight: db.flight,
    lastCheck: db.lastCheck,
    lastError: db.lastError || null,
    alertCount: (db.alerts || []).length,
    config: { flightNumber: FLIGHT, phone: PHONE, intervalHours: INTERVAL_MS / 3600000, demo: DEMO_MODE }
  });
});

app.get('/api/alerts', (req, res) => {
  const db = readDB();
  res.json({ alerts: db.alerts || [] });
});

app.post('/api/check', async (req, res) => {
  const flight = await checkFlight();
  const db = readDB();
  res.json({ success: true, flight, lastCheck: db.lastCheck, alerts: db.alerts || [] });
});

// ── Trial / test SMS ─────────────────────────────────────────────────────────
app.post('/api/test-sms', async (req, res) => {
  const f = readDB().flight || mockFlight();
  const dep = f.departure?.actual || f.departure?.scheduled;
  const arr = f.arrival?.estimated || f.arrival?.scheduled;
  const depLocalStr = fmtTime(dep, 'Europe/Athens');
  const etaMtlStr   = fmtTime(arr, 'America/Toronto');
  const durMs       = dep && arr ? new Date(arr) - new Date(dep) : null;
  const durStr      = durMs ? formatDuration(durMs) : FLIGHT_DUR;

  const msg = [
    `✈️ TEST · ${PERSON_NAME} Vol TS691`,
    `━━━━━━━━━━━━━━━━━━━━`,
    `📍 Athens (ATH) → Montréal (YUL)`,
    `🕐 Départ Athènes: ${depLocalStr} (heure locale)`,
    `📏 Distance: ${DIST_KM.toLocaleString('fr-CA')} km (${DIST_MI.toLocaleString('fr-CA')} mi)`,
    `⏱ Durée estimée: ${durStr}`,
    `🛬 Arrivée prévue MTL: ${etaMtlStr}`,
    `✈️ Air Transat · Airbus A330`,
    `━━━━━━━━━━━━━━━━━━━━`,
    `🔔 Alertes: Embarquement · En Route · Atterri`
  ].join('\n');

  let sent = false, error = null, demo = false;
  try {
    const result = await sendAlert(msg);
    sent = true;
    demo = !!result?.demo;
  } catch (e) {
    error = e.message;
  }

  const db = readDB();
  db.alerts.unshift({
    id: String(Date.now()),
    timestamp: new Date().toISOString(),
    status: 'test',
    statusLabel: 'Test',
    flight: FLIGHT,
    phone: PHONE,
    message: msg,
    sent,
    error
  });
  writeDB(db);

  res.json({ success: true, sent, demo, error, message: msg });
});

module.exports = { checkFlight };

// Only start HTTP server when run directly (not via GitHub Actions require)
if (require.main === module) {
  app.listen(PORT, () => {
    const mode = DEMO_MODE ? ' [MODE DÉMO]' : '';
    console.log(`\n✈️  Vol Tracker TS691 démarré${mode}`);
    console.log(`📍 Interface:  http://localhost:${PORT}`);
    console.log(`📱 Alertes →  ${PHONE}`);
    console.log(`🔄 Intervalle: ${INTERVAL_MS / 3600000}h`);
    console.log(`💾 Base de données: ${DB_FILE}\n`);
    checkFlight();
    setInterval(checkFlight, INTERVAL_MS);
  });
}
