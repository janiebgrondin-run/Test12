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
const FLIGHT_DUR   = '~10h 15min';

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
  //     Fonctionne uniquement quand l'avion est en vol (pas encore parti = aucun résultat)
  try {
    const icao = 'TSC691'; // Air Transat ICAO + numéro de vol
    const { data } = await axios.get(`https://api.adsb.fi/v1/callsign/${icao}`, { timeout: 8000 });
    if (data?.ac?.length > 0) {
      console.log('✅ Source: ADSB.fi (live ADS-B)');
      return buildFromADSB(data.ac[0]);
    }
    console.log('ℹ️  ADSB.fi: aucun vol TSC691 en cours (pas encore en vol)');
  } catch (e) { console.log('ADSB.fi erreur:', e.message); }

  // 3️⃣  Scheduled fallback (horaire estimé jusqu'au décollage)
  console.log('ℹ️  Utilisation de l\'horaire estimé');
  return mockFlight();
}

// Great-circle distance in km (haversine)
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 +
            Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) * Math.sin(dLon/2)**2;
  return R * 2 * Math.asin(Math.sqrt(a));
}

function buildFromADSB(ac) {
  const onGround = ac.alt_baro === 'ground' || !!ac.on_ground;
  const altFt    = typeof ac.alt_baro === 'number' ? ac.alt_baro : null;
  const speedKmh = ac.gs ? Math.round(ac.gs * 1.852) : null;

  // Compute dep/arr dynamically from live position + speed — no hardcoded times
  let depISO = null, arrISO = null;
  if (ac.lat && ac.lon && speedKmh && speedKmh > 200) {
    const remainingKm = haversine(ac.lat, ac.lon, 45.4706, -73.7408); // → YUL
    const traveledKm  = Math.max(0, DIST_KM - remainingKm);
    depISO = new Date(Date.now() - (traveledKm  / speedKmh) * 3600000).toISOString();
    arrISO = new Date(Date.now() + (remainingKm / speedKmh) * 3600000).toISOString();
  }

  return {
    flight_status: onGround ? 'landed' : 'active',
    departure: {
      airport: 'Athens International Airport "Eleftherios Venizelos"',
      iata: 'ATH', timezone: 'Europe/Athens',
      scheduled: depISO, actual: depISO
    },
    arrival: {
      airport: 'Montréal-Pierre Elliott Trudeau International Airport',
      iata: 'YUL', timezone: 'America/Toronto',
      scheduled: arrISO, estimated: arrISO
    },
    flight:   { iata: 'TS691', icao: 'TSC691', number: '691' },
    airline:  { name: 'Air Transat', iata: 'TS', icao: 'TSC' },
    aircraft: { registration: ac.r || 'C-GTSI', iata: ac.t || 'A332' },
    live: {
      latitude:    ac.lat   || null,
      longitude:   ac.lon   || null,
      altitude_ft: altFt,
      speed_kmh:   speedKmh,
      heading:     ac.track ? Math.round(ac.track) : null,
      source: 'adsb.fi'
    }
  };
}

