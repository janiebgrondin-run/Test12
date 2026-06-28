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
  if (DEMO_MODE || !process.env.AVIATION_API_KEY) return mockFlight();
  const { data } = await axios.get('http://api.aviationstack.com/v1/flights', {
    params: { access_key: process.env.AVIATION_API_KEY, flight_iata: FLIGHT },
    timeout: 10000
  });
  return data?.data?.[0] || null;
}

function mockFlight() {
  const now = Date.now();
  const depOffset = 5.5 * 3600000;
  const arrOffset = 4.2 * 3600000;
  return {
    flight_status: 'active',
    departure: {
      airport: 'Athens International Airport "Eleftherios Venizelos"',
      iata: 'ATH',
      timezone: 'Europe/Athens',
      scheduled: new Date(now - depOffset).toISOString(),
      actual: new Date(now - depOffset + 900000).toISOString()
    },
    arrival: {
      airport: 'Montréal-Pierre Elliott Trudeau International Airport',
      iata: 'YUL',
      timezone: 'America/Toronto',
      scheduled: new Date(now + arrOffset).toISOString(),
      estimated: new Date(now + arrOffset - 600000).toISOString()
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
  landed: 'Atterri', cancelled: 'Annulé', diverted: 'Détourné', unknown: 'Inconnu'
};

function fmtTime(iso, tz = 'America/Toronto') {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('fr-CA', {
    timeZone: tz, hour: '2-digit', minute: '2-digit',
    day: 'numeric', month: 'short'
  });
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

    const status = f.flight_status;
    const eta = f.arrival?.estimated || f.arrival?.scheduled;
    const etaStr = fmtTime(eta);

    const ALERT_MESSAGES = {
      boarding: `🛫 TS691 | Embarquement!\nAthen → Montréal\nArrivée prévue: ${etaStr} (MTL)\n📍 Aéroport d'Athènes`,
      active:   `✈️ TS691 | En route!\nAthen → Montréal\nArrivée prévue: ${etaStr} (MTL)`,
      landed:   `🏁 TS691 | Atterri à Montréal!\nBienvenue! 🎉\nHeure: ${fmtTime(f.arrival?.actual || eta)}`
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

module.exports = { checkFlight };
