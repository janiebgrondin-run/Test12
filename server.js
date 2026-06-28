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

const PERSON_NAME = 'Gabrielle';
const DIST_KM     = 7426;
const DIST_MI     = 4615;
const FLIGHT_DUR  = '~10h 30min';

function readDB() {
  if (!fs.existsSync(DB_FILE)) return { alerts: [], lastCheck: null, flight: null };
  try { return JSON.parse(fs.readFileSync(DB_FILE)); } catch { return { alerts: [], lastCheck: null, flight: null }; }
}
function writeDB(data) { fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2)); }

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
  // TS691: departs Athens ~17h00 local (14h00 UTC), arrives MTL ~00h30 next day
  const depUTC = new Date(now);
  depUTC.setUTCHours(14, 0, 0, 0);
  if (depUTC.getTime() < now) depUTC.setUTCDate(depUTC.getUTCDate() + 1);
  const depTime = depUTC.getTime();
  const arrTime = depTime + 10.5 * 3600000;
  return {
    flight_status: (depTime - now) < 3600000 ? 'boarding' : 'scheduled',
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

async function sendAlert(message) {
  const sid = process.env.TWILIO_ACCOUNT_SID, token = process.env.TWILIO_AUTH_TOKEN, from = process.env.TWILIO_PHONE_NUMBER;
  if (!sid || !token || !from || DEMO_MODE) { console.log(`\u📵 [DÉMO] SMS → ${PHONE}:\n${message}\n`); return { demo: true }; }
  const client = require('twilio')(sid, token);
  const useWA = process.env.WHATSAPP_ENABLED === 'true';
  return client.messages.create({ body: message, from: useWA ? `whatsapp:${from}` : from, to: useWA ? `whatsapp:${PHONE}` : PHONE });
}

const STATUS_LABELS = { scheduled:'Prévu', active:'En Route', boarding:'Embarquement', landed:'Atterri', cancelled:'Annulé', diverted:'Détourné', unknown:'Inconnu' };

function fmtTime(iso, tz = 'America/Toronto') {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('fr-CA', { timeZone: tz, hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' });
}
function formatDuration(ms) {
  const m = Math.round(ms/60000), h = Math.floor(m/60);
  return `${h}h ${(m%60).toString().padStart(2,'0')}min`;
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

    fs.writeFileSync(path.join(__dirname, 'flight-data.json'),
      JSON.stringify({ flight: f, lastUpdated: ts, source: process.env.AVIATION_API_KEY ? 'live' : 'demo' }, null, 2));

    const status = f.flight_status;
    const eta = f.arrival?.estimated || f.arrival?.scheduled;
    const depLocalStr = fmtTime(f.departure?.actual || f.departure?.scheduled, 'Europe/Athens');
    const etaMtlStr   = fmtTime(eta, 'America/Toronto');
    const depActual   = f.departure?.actual || f.departure?.scheduled;
    const durationMs  = depActual && (f.arrival?.actual || eta) ? new Date(f.arrival?.actual || eta) - new Date(depActual) : null;
    const durStr      = durationMs ? formatDuration(durationMs) : FLIGHT_DUR;

    const MSGS = {
      boarding: [`🛫 ${PERSON_NAME} embarque! Vol TS691`,`━━━━━━━━━━━━━━━━━━━━`,`📍 Athens (ATH) → Montréal (YUL)`,`🕐 Départ Athènes: ${depLocalStr}`,`📏 Distance: ${DIST_KM.toLocaleString('fr-CA')} km`,`⏱ Durée estimée: ${FLIGHT_DUR}`,`🛬 Arrivée prévue MTL: ${etaMtlStr}`,`✈️ Air Transat · Airbus A330`].join('\n'),
      active:   [`✈️ ${PERSON_NAME} est en route! Vol TS691`,`━━━━━━━━━━━━━━━━━━━━`,`📍 Athens (ATH) → Montréal (YUL)`,`🕐 Partie d'Athènes: ${depLocalStr}`,`📏 Distance totale: ${DIST_KM.toLocaleString('fr-CA')} km`,`⏱ Durée de vol: ${durStr}`,`🛬 Arrivée prévue MTL: ${etaMtlStr}`,`✈️ Air Transat TS691`].join('\n'),
      landed:   [`🏁 ${PERSON_NAME} est arrivée à Montréal! 🎉`,`━━━━━━━━━━━━━━━━━━━━`,`📍 Athens → Montréal-Trudeau (YUL)`,`🛬 Atterrissage: ${fmtTime(f.arrival?.actual || eta, 'America/Toronto')}`,`📏 Distance parcourue: ${DIST_KM.toLocaleString('fr-CA')} km`,`⏱ Durée du vol: ${durStr}`,`🎉 Bienvenue à Montréal!`].join('\n')
    };

    if (MSGS[status] && !alreadySentToday(db, status)) {
      let sent = false, error = null;
      try { await sendAlert(MSGS[status]); sent = true; } catch (e) { error = e.message; }
      db.alerts.unshift({ id: String(Date.now()), timestamp: ts, status, statusLabel: STATUS_LABELS[status]||status, flight: FLIGHT, phone: PHONE, message: MSGS[status], sent, error });
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
  app.get('/api/status', (req, res) => { const db = readDB(); res.json({ flight: db.flight, lastCheck: db.lastCheck, config: { flightNumber: FLIGHT, phone: PHONE, intervalHours: INTERVAL_MS/3600000, demo: DEMO_MODE } }); });
  app.get('/api/alerts', (req, res) => { const db = readDB(); res.json({ alerts: db.alerts||[] }); });
  app.post('/api/check', async (req, res) => { const f = await checkFlight(); const db = readDB(); res.json({ success:true, flight:f, lastCheck:db.lastCheck, alerts:db.alerts||[] }); });
  app.listen(PORT, () => { console.log(`\n✈️  Vol Tracker TS691\n📍 http://localhost:${PORT}\n`); checkFlight(); setInterval(checkFlight, INTERVAL_MS); });
}
