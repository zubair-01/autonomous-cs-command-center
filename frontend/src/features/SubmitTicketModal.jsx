import React, { useState } from 'react';
import { Send, X, AlertCircle, Check } from 'lucide-react';

export function SubmitTicketModal({ isOpen, onClose, onSuccess }) {
  const [customerEmail, setCustomerEmail] = useState('alice@acme.com');
  const [subject, setSubject] = useState('Enterprise SLA billing inquiry and PostgreSQL API timeout error');
  const [body, setBody] = useState('We are paying for the Enterprise SLA plan but experiencing 504 timeouts on our database. Please verify our SLA guarantee and fix the database timeouts.');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setResult(null);

    try {
      const response = await fetch('/api/v1/tickets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_email: customerEmail, subject, body }),
      });

      const data = await response.json();
      if (response.ok) {
        setResult({ success: true, data });
        if (onSuccess) onSuccess({ ...data, subject, body, customer_email: customerEmail });
        setTimeout(() => {
          setIsSubmitting(false);
          onClose();
        }, 1200);
      } else {
        setResult({ success: false, error: data.detail || 'Failed to submit ticket' });
        setIsSubmitting(false);
      }
    } catch (err) {
      setResult({ success: false, error: err.message });
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(9, 9, 11, 0.85)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div className="mono-card" style={{ width: '100%', maxWidth: '520px', padding: '24px', position: 'relative' }}>
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '20px', right: '20px', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
        >
          <X size={18} />
        </button>

        <h2 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '4px' }}>
          Submit Customer Ticket Event
        </h2>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '20px' }}>
          Triggers event-driven HTTP 202 ingestion to Kafka & LangGraph.
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px', color: 'var(--text-muted)' }}>
              CUSTOMER EMAIL
            </label>
            <select
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-main)',
                color: 'var(--text-primary)',
                fontSize: '13px'
              }}
            >
              <option value="alice@acme.com">alice@acme.com (Enterprise Plan - 2h SLA)</option>
              <option value="bob@startup.io">bob@startup.io (Pro Plan - 8h SLA)</option>
              <option value="charlie@techlabs.dev">charlie@techlabs.dev (Standard Plan - 24h SLA)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px', color: 'var(--text-muted)' }}>
              ISSUE SUBJECT
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-main)',
                color: 'var(--text-primary)',
                fontSize: '13px'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px', color: 'var(--text-muted)' }}>
              ISSUE PAYLOAD BODY
            </label>
            <textarea
              rows={4}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-main)',
                color: 'var(--text-primary)',
                fontSize: '13px',
                fontFamily: 'inherit'
              }}
            />
          </div>

          {result && (
            <div style={{
              padding: '10px 12px',
              borderRadius: '6px',
              backgroundColor: result.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
              border: `1px solid ${result.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '12px',
              color: result.success ? 'var(--accent-emerald)' : 'var(--accent-rose)'
            }}>
              {result.success ? <Check size={16} /> : <AlertCircle size={16} />}
              <span>{result.success ? result.data.message : result.error}</span>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              <Send size={14} />
              {isSubmitting ? 'Ingesting to Kafka...' : 'Publish Ticket Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
