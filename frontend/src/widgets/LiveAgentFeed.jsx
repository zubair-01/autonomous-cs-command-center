import React from 'react';
import { Bot, Database, Search, Edit3, Activity, ArrowRight } from 'lucide-react';

const NODE_ICONS = {
  RouterAgent: Bot,
  SQLAgent: Database,
  RAGAgent: Search,
  DraftAgent: Edit3,
};

export function LiveAgentFeed({ events }) {
  return (
    <div className="mono-card" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid var(--border-main)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={16} color="var(--text-primary)" />
          <h2 style={{ fontSize: '13px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-primary)' }}>
            Real-Time Agent Telemetry
          </h2>
        </div>
        <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          {events.length} trace events
        </span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
            <p style={{ fontSize: '13px', fontWeight: '500' }}>No active telemetry streams</p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Events will appear as multi-agent pipelines process tickets.
            </p>
          </div>
        ) : (
          events.map((ev, index) => {
            const IconComponent = NODE_ICONS[ev.node_name] || Bot;

            return (
              <div
                key={index}
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-main)',
                  borderRadius: '8px',
                  padding: '12px 14px',
                  display: 'flex',
                  gap: '12px',
                  alignItems: 'flex-start'
                }}
              >
                <div style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '6px',
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-main)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: '2px'
                }}>
                  <IconComponent size={15} color="var(--text-primary)" />
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        STEP {ev.step_index}
                      </span>
                      <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
                        {ev.node_name}
                      </span>
                    </div>
                    <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    {ev.action_type}
                  </p>

                  <div style={{
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-muted)',
                    backgroundColor: 'var(--bg-root)',
                    padding: '6px 10px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-main)',
                    marginTop: '6px'
                  }}>
                    {ev.details}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
