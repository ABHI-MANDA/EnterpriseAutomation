'use client';

import React, { useState, useEffect } from 'react';
import { getOverview, getLeads, previewAllocations, executeAllocations, askAIAgent } from '@/lib/api';
import { ExecutiveOverview, LeadRecord, AIAgentResponse } from '@/types';

export default function CommandCenterPage() {
  const [token, setToken] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'records' | 'ai'>('overview');
  const [overview, setOverview] = useState<ExecutiveOverview | null>(null);
  const [leads, setLeads] = useState<LeadRecord[]>([]);
  const [aiMessage, setAiMessage] = useState('');
  const [aiHistory, setAiHistory] = useState<AIAgentResponse[]>([]);
  const [loading, setLoading] = useState(false);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <aside style={{ width: '260px', background: '#0f172a', borderRight: '1px solid #1e293b', padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
          <div style={{ background: '#2563eb', width: '32px', height: '32px', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>🏢</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '14px' }}>Command Center</div>
            <div style={{ fontSize: '11px', color: '#64748b' }}>Operations & AI</div>
          </div>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button onClick={() => setActiveTab('overview')} style={{ textAlign: 'left', padding: '10px 14px', borderRadius: '6px', background: activeTab === 'overview' ? '#1e293b' : 'transparent', color: activeTab === 'overview' ? '#60a5fa' : '#94a3b8', border: 'none', cursor: 'pointer', fontWeight: 600 }}>📊 Executive Overview</button>
          <button onClick={() => setActiveTab('records')} style={{ textAlign: 'left', padding: '10px 14px', borderRadius: '6px', background: activeTab === 'records' ? '#1e293b' : 'transparent', color: activeTab === 'records' ? '#60a5fa' : '#94a3b8', border: 'none', cursor: 'pointer', fontWeight: 600 }}>🔍 Record Explorer</button>
          <button onClick={() => setActiveTab('ai')} style={{ textAlign: 'left', padding: '10px 14px', borderRadius: '6px', background: activeTab === 'ai' ? '#1e293b' : 'transparent', color: activeTab === 'ai' ? '#60a5fa' : '#94a3b8', border: 'none', cursor: 'pointer', fontWeight: 600 }}>🤖 AI Agent Assistant</button>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
        <header style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: 700 }}>Real Estate Operations Command Center</h1>
            <p style={{ fontSize: '13px', color: '#94a3b8' }}>Observe, Analyze, Decide, Execute, and Monitor across all regions</p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <span style={{ fontSize: '12px', background: 'rgba(16,185,129,0.15)', color: '#34d399', padding: '6px 10px', borderRadius: '9999px', border: '1px solid rgba(16,185,129,0.3)' }}>● Live Engine Connected</span>
          </div>
        </header>

        {activeTab === 'overview' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
              <div style={{ background: '#111827', border: '1px solid #1e293b', padding: '16px', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>ACTIVE LEADS</div>
                <div style={{ fontSize: '24px', fontWeight: 700, margin: '6px 0' }}>112</div>
                <div style={{ fontSize: '11px', color: '#60a5fa' }}>Conversion Rate: 16.4%</div>
              </div>
              <div style={{ background: '#111827', border: '1px solid #1e293b', padding: '16px', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>ACTIVE PROJECTS</div>
                <div style={{ fontSize: '24px', fontWeight: 700, margin: '6px 0' }}>5 Projects</div>
                <div style={{ fontSize: '11px', color: '#34d399' }}>Available Units: 45</div>
              </div>
              <div style={{ background: '#111827', border: '1px solid #1e293b', padding: '16px', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>PIPELINE VALUE</div>
                <div style={{ fontSize: '24px', fontWeight: 700, margin: '6px 0' }}>₹142.5 Cr</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Closed Revenue: ₹48.0 Cr</div>
              </div>
              <div style={{ background: '#111827', border: '1px solid #1e293b', padding: '16px', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>CRM SYNC HEALTH</div>
                <div style={{ fontSize: '24px', fontWeight: 700, margin: '6px 0', color: '#34d399' }}>Healthy</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Outbox Queue: 0 Pending</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'records' && (
          <div style={{ background: '#111827', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ fontSize: '15px', marginBottom: '12px' }}>Database Record Explorer</h3>
            <p style={{ fontSize: '13px', color: '#94a3b8' }}>Server-side paginated lead records authorized via Row Level Security (RLS).</p>
          </div>
        )}

        {activeTab === 'ai' && (
          <div style={{ background: '#111827', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ fontSize: '15px', marginBottom: '12px' }}>AI Agent Orchestrator & Conversational Actions</h3>
            <p style={{ fontSize: '13px', color: '#94a3b8' }}>Interprets intent, retrieves evidence, evaluates workload balance, and requests manager authorization before consequential CRM actions.</p>
          </div>
        )}
      </main>
    </div>
  );
}
