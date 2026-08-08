import React, { useState } from 'react';
import { Check, Copy, RefreshCw, Mail, ShieldCheck, Clock, FileText } from 'lucide-react';

export function TicketDetailView({ ticket, onApprove }) {
  const [copied, setCopied] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [approved, setApproved] = useState(false);

  if (!ticket) {
    return (
      <div className="mono-card" style={{ padding: '40px 20px', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        <FileText size={36} style={{ marginBottom: '12px', opacity: 0.4 }} />
        <p style={{ fontSize: '14px', fontWeight: '500' }}>No Ticket Selected</p>
        <p style={{ fontSize: '12px', marginTop: '4px' }}>Select a ticket from the queue to view its AI draft resolution.</p>
      </div>
    );
  }

  const handleCopy = () => {
    if (ticket.resolution_draft) {
      navigator.clipboard.writeText(ticket.resolution_draft);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleApprove = async () => {
    setIsApproving(true);
    setTimeout(() => {
      setIsApproving(false);
      setApproved(true);
      if (onApprove) onApprove(ticket.id);
    }, 1000);
  };

  return (
    <div className="mono-card" style={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Info */}
      <div style={{ paddingBottom: '16px', borderBottom: '1px solid var(--border-main)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
          <div>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              TICKET #{ticket.id.slice(0, 8)}
            </span>
            <h2 style={{ fontSize: '18px', fontWeight: '600', color: 'var(--text-primary)', marginTop: '2px' }}>
              {ticket.subject}
            </h2>
          </div>
          <span className={`badge-status badge-${ticket.status.toLowerCase()}`}>
            {ticket.status}
          </span>
        </div>

        {/* Customer Metadata */}
        <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--text-secondary)', marginTop: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Mail size={14} color="var(--text-muted)" />
            <span>{ticket.customer_name} ({ticket.customer_email})</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={14} color="var(--text-muted)" />
            <span>{ticket.plan_tier} Plan</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Clock size={14} color="var(--text-muted)" />
            <span>{ticket.sla_hours}h SLA</span>
          </div>
        </div>
      </div>

      {/* Customer Issue Body */}
      <div>
        <h3 style={{ fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Customer Issue Payload
        </h3>
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-main)',
          borderRadius: '8px',
          padding: '12px 14px',
          fontSize: '13px',
          color: 'var(--text-secondary)',
          lineHeight: '1.5'
        }}>
          {ticket.body}
        </div>
      </div>

      {/* AI Resolution Draft Section */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 style={{ fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
            Grounded AI Draft Resolution (Gemini 3.1 Flash Lite)
          </h3>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={handleCopy} className="btn-secondary" style={{ padding: '4px 10px', fontSize: '12px' }}>
              {copied ? <Check size={14} /> : <Copy size={14} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
        </div>

        <div style={{
          flex: 1,
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-main)',
          borderRadius: '8px',
          padding: '16px',
          fontSize: '13px',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-primary)',
          whiteSpace: 'pre-wrap',
          lineHeight: '1.6',
          overflowY: 'auto'
        }}>
          {ticket.resolution_draft || (
            <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
              AI response draft is synthesizing... Please wait while multi-agent workflow completes.
            </span>
          )}
        </div>
      </div>

      {/* Supervisor Approval Actions */}
      <div style={{ paddingTop: '16px', borderTop: '1px solid var(--border-main)', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
        <button
          onClick={handleApprove}
          disabled={isApproving || approved || !ticket.resolution_draft}
          className="btn-primary"
          style={{ opacity: (!ticket.resolution_draft || approved) ? 0.6 : 1 }}
        >
          {approved ? <Check size={16} /> : <Mail size={16} />}
          {approved ? 'Approved & Sent to Customer' : isApproving ? 'Sending Response...' : 'Approve & Send Response'}
        </button>
      </div>
    </div>
  );
}
