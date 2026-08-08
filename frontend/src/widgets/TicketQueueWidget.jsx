import React from 'react';
import { Ticket, Plus } from 'lucide-react';

export function TicketQueueWidget({ tickets, selectedTicketId, onSelectTicket, onOpenSubmitModal }) {
  return (
    <div className="mono-card" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid var(--border-main)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Ticket size={16} color="var(--text-primary)" />
          <h2 style={{ fontSize: '13px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-primary)' }}>
            Ticket Queue
          </h2>
        </div>

        <button onClick={onOpenSubmitModal} className="btn-secondary" style={{ padding: '4px 10px', fontSize: '12px' }}>
          <Plus size={14} />
          New
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {tickets.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px 10px', color: 'var(--text-muted)' }}>
            <p style={{ fontSize: '13px' }}>No tickets in queue</p>
          </div>
        ) : (
          tickets.map((t) => {
            const isSelected = t.id === selectedTicketId;

            return (
              <div
                key={t.id}
                onClick={() => onSelectTicket(t)}
                className="mono-card-interactive"
                style={{
                  padding: '12px 14px',
                  borderRadius: '8px',
                  border: `1px solid ${isSelected ? 'var(--text-primary)' : 'var(--border-main)'}`,
                  backgroundColor: isSelected ? 'var(--bg-card-hover)' : 'var(--bg-surface)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    #{t.id.slice(0, 8)}
                  </span>
                  <span className={`badge-status badge-${t.status.toLowerCase()}`}>
                    {t.status}
                  </span>
                </div>

                <p style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {t.subject}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>{t.customer_name || t.customer_email}</span>
                  <span>{t.plan_tier || 'Enterprise'}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
