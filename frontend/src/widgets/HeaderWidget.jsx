import React from 'react';
import { Terminal, Database, Radio, Cpu, Layers } from 'lucide-react';

export function HeaderWidget({ isConnected }) {
  return (
    <header style={{
      borderBottom: '1px solid var(--border-main)',
      backgroundColor: 'var(--bg-surface)',
      padding: '14px 28px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }}>
      {/* Brand & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '6px',
          backgroundColor: 'var(--text-primary)',
          color: 'var(--bg-root)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: '700'
        }}>
          <Terminal size={18} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
              Command Center
            </h1>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', background: 'var(--bg-card)', padding: '2px 8px', borderRadius: '4px', border: '1px solid var(--border-main)', fontFamily: 'var(--font-mono)' }}>
              v1.0.0
            </span>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Autonomous Customer Success Multi-Agent AI Pipeline
          </p>
        </div>
      </div>

      {/* Infrastructure Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <Cpu size={14} color="var(--text-muted)" />
          <span>Gemini 3.1 Flash Lite</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <Database size={14} color="var(--text-muted)" />
          <span>pgvector</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <Layers size={14} color="var(--text-muted)" />
          <span>Kafka</span>
        </div>

        <div style={{ width: '1px', height: '16px', backgroundColor: 'var(--border-main)' }} />

        {/* Live Telemetry Status Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '4px 10px',
          borderRadius: '20px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-main)',
          fontSize: '11px',
          fontWeight: '500',
          color: isConnected ? 'var(--text-primary)' : 'var(--text-muted)'
        }}>
          <div style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: isConnected ? 'var(--accent-emerald)' : 'var(--accent-rose)'
          }} />
          <span>{isConnected ? 'STREAM CONNECTED' : 'DISCONNECTED'}</span>
        </div>
      </div>
    </header>
  );
}
