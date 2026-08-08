import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../shared/hooks/useWebSocket';
import { HeaderWidget } from '../widgets/HeaderWidget';
import { LiveAgentFeed } from '../widgets/LiveAgentFeed';
import { TicketQueueWidget } from '../widgets/TicketQueueWidget';
import { TicketDetailView } from '../widgets/TicketDetailView';
import { SubmitTicketModal } from '../features/SubmitTicketModal';

// Sample seed ticket data for instant UI presentation
const INITIAL_TICKETS = [
  {
    id: '52e3f113-c9f1-49d1-9aba-0725c9610619',
    customer_name: 'Alice Smith',
    customer_email: 'alice@acme.com',
    plan_tier: 'Enterprise',
    sla_hours: 2,
    subject: 'PostgreSQL 504 Timeout in API',
    body: 'We are getting gateway timeouts on our enterprise database when scaling up API throughput.',
    status: 'COMPLETED',
    resolution_draft: `Dear Alice Smith,\n\nThank you for contacting Support regarding: 'PostgreSQL 504 Timeout in API'.\n\nAs an esteemed Enterprise Plan customer (Guaranteed SLA: 2 hours), your ticket has been prioritized by our Autonomous AI Engineering pipeline.\n\n### Technical Resolution & Diagnosis:\n- Resolving PostgreSQL 504 Gateway Timeouts in Enterprise API: Increase connection pool max_connections and adjust statement_timeout parameters in postgresql.conf.\n\n### Action Plan:\nOur engineering team has verified your account configuration (ACTIVE). Please apply the recommended pool tuning settings.\n\nBest regards,\nCustomer Success Engineering Team\nAutonomous CS Command Center`
  }
];

export function DashboardPage() {
  const { events, isConnected } = useWebSocket();
  const [tickets, setTickets] = useState(INITIAL_TICKETS);
  const [selectedTicketId, setSelectedTicketId] = useState(INITIAL_TICKETS[0].id);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Listen for incoming telemetry events and update ticket resolution draft live!
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[0];
      if (latestEvent.node_name === 'DraftAgent') {
        const draftText = latestEvent.full_draft || latestEvent.details;

        setTickets((prev) =>
          prev.map((t) => {
            if (t.id === latestEvent.ticket_id) {
              return {
                ...t,
                status: 'COMPLETED',
                resolution_draft: draftText
              };
            }
            return t;
          })
        );
      }
    }
  }, [events]);

  const handleTicketSubmitted = (newTicketData) => {
    const createdTicket = {
      id: newTicketData.ticket_id || `ticket-${Date.now()}`,
      customer_name: newTicketData.customer_email.split('@')[0],
      customer_email: newTicketData.customer_email,
      plan_tier: newTicketData.customer_email.includes('alice') ? 'Enterprise' : 'Standard',
      sla_hours: newTicketData.customer_email.includes('alice') ? 2 : 24,
      subject: newTicketData.subject,
      body: newTicketData.body,
      status: 'PROCESSING',
      resolution_draft: ''
    };

    setTickets((prev) => [createdTicket, ...prev]);
    setSelectedTicketId(createdTicket.id);
  };

  const selectedTicket = tickets.find((t) => t.id === selectedTicketId) || tickets[0];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-root)', display: 'flex', flexDirection: 'column' }}>
      <HeaderWidget isConnected={isConnected} />

      {/* Main Workspace Layout (3-Column Grid) */}
      <main style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: '320px 1fr 380px',
        gap: '16px',
        padding: '16px 24px',
        height: 'calc(100vh - 65px)',
        overflow: 'hidden'
      }}>
        {/* Left Column: Ticket Queue List */}
        <TicketQueueWidget
          tickets={tickets}
          selectedTicketId={selectedTicketId}
          onSelectTicket={(t) => setSelectedTicketId(t.id)}
          onOpenSubmitModal={() => setIsModalOpen(true)}
        />

        {/* Middle Column: Ticket Detail & Resolution Draft */}
        <TicketDetailView
          ticket={selectedTicket}
          onApprove={(id) => {
            setTickets((prev) => prev.map((t) => t.id === id ? { ...t, status: 'APPROVED' } : t));
          }}
        />

        {/* Right Column: Real-Time Telemetry Timeline */}
        <LiveAgentFeed events={events} />
      </main>

      <SubmitTicketModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleTicketSubmitted}
      />
    </div>
  );
}