function mockFlight() {
  // No hardcoded times — show "scheduled" with blank times until live API provides data
  return {
    flight_status: 'scheduled',
    departure: {
      airport: 'Athens International Airport "Eleftherios Venizelos"',
      iata: 'ATH', timezone: 'Europe/Athens',
      scheduled: null
    },
    arrival: {
      airport: 'Montréal-Pierre Elliott Trudeau International Airport',
      iata: 'YUL', timezone: 'America/Toronto',
      scheduled: null, estimated: null
    },
    flight:   { iata: 'TS691', icao: 'TSC691', number: '691' },
    airline:  { name: 'Air Transat', iata: 'TS', icao: 'TSC' },
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
  active_25: '✈️ En Route 1/4', active_50: '✈️ Mi-chemin 2/4',
  active_75: '✈️ En Route 3/4', active_95: '✈️ Approche 4/4',
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

    // Write public flight-data.json so the static HTML can read it from GitHub
    fs.writeFileSync(
      path.join(__dirname, 'flight-data.json'),
      JSON.stringify({ flight: f, lastUpdated: ts, source: process.env.AVIATION_API_KEY ? 'live' : 'demo' }, null, 2)
    );

    const status = f.flight_status;
    const eta = f.arrival?.estimated || f.arrival?.scheduled;
    const etaStr = fmtTime(eta);

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

    // 📍 En route position updates — 4 checkpoints (25 / 50 / 75 / 95 %)
    if (status === 'active') {
      const depMs  = new Date(depActual).getTime();
      const arrMs  = new Date(arrActual).getTime();
      const total  = arrMs - depMs;
      const elapsed = Date.now() - depMs;
      const pct    = total > 0 ? (elapsed / total) * 100 : 0;

      const checkpoints = [
        { key: 'active_25', threshold: 25, num: '1/4', label: 'Premier point de position' },
        { key: 'active_50', threshold: 50, num: '2/4', label: 'Mi-chemin — au-dessus de l\'Atlantique 🌊' },
        { key: 'active_75', threshold: 75, num: '3/4', label: 'Approche Canada' },
        { key: 'active_95', threshold: 95, num: '4/4', label: 'Arrivée imminente!' }
      ];

      for (const cp of checkpoints) {
        if (pct >= cp.threshold && !alreadySentToday(db, cp.key)) {
          const remaining = arrMs - Date.now();
          const remainStr = remaining > 0 ? formatDuration(remaining) : '~0min';

          const posLines = f.live?.altitude_ft
            ? [
                `📡 Altitude: ${f.live.altitude_ft.toLocaleString('fr-CA')} ft`,
                `💨 Vitesse: ${f.live.speed_kmh || '—'} km/h · Cap: ${f.live.heading || '—'}°`
              ]
            : [`📡 Position: données ADS-B non disponibles`];

          const cpMsg = [
            `✈️ ${PERSON_NAME} en route [${cp.num}] — ${cp.label}`,
            `━━━━━━━━━━━━━━━━━━━━`,
            `📍 Athens (ATH) → Montréal (YUL)`,
            `📊 Progression: ${Math.round(pct)}% du trajet`,
            ...posLines,
            `⏱ Temps restant: ~${remainStr}`,
            `🛬 Arrivée prévue MTL: ${etaMtlStr}`
          ].join('\n');

          let sent = false, error = null;
          try { await sendAlert(cpMsg); sent = true; console.log(`✅ Position [${cp.num}] envoyée`); }
          catch (e) { error = e.message; console.error(`❌ SMS position erreur: ${e.message}`); }

          db.alerts.unshift({
            id: String(Date.now()),
            timestamp: ts,
            status: cp.key,
            statusLabel: STATUS_LABELS[cp.key],
            flight: FLIGHT, phone: PHONE,
            message: cpMsg, sent, error
          });

          break; // one update per check cycle — next run handles the following stage
        }
      }
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

async function sendTestSMSAlert() {
  const f = readDB().flight || mockFlight();
  const dep = f.departure?.actual || f.departure?.scheduled;
  const arr = f.arrival?.estimated || f.arrival?.scheduled;
  const depLocalStr = fmtTime(dep, 'Europe/Athens');
  const etaMtlStr   = fmtTime(arr, 'America/Toronto');
  const durMs       = dep && arr ? new Date(arr) - new Date(dep) : null;
  const durStr      = durMs ? formatDuration(durMs) : FLIGHT_DUR;

  const msg = [
    `🔔 Vous êtes maintenant abonné au retour de Gabrielle à Montréal!`,
    `━━━━━━━━━━━━━━━━━━━━`,
    `✈️ Vol TS691 · Athens (ATH) → Montréal (YUL)`,
    `🕐 Départ Athènes: ${depLocalStr} (heure locale)`,
    `🛬 Arrivée prévue MTL: ${etaMtlStr}`,
    `📏 Distance: ${DIST_KM.toLocaleString('fr-CA')} km (${DIST_MI.toLocaleString('fr-CA')} mi)`,
    `⏱ Durée estimée: ${durStr}`,
    `━━━━━━━━━━━━━━━━━━━━`,
    `📱 Vous recevrez 8 alertes:`,
    `   🛫 Embarquement`,
    `   ✈️ En route (x4 mises à jour position)`,
    `   🏁 Atterrissage`,
    `   💋 Vous pouvez embrasser Gabrielle!`
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

  console.log(sent ? `✅ SMS test envoyé à ${PHONE}` : `❌ Erreur SMS test: ${error}`);
  return { success: true, sent, demo, error, message: msg };
}

app.post('/api/test-sms', async (req, res) => {
  const result = await sendTestSMSAlert();
  res.json(result);
});

module.exports = { checkFlight, sendTestSMSAlert };

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
