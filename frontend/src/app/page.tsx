'use client';

import { useState, type ChangeEvent, type CSSProperties, type DragEvent, type FormEvent } from 'react';
import { login, uploadLeadFile } from '@/lib/api';
import type { ImportUploadResult, User } from '@/types';

export default function CommandCenterPage() {
  const [token, setToken] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'records' | 'ai'>('overview');
  const [user, setUser] = useState<User | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<ImportUploadResult | null>(null);
  const [uploadError, setUploadError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isBusy, setIsBusy] = useState(false);

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setUploadError('');
    setIsBusy(true);
    try {
      const session = await login(email, password, otp);
      setToken(session.token);
      setUser(session.user);
      setPassword('');
      setOtp('');
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Unable to sign in.');
    } finally {
      setIsBusy(false);
    }
  };

  const handleSignOut = () => {
    setToken(null);
    setUser(null);
    setFile(null);
    setUploadResult(null);
    setUploadError('');
  };

  const selectFile = (selectedFile: File | null) => {
    setFile(selectedFile);
    setUploadResult(null);
    setUploadError('');
  };

  const handleFileSelection = (event: ChangeEvent<HTMLInputElement>) => {
    selectFile(event.currentTarget.files?.[0] ?? null);
    event.currentTarget.value = '';
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    selectFile(event.dataTransfer.files[0] ?? null);
  };

  const handleUpload = async () => {
    if (!token || !file) return;
    setIsBusy(true);
    setUploadError('');
    setUploadResult(null);
    try {
      setUploadResult(await uploadLeadFile(token, file));
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Unable to process the uploaded file.');
    } finally {
      setIsBusy(false);
    }
  };

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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
              <div>
                <h3 style={{ fontSize: '15px', margin: 0 }}>Database Record Explorer</h3>
                <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: 0 }}>Import cleaned and validated lead records into the central database.</p>
              </div>
              {token && (
                <button onClick={handleSignOut} style={{ background: '#1e293b', color: '#cbd5e1', border: '1px solid #334155', borderRadius: '6px', padding: '8px 12px', cursor: 'pointer' }}>
                  Sign out{user ? ` (${user.name})` : ''}
                </button>
              )}
            </div>

            {!token ? (
              <form onSubmit={handleLogin} style={{ maxWidth: '420px', display: 'grid', gap: '12px', marginTop: '22px' }}>
                <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>Sign in with an authorized management account to upload data.</p>
                <label style={{ display: 'grid', gap: '6px', fontSize: '12px', color: '#cbd5e1' }}>
                  Email
                  <input type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} style={inputStyle} />
                </label>
                <label style={{ display: 'grid', gap: '6px', fontSize: '12px', color: '#cbd5e1' }}>
                  Password
                  <input type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} style={inputStyle} />
                </label>
                <label style={{ display: 'grid', gap: '6px', fontSize: '12px', color: '#cbd5e1' }}>
                  Authenticator code (if enabled)
                  <input inputMode="numeric" autoComplete="one-time-code" value={otp} onChange={(event) => setOtp(event.target.value)} style={inputStyle} />
                </label>
                <button type="submit" disabled={isBusy} style={primaryButtonStyle}>
                  {isBusy ? 'Signing in…' : 'Sign in'}
                </button>
              </form>
            ) : (
              <div style={{ maxWidth: '720px', marginTop: '22px' }}>
                <div
                  onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  style={{
                    border: `2px dashed ${isDragging ? '#60a5fa' : '#475569'}`,
                    background: isDragging ? 'rgba(37,99,235,0.12)' : '#0b1220',
                    borderRadius: '8px',
                    padding: '28px 18px',
                    textAlign: 'center'
                  }}
                >
                  <p style={{ margin: '0 0 8px', fontWeight: 600 }}>Drag and drop a file here</p>
                  <p style={{ margin: '0 0 14px', color: '#94a3b8', fontSize: '13px' }}>CSV or Excel (.xlsx), up to 20 MB and 50,000 rows</p>
                  <label htmlFor="lead-file" style={{ ...primaryButtonStyle, display: 'inline-block', cursor: 'pointer' }}>
                    Choose file
                  </label>
                  <input id="lead-file" type="file" accept=".csv,.xlsx" onChange={handleFileSelection} style={{ display: 'none' }} />
                </div>

                {file && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginTop: '14px' }}>
                    <span style={{ color: '#cbd5e1', fontSize: '13px', overflowWrap: 'anywhere' }}>Selected: {file.name}</span>
                    <button onClick={handleUpload} disabled={isBusy} style={primaryButtonStyle}>
                      {isBusy ? 'Validating and importing…' : 'Upload and import'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {uploadError && <p role="alert" style={{ color: '#fca5a5', fontSize: '13px', marginTop: '16px' }}>{uploadError}</p>}

            {uploadResult && (
              <section aria-live="polite" style={{ marginTop: '20px', padding: '16px', background: '#0b1220', border: '1px solid #334155', borderRadius: '8px' }}>
                <h4 style={{ margin: '0 0 12px', fontSize: '14px' }}>Import complete: {uploadResult.filename}</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px' }}>
                  <QualityMetric label="Rows checked" value={uploadResult.quality_report.total_imported_records} />
                  <QualityMetric label="Valid rows" value={uploadResult.quality_report.valid_records} />
                  <QualityMetric label="New records stored" value={uploadResult.quality_report.successful_records} />
                  <QualityMetric label="Duplicates for review" value={uploadResult.quality_report.duplicate_candidates} />
                  <QualityMetric label="Rejected rows" value={uploadResult.quality_report.rejected_records} />
                  <QualityMetric label="Data completeness" value={`${uploadResult.quality_report.data_completeness_pct}%`} />
                </div>
                <p style={{ color: '#94a3b8', fontSize: '12px', marginBottom: 0 }}>Batch ID: {uploadResult.batch_id}</p>
              </section>
            )}
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

const inputStyle: CSSProperties = {
  background: '#0b1220',
  color: '#f8fafc',
  border: '1px solid #334155',
  borderRadius: '6px',
  padding: '10px 12px',
  font: 'inherit'
};

const primaryButtonStyle: CSSProperties = {
  background: '#2563eb',
  color: '#fff',
  border: 'none',
  borderRadius: '6px',
  padding: '10px 14px',
  fontWeight: 600,
  cursor: 'pointer'
};

function QualityMetric({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <div style={{ color: '#94a3b8', fontSize: '11px' }}>{label}</div>
      <div style={{ fontSize: '18px', fontWeight: 700, marginTop: '3px' }}>{value}</div>
    </div>
  );
}
