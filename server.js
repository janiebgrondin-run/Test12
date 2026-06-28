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

const PERSON_NAME  = 'Gabrielle';
const DIST_KM      = 7426;
const DIST_MI      = 4615;
const FLIGHT_DUR   = '~10h 30min';

function readDB() {
  if (!fs.existsSync(DB_FILE)) return { alerts: [], lastCheck: null, flight: null };
  try { return JSON.parse(fs.readFileSync(DB_FILE)); } catch { return { alerts: [], lastCheck: null, flight: null }; }
}

function writeDB(data) {
  fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
}

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
  return {
    flight_status: 'active',
    departure: {
      airport: 'Athens International Airport',
      iata: 'ATH', timezone: 'Europe/Athens',
      scheduled: new Date(now - 5.5*3600000).toISOString(),
      actual: new Date(now - 5.4*3600000).toISOString()
    },
    arrival: {
      airport: 'Montréal-Pierre Elliott Trudeau International Airport',
      iata: 'YUL', timezone: 'America/Toronto',
      scheduled: new Date(now + 4.2*3600000).toISOString(),
      estimated: new Date(now + 4.0*3600000).toISOString()
    },
    flight: { iata: 'TS691', number: '691' },
    airline: { name: 'Air Transat', iata: 'TS' },
    aircraft: { registration: 'C-GTSI', iata: 'A332' }
  };
}

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

const STATUS_LABELS = {
  scheduled: 'Prévu', active: 'En Route', boarding: 'Embarquement',
  landed: 'Atterri', cancelled: 'Annulé', diverted: 'Détourné', unknown: 'Inconnu'
};

function fmtTime(iso, tz = 'America/Toronto') {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('fr-CA', {
    timeZone: tz, hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short'
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

async function checkFlight() {
  const ts = new Date().toISOString();
  console.log(`\n[${ts}] 🔄 Vérification ${FLIGHT}...`);
  const db = readDB();
  db.lastCheck = ts;
  try {
    const f = await fetchFlight();
    db.flight = f;
    if (!f) { writeDB(db); return f; }
    const status = f.flight_status;
    const eta = f.arrival?.estimated || f.arrival?.scheduled;
    const depLocalStr = fmtTime(f.departure?.actual || f.departure?.scheduled, 'Europe/Athens');
    const etaMtlStr   = fmtTime(eta, 'America/Toronto');
    const depActual   = f.departure?.actual || f.departure?.scheduled;
    const arrActual   = f.arrival?.actual || eta;
    const durationMs  = arrActual && depActual ? new Date(arrActual) - new Date(depActual) : null;
    const durStr      = durationMs ? formatDuration(durationMs) : FLIGHT_DUR;
    const ALERT_MESSAGES = {
      boarding: [`🛫 ${PERSON_NAME} embarque! Vol TS691`,`━━━━━━━━━━━━━━━━━━━━`,`📍 Athens (ATH) → Montréal (YUL)`,`🕐 Départ local Athènes: ${depLocalStr}`,`📏 Distance: ${DIST_KM.toLocaleString('fr-CA')} km (${DIST_MI.toLocaleString('fr-CA')} mi)`,`⏱ Durée estimée: ${FLIGHT_DUR}`,`🛬 Arrivée prévue MTL: ${etaMtlStr}`,`✈️ Air Transat · Airbus A330`].join('\n'),
      active:   [`✈️ ${PERSON_NAME} est en route! Vol TS691`,`━━━━━━━━━━━━━━━━━━━━`,`📍 Athens (ATH) → Montréal (YUL)`,`🕐 Partie d'Athènes: ${depLocalStr}`,`📏 Distance totale: ${DIST_KM.toLocaleString('fr-CA')} km`,`⏱ Durée de vol: ${durStr}`,`🛬 Arrivée prévue MTL: ${etaMtlStr}`,`✈️ Air Transat TS691`].join('\n'),
      landed:   [`🏁 ${PERSON_NAME} est arrivée à Montréal! 🎉`,`━━━━━━━━━━━━━━━━━━━━`,`📍 Athens → Montréal-Trudeau (YUL)`,`🛬 Atterrissage: ${fmtTime(f.arrival?.actual || eta, 'America/Toronto')}`,`📏 Distance parcourue: ${DIST_KM.toLocaleString('fr-CA')} km`,`⏱ Durée du vol: ${durStr}`,`🎉 Bienvenue à Montréal!`].join('\n')
    };
    if (ALERT_MESSAGES[status] && !alreadySentToday(db, status)) {
      const msg = ALERT_MESSAGES[status];
      let sent = false, error = null;
      try { await sendAlert(msg); sent = true; console.log(`✅ Alerte envoyée: ${status}`); }
      catch (e) { error = e.message; console.error(`❌ SMS erreur: ${e.message}`); }
      db.alerts.unshift({ id: String(Date.now()), timestamp: ts, status, statusLabel: STATUS_LABELS[status] || status, flight: FLIGHT, phone: PHONE, message: msg, sent, error });
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

module.exports = { checkFlight };

if (require.main === module) {
  app.use(express.json());
  app.use(express.static(__dirname));
  app.listen(PORT, () => {
    console.log(`\n✈️  Vol Tracker TS691 démarré`);
    console.log(`📍 Interface:  http://localhost:${PORT}`);
    checkFlight();
    setInterval(checkFlight, INTERVAL_MS);
  });
}
