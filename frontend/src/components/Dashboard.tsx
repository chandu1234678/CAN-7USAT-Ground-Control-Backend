import { useEffect, useState } from 'react';
import { useTelemetryStore } from '../stores/telemetryStore';
import { TelemetryChart } from './TelemetryChart';
import './Dashboard.css';

const WS_URL = 'ws://localhost:8000/ws/telemetry';

const STATES = ['PRE-LAUNCH','LAUNCH','ASCENT','APOGEE','DESCENT','LANDED','RECOVERY'];

export const Dashboard = () => {
  const { connected, latestPacket, altitudeHistory, velocityHistory,
          packetsReceived, maxAltitude, connect, disconnect } = useTelemetryStore();

  const [uptime, setUptime] = useState(0);
  const [armed, setArmed] = useState(false);

  useEffect(() => {
    connect(WS_URL);
    return () => disconnect();
  }, [connect, disconnect]);
  useEffect(() => {
    const t = setInterval(() => setUptime(p => p + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const hms = (s: number) => {
    const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), ss = s%60;
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(ss).padStart(2,'0')}`;
  };

  const fmsFlight = (ms: number) => {
    const s = Math.floor(ms/1000), m = Math.floor(s/60), ss = s%60;
    return `00:${String(m).padStart(2,'0')}:${String(ss).padStart(2,'0')}`;
  };

  const hz = altitudeHistory.length > 1
    ? (10 / ((altitudeHistory.at(-1)?.time ?? 0) - (altitudeHistory.at(-11)?.time ?? 0) || 1))
    : 0;

  const curState = latestPacket?.flight_state_name?.toUpperCase() ?? 'LANDED';
  const curIdx   = STATES.findIndex(s => s === curState);

  return (
    <div className="gcs">
      {/* ── HEADER ── */}
      <header className="gcs-header">
        <div className="gcs-header-left">
          <span style={{fontSize:'1.6rem'}}>🚀</span>
          <div>
            <h1>CanSat Ground Control</h1>
            <p>CAN-7USAT Mission Control (Arial)</p>
          </div>
        </div>
        <div className="gcs-header-right">
          <div className={`hbadge ${connected ? 'ok' : 'fail'}`}>
            <span className="hbadge-lbl">TELEMETRY</span>
            <span className="hbadge-val">{connected ? 'ACTIVE' : 'INACTIVE'}</span>
          </div>
          <div className="hbadge">
            <span className="hbadge-lbl">PACKETS</span>
            <span className="hbadge-val">{packetsReceived}</span>
          </div>
          <div className="hbadge">
            <span className="hbadge-lbl">RATE</span>
            <span className="hbadge-val">{hz.toFixed(0)} Hz</span>
          </div>
          <div className="hbadge">
            <span className="hbadge-lbl">UPTIME</span>
            <span className="hbadge-val">{hms(uptime)}</span>
          </div>
        </div>
      </header>

      {/* ── BODY ── */}
      <div className="gcs-body">

        {/* ── LEFT ── */}
        <div className="col-left">
          {/* Flight State */}
          <div className="panel p-flight">
            <div className="panel-hdr">Flight State Panel</div>
            <div className="panel-body">
              <div className="fs-box">{curState}</div>
              <ul className="fs-list">
                {STATES.map((s, i) => (
                  <li key={s} className={i <= curIdx ? 'on' : ''}>
                    <span className="fs-dot"/>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Vehicle Status */}
          <div className="panel p-vstatus">
            <div className="panel-hdr">Vehicle Status</div>
            <div className="panel-body" style={{padding:0}}>
              <div className="vstatus-grid">
                <div className="vs-cell">
                  <span className="vs-lbl">VEHICLE ARM/SAFE</span>
                  <span className={`vs-val ${armed ? 'armed' : 'safe'}`}>{armed ? 'ARMED' : 'SAFE'}</span>
                </div>
                <div className="vs-cell">
                  <span className="vs-lbl">POWER</span>
                  <span className="vs-val nominal">NOMINAL</span>
                </div>
                <div className="vs-cell">
                  <span className="vs-lbl">DROGUE</span>
                  <span className="vs-val">DEPLOYED</span>
                </div>
                <div className="vs-cell">
                  <span className="vs-lbl">MAIN</span>
                  <span className="vs-val">DEPLOYED</span>
                </div>
              </div>
            </div>
          </div>

          {/* Command & Control */}
          <div className="panel p-cmd">
            <div className="panel-hdr">Command & Control</div>
            <div className="panel-body">
              <div className="cmd-btns">
                <button className={`cbtn ${armed ? 'disarm' : 'arm'}`} onClick={() => setArmed(!armed)}>
                  {armed ? 'DISARM VEHICLE' : 'ARM VEHICLE'}
                </button>
                <button className="cbtn" disabled={!armed}>MANUAL DEPLOY</button>
                <button className="cbtn">ABORT</button>
                <button className="cbtn">RESET</button>
              </div>
            </div>
          </div>

          {/* GPS */}
          <div className="panel p-gps">
            <div className="panel-hdr">GPS Position</div>
            <div className="panel-body">
              <div className="gps-row">
                <span className="gps-lbl">Lat</span>
                <span className="gps-val">{latestPacket?.gps_lat.toFixed(4) ?? '34.0522'} N</span>
              </div>
              <div className="gps-row">
                <span className="gps-lbl">Long</span>
                <span className="gps-val">{latestPacket?.gps_lon.toFixed(4) ?? '118.2437'} W</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── CENTER ── */}
        <div className="col-center">
          {/* Primary Telemetry */}
          <div className="panel p-telem">
            <div className="panel-hdr">Primary Telemetry</div>
            <div className="panel-body" style={{padding:0}}>
              <div className="telem-grid">
                <div className="tc">
                  <span className="tc-lbl">Altitude</span>
                  <span className="tc-val">{latestPacket?.altitude_m.toFixed(0) ?? '1250'} m</span>
                </div>
                <div className="tc">
                  <span className="tc-lbl">Velocity</span>
                  <span className="tc-val">{latestPacket?.velocity_ms.toFixed(0) ?? '45'} m/s</span>
                </div>
                <div className="tc">
                  <span className="tc-lbl">Max Alt</span>
                  <span className="tc-val">{maxAltitude.toFixed(0)} m</span>
                </div>
                <div className="tc">
                  <span className="tc-lbl">Flight Time</span>
                  <span className="tc-val">{latestPacket ? fmsFlight(latestPacket.timestamp_ms) : '00:12:45'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Altitude Chart */}
          <div className="panel p-chart">
            <div className="panel-hdr">Altitude Profile</div>
            <div className="panel-body chart-wrap">
              <TelemetryChart data={altitudeHistory} title="" color="#000" unit="m" height={160}/>
            </div>
          </div>

          {/* Velocity Chart */}
          <div className="panel p-chart">
            <div className="panel-hdr">Velocity Profile</div>
            <div className="panel-body chart-wrap">
              <TelemetryChart data={velocityHistory} title="" color="#000" unit="m/s" height={160}/>
            </div>
          </div>
        </div>

        {/* ── RIGHT ── */}
        <div className="col-right">
          {/* Vehicle Orientation - Exact Stitch Rocket */}
          <div className="panel p-orient">
            <div className="panel-hdr">Vehicle Orientation</div>
            <div className="panel-body" style={{padding:0}}>
              <div className="rocket-wrap">
                <svg className="rocket-svg" viewBox="0 0 200 260" preserveAspectRatio="xMidYMid meet">
                  {/* Dark teal background */}
                  <rect width="200" height="260" fill="#001c1c"/>
                  {/* Grid */}
                  <defs>
                    <pattern id="g" width="16" height="16" patternUnits="userSpaceOnUse">
                      <path d="M16 0L0 0 0 16" fill="none" stroke="#0a3030" strokeWidth="0.6"/>
                    </pattern>
                  </defs>
                  <rect width="200" height="260" fill="url(#g)"/>

                  {/* ── ROCKET BODY (centered at x=80) ── */}
                  {/* Nose cone */}
                  <polygon points="68,20 92,20 80,5" fill="none" stroke="#00e5ff" strokeWidth="1.8"/>

                  {/* Upper body */}
                  <rect x="68" y="20" width="24" height="20" fill="none" stroke="#00e5ff" strokeWidth="1.8"/>

                  {/* Recovery bay */}
                  <rect x="68" y="40" width="24" height="30" fill="none" stroke="#00e5ff" strokeWidth="1.8"/>
                  {/* cross-hatch inside recovery */}
                  <line x1="68" y1="50" x2="92" y2="50" stroke="#00e5ff" strokeWidth="0.8" strokeDasharray="3,2"/>
                  <line x1="68" y1="60" x2="92" y2="60" stroke="#00e5ff" strokeWidth="0.8" strokeDasharray="3,2"/>

                  {/* Avionics bay */}
                  <rect x="68" y="70" width="24" height="30" fill="none" stroke="#00e5ff" strokeWidth="1.8"/>
                  <line x1="68" y1="80" x2="92" y2="80" stroke="#00e5ff" strokeWidth="0.8" strokeDasharray="3,2"/>
                  <line x1="68" y1="90" x2="92" y2="90" stroke="#00e5ff" strokeWidth="0.8" strokeDasharray="3,2"/>

                  {/* Payload bay */}
                  <rect x="68" y="100" width="24" height="35" fill="none" stroke="#00e5ff" strokeWidth="1.8"/>
                  <line x1="68" y1="112" x2="92" y2="112" stroke="#00e5ff" strokeWidth="0.8" strokeDasharray="3,2"/>
                  <line x1="68" y1="124" x2="92" y2="124" stroke="#00e5ff" strokeWidth="0.8" strokeDasharray="3,2"/>

                  {/* Engine section */}
                  <rect x="70" y="135" width="20" height="25" fill="none" stroke="#00e5ff" strokeWidth="1.8"/>

                  {/* Fins */}
                  <polygon points="68,145 56,165 68,165" fill="none" stroke="#00e5ff" strokeWidth="1.8"/>
                  <polygon points="92,145 104,165 92,165" fill="none" stroke="#00e5ff" strokeWidth="1.8"/>

                  {/* Nozzle */}
                  <polygon points="72,160 88,160 85,170 75,170" fill="none" stroke="#00e5ff" strokeWidth="1.8"/>

                  {/* ── LABELS ── */}
                  <text x="100" y="14"  fill="#00e5ff" fontSize="9" fontFamily="Arial">NOSE</text>
                  <text x="100" y="58"  fill="#00e5ff" fontSize="9" fontFamily="Arial">RECOVERY</text>
                  <text x="100" y="88"  fill="#00e5ff" fontSize="9" fontFamily="Arial">AVIONICS</text>
                  <text x="100" y="120" fill="#00e5ff" fontSize="9" fontFamily="Arial">PAYLOAD</text>
                  <text x="100" y="152" fill="#00e5ff" fontSize="9" fontFamily="Arial">ENGINE/FINS</text>

                  {/* Connector lines from labels to rocket */}
                  <line x1="98" y1="12"  x2="92" y2="12"  stroke="#00e5ff" strokeWidth="0.8"/>
                  <line x1="98" y1="56"  x2="92" y2="56"  stroke="#00e5ff" strokeWidth="0.8"/>
                  <line x1="98" y1="86"  x2="92" y2="86"  stroke="#00e5ff" strokeWidth="0.8"/>
                  <line x1="98" y1="118" x2="92" y2="118" stroke="#00e5ff" strokeWidth="0.8"/>
                  <line x1="98" y1="150" x2="92" y2="150" stroke="#00e5ff" strokeWidth="0.8"/>
                </svg>
              </div>
            </div>
          </div>

          {/* Quaternion */}
          <div className="panel p-quat">
            <div className="panel-hdr">Quaternion Panel</div>
            <div className="panel-body" style={{padding:0}}>
              <div className="quat-grid">
                {(['quat_w','quat_x','quat_y','quat_z'] as const).map((k, i) => (
                  <div className="qc" key={k}>
                    <span className="qc-lbl">{['W','X','Y','Z'][i]}</span>
                    <span className="qc-val">{latestPacket?.[k].toFixed(4) ?? '0.0000'}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* System Diagnostics */}
          <div className="panel p-diag">
            <div className="panel-hdr">System Diagnostics</div>
            <div className="panel-body">
              <ul className="diag-list">
                {[
                  ['IMU Status',   'NOMINAL'],
                  ['GPS Status',   'NOMINAL'],
                  ['Radio Status', 'NOMINAL'],
                  ['Power Status', 'NOMINAL'],
                ].map(([name, val]) => (
                  <li key={name}>
                    <span className="d-dot"/>
                    {name}:
                    <strong>{val}</strong>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
