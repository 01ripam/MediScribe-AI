'use client';

import { useState, useEffect, useRef } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const [loginLoading, setLoginLoading] = useState<string | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);

  // Doctor state
  const [activeTab, setActiveTab] = useState<'dashboard' | 'history' | 'calendar'>('dashboard');
  const [calendarMonth, setCalendarMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [calendarAppointments, setCalendarAppointments] = useState<any[]>([]);
  const [calendarSelectedDay, setCalendarSelectedDay] = useState<number | null>(null);
  const [appointments, setAppointments] = useState<any[]>([]);

  // Shared Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newAppt, setNewAppt] = useState({ patientName: '', patientEmail: '', patientAge: '', patientGender: '', appointmentDate: '', doctorId: '' });
  const [isProcessing, setIsProcessing] = useState(false);

  // Common/Patient state
  const [history, setHistory] = useState<any[]>([]);
  const [currentPatient, setCurrentPatient] = useState<any | null>(null);

  // Expanded Patient State
  const [patientTab, setPatientTab] = useState<'records' | 'doctors' | 'reports'>('records');
  const [doctorsList, setDoctorsList] = useState<any[]>([]);
  const [busySlots, setBusySlots] = useState<string[]>([]);
  const [busySlotsLoading, setBusySlotsLoading] = useState(false);

  // Reports
  const [reportsList, setReportsList] = useState<any[]>([]);
  const [reportText, setReportText] = useState('');
  const [selectedDoctorId, setSelectedDoctorId] = useState('');

  // Quick Scribe
  const [isQuickScribeOpen, setIsQuickScribeOpen] = useState(false);
  const [isDictating, setIsDictating] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [scribeData, setScribeData] = useState<any>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const error = urlParams.get('error');
      if (error) setLoginError("Authentication failed. " + error);
    }
  }, []);

  const role = (session?.user as any)?.role || 'PATIENT';

  useEffect(() => {
    if (status === 'authenticated') {
      fetchHistory();
      fetchReports();
      if (role === 'DOCTOR') {
        fetchAppointments('UPCOMING');
      } else {
        fetchDoctors();
      }
    }
  }, [status, role]);

  useEffect(() => {
    if (status === 'authenticated' && role === 'DOCTOR' && activeTab === 'calendar') {
      fetchCalendarAppointments(calendarMonth);
    }
  }, [activeTab, calendarMonth, status, role]);

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/patients');
      const data = await res.json();
      if (res.ok && Array.isArray(data)) setHistory(data);
    } catch (err) {}
  };

  const fetchAppointments = async (statusFilter: string) => {
    try {
      const res = await fetch(`/api/appointments?status=${statusFilter}`);
      const data = await res.json();
      if (res.ok && Array.isArray(data)) setAppointments(data);
    } catch (err) {}
  };

  const fetchDoctors = async () => {
    try {
      const res = await fetch('/api/doctors');
      const data = await res.json();
      if (res.ok) setDoctorsList(data);
    } catch (err) {}
  };

  const fetchBusySlots = async (doctorId: string, month: string) => {
    if (!doctorId) return;
    setBusySlotsLoading(true);
    try {
      const res = await fetch(`/api/appointments?mode=availability&doctorId=${doctorId}&month=${month}`);
      const data = await res.json();
      if (res.ok && Array.isArray(data)) setBusySlots(data);
      else setBusySlots([]);
    } catch { setBusySlots([]); } finally { setBusySlotsLoading(false); }
  };

  const fetchCalendarAppointments = async (month: string) => {
    try {
      const res = await fetch(`/api/appointments?month=${month}`);
      const data = await res.json();
      if (res.ok && Array.isArray(data)) setCalendarAppointments(data);
    } catch {}
  };

  const fetchReports = async () => {
    try {
      const res = await fetch('/api/reports');
      const data = await res.json();
      if (res.ok && Array.isArray(data)) setReportsList(data);
    } catch (err) {}
  };

  const handleCreateAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);
    try {
      const payload = { ...newAppt };
      if (role === 'PATIENT') {
        payload.patientName = session?.user?.name || 'Patient';
        payload.patientEmail = session?.user?.email || '';
      } else {
        payload.doctorId = (session?.user as any)?.id;
      }
      const res = await fetch('/api/appointments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.error || 'Failed');
      setIsModalOpen(false);
      setBusySlots([]);
      setNewAppt({ patientName: '', patientEmail: '', patientAge: '', patientGender: '', appointmentDate: '', doctorId: '' });
      if (role === 'DOCTOR') {
        fetchAppointments('UPCOMING');
        fetchCalendarAppointments(calendarMonth);
      }
      if (role === 'PATIENT') alert("\u2705 Appointment successfully booked!");
    } catch (err: any) {
      alert("\u274c " + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAnalyzeReport = async () => {
    if (!reportText || !selectedDoctorId) {
      alert("Please provide the report text and select a physician to review it.");
      return;
    }
    setIsProcessing(true);
    try {
      const aiRes = await fetch('/api/analyze-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reportText })
      });
      const aiData = await aiRes.json();
      if (!aiRes.ok) throw new Error(aiData.error || 'AI Processing Failed. Ensure GEMINI_API_KEY is active.');
      const saveRes = await fetch('/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doctorId: selectedDoctorId, aiSummary: aiData.summary, isEmergency: aiData.isEmergency, details: aiData.details, rawText: reportText })
      });
      if (!saveRes.ok) throw new Error('Database save failed');
      alert(aiData.isEmergency ? "CRITICAL ALERT: Your analysis has been flagged as high-risk and immediately forwarded to your physician's emergency queue." : "Report securely analyzed and archived for your next consultation.");
      setReportText('');
      setPatientTab('records');
      fetchReports();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const startQuickScribe = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert("Your browser does not support Speech Recognition. Please use Chrome.");
      return;
    }
    setScribeData(null);
    setLiveTranscript('');
    setIsQuickScribeOpen(true);
    setIsDictating(true);
    const SpeechRecognition = (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.onresult = (event: any) => {
      let currentTranscript = '';
      for (let i = 0; i < event.results.length; i++) currentTranscript += event.results[i][0].transcript;
      setLiveTranscript(currentTranscript);
    };
    recognition.start();
    recognitionRef.current = recognition;
  };

  const stopQuickScribe = async () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsDictating(false);
      setIsProcessing(true);
      try {
        const formData = new FormData();
        formData.append('transcript', liveTranscript);
        const response = await fetch('/api/generate-soap', { method: 'POST', body: formData });
        const aiData = await response.json();
        if (!response.ok) throw new Error(aiData.error || 'Failed');
        setScribeData({ name: aiData.name || '', patientEmail: '', age: aiData.age || '', gender: aiData.gender || '', bloodGroup: aiData.bloodGroup || '', subjective: aiData.subjective || '', objective: aiData.objective || '', assessment: aiData.assessment || '', plan: aiData.plan || '' });
      } catch (err: any) {
        alert("Failed to process AI logic: " + err.message);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const saveQuickScribe = async () => {
    setIsProcessing(true);
    try {
      const compiledNote = `# SOAP Note\n\n**Subjective:**\n${scribeData.subjective}\n\n**Objective:**\n${scribeData.objective}\n\n**Assessment:**\n${scribeData.assessment}\n\n**Plan:**\n${scribeData.plan}`;
      const payload = { name: scribeData.name, patientEmail: scribeData.patientEmail, age: scribeData.age, gender: scribeData.gender, bloodGroup: scribeData.bloodGroup, note: compiledNote };
      const res = await fetch('/api/patients', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error('Failed to save record.');
      setIsQuickScribeOpen(false);
      setScribeData(null);
      fetchHistory();
      setActiveTab('history');
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const todayStr = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

  if (status === 'loading') {
    return <div className="app-window" style={{justifyContent: 'center', alignItems: 'center'}}>Loading Workspace...</div>;
  }

  if (status === 'unauthenticated') {
    const handleDemoLogin = async () => {
      setLoginLoading('demo');
      const res = await signIn('credentials', { username: 'admin', password: 'password', redirect: false });
      if (res?.error) { setLoginError("Invalid admin credentials"); setLoginLoading(null); }
    };
    const handleSocialLogin = async (provider: string) => {
      setLoginLoading(provider);
      await signIn(provider, { callbackUrl: '/' });
    };
    return (
      <div className="app-window" style={{justifyContent: 'center', alignItems: 'center', background: 'var(--bg-main)'}}>
        <div style={{background: 'var(--card-bg)', padding: '3rem', borderRadius: '1rem', border: '1px solid var(--border-color)', textAlign: 'center', maxWidth: '450px', width: '100%', boxShadow: '0 10px 30px rgba(0,0,0,0.5)'}}>
          <h1 style={{marginBottom: '0.5rem', fontSize: '2rem'}}>MediScribe <span style={{color: 'var(--primary)'}}>AI</span></h1>
          <p style={{marginBottom: '2rem', color: 'var(--text-gray)'}}>Sign in to access your secure clinical workspace.</p>
          {loginError && <div style={{background: 'rgba(216, 0, 12, 0.1)', color: '#ff6b6b', padding: '1rem', borderRadius: '0.5rem', marginBottom: '1.5rem', fontSize: '0.9rem', border: '1px solid #ff6b6b'}}>{loginError}</div>}
          <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            <button className="action-btn" onClick={() => handleSocialLogin('google')} disabled={!!loginLoading} style={{background: '#db4437'}}>
              {loginLoading === 'google' ? 'Signing in...' : 'Sign in with Google'}
            </button>
            <button className="action-btn" onClick={handleDemoLogin} disabled={!!loginLoading} style={{background: 'var(--card-bg)', color: 'var(--text-main)', border: '1px solid var(--border-color)'}}>
              {loginLoading === 'demo' ? 'Signing in...' : 'Sign in with Demo Account'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ==== PATIENT VIEW ====
  if (role === 'PATIENT') {
    const downloadPdf = async (patientName: string) => {
      const { default: jsPDF } = await import('jspdf');
      const { default: html2canvas } = await import('html2canvas');
      const input = document.getElementById('prescription-container');
      if (!input) return;
      // @ts-ignore
      const canvas = await html2canvas(input, { scale: 2 });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`MediScribe_Prescription_${patientName.replace(/\s+/g, '_')}.pdf`);
    };

    // Helper: is a datetime ISO string within the selected month?
    const nowForModal = new Date();
    const currentMonthStr = `${nowForModal.getFullYear()}-${String(nowForModal.getMonth() + 1).padStart(2, '0')}`;

    return (
      <div className="app-window" style={{flexDirection: 'column'}}>
        <div style={{display: 'flex', flex: 1, overflow: 'hidden'}}>
          <aside className="sidebar">
            <div className="logo-area"><div className="logo-icon"><div/><div/><div/></div>MediScribe Patient</div>
            <div className="user-profile">
              <div className="avatar-container" onClick={() => signOut()} style={{cursor: 'pointer'}} title="Sign out">ðŸ‘¤</div>
              <div className="user-name">{session?.user?.name || 'Patient'}</div>
              <div className="user-email">{session?.user?.email}</div>
            </div>
            <nav className="nav-menu">
              <div className={`nav-item ${patientTab === 'records' ? 'active' : ''}`} onClick={() => setPatientTab('records')}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16h16V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                My Records
              </div>
              <div className={`nav-item ${patientTab === 'doctors' ? 'active' : ''}`} onClick={() => setPatientTab('doctors')}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>
                Find a Doctor
              </div>
              <div className={`nav-item ${patientTab === 'reports' ? 'active' : ''}`} onClick={() => setPatientTab('reports')}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                Upload AI Reports
              </div>
            </nav>
          </aside>

          <main className="main-area">
            {patientTab === 'records' && (
              <>
                <header className="header" style={{marginBottom: '2rem', display: 'flex', justifyContent: 'space-between'}}>
                  <h1>My Medical Records</h1>
                </header>
                <div className="task-list">
                  {history.length === 0 ? (
                    <p style={{color: '#94a3b8'}}>No official medical records found linked to this account.</p>
                  ) : (
                    history.map((pt, i) => (
                      <div className={`task-item ${i%3===0?'teal':i%3===1?'purple':'orange'}`} key={pt.id} onClick={() => setCurrentPatient(pt)} style={{cursor:'pointer', borderLeftWidth: '6px'}}>
                        <div>
                          <h4>{pt.name} - Official Consultation</h4>
                          <p>Issued on {new Date(pt.date!).toLocaleDateString()} at {new Date(pt.date!).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                        </div>
                      </div>
                    ))
                  )}
                  {reportsList.length > 0 && (
                    <>
                      <h3 style={{marginTop: '2rem', marginBottom: '1rem', color: '#475569'}}>Analyzed Lab Reports</h3>
                      {reportsList.map((rep) => (
                        <div key={rep._id} style={{padding: '1.5rem', background: 'white', borderRadius: '12px', border: rep.isEmergency ? '2px solid #ef4444' : '1px solid #e2e8f0', marginBottom: '1rem'}}>
                          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                            <div style={{fontWeight: 600, color: rep.isEmergency ? '#ef4444' : '#0f172a'}}>{rep.isEmergency && "ðŸš¨ CRITICAL: "}Report Analysis</div>
                            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>{new Date(rep.createdAt).toLocaleString()}</div>
                          </div>
                          <p style={{color: '#334155', lineHeight: '1.6'}}>{rep.aiSummary}</p>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              </>
            )}

            {patientTab === 'doctors' && (
              <>
                <header className="header" style={{marginBottom: '2rem'}}>
                  <h1>Find a Doctor</h1>
                  <p style={{color: 'var(--text-gray)'}}>Book an appointment with specialized physicians.</p>
                </header>
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem'}}>
                  {doctorsList.map((doc) => (
                    <div key={doc.id} style={{background: 'white', borderRadius: '16px', padding: '2rem', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', textAlign: 'center'}}>
                      <div style={{width: '64px', height: '64px', borderRadius: '50%', background: '#e0bbe4', margin: '0 auto 1rem auto', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem'}}>ðŸ©º</div>
                      <h3 style={{fontSize: '1.3rem', marginBottom: '0.5rem', color: '#0f172a'}}>{doc.name}</h3>
                      <div style={{color: '#8b5cf6', fontWeight: 600, fontSize: '0.9rem', marginBottom: '1.5rem', textTransform: 'uppercase'}}>{doc.specialty}</div>
                      <button className="action-btn" style={{width: '100%', background: '#10b981'}} onClick={() => {
                        setNewAppt({...newAppt, doctorId: doc.id});
                        fetchBusySlots(doc.id, currentMonthStr);
                        setIsModalOpen(true);
                      }}>Book Appointment</button>
                    </div>
                  ))}
                </div>
              </>
            )}

            {patientTab === 'reports' && (
              <div style={{maxWidth: '800px'}}>
                <header className="header" style={{marginBottom: '2rem'}}>
                  <h1>AI Diagnostic Report Triage</h1>
                  <p style={{color: 'var(--text-gray)'}}>Upload your lab results or diagnostics. Our AI will analyze the metrics and alert your preferred physician heavily if an emergency is detected, ensuring critical care isn't missed between visits.</p>
                </header>
                <div style={{background: 'white', padding: '2.5rem', borderRadius: '16px', border: '1px solid #e2e8f0', boxShadow: '0 10px 25px rgba(0,0,0,0.05)'}}>
                  <div style={{marginBottom: '1.5rem'}}>
                    <label style={{display: 'block', fontWeight: 600, marginBottom: '0.5rem'}}>Select Physician for Review</label>
                    <select className="form-input" style={{width: '100%'}} value={selectedDoctorId} onChange={e => setSelectedDoctorId(e.target.value)}>
                      <option value="" disabled>Choose a Doctor</option>
                      {doctorsList.map(doc => <option key={doc.id} value={doc.id}>{doc.name} - {doc.specialty}</option>)}
                    </select>
                  </div>
                  <div style={{marginBottom: '2rem'}}>
                    <label style={{display: 'block', fontWeight: 600, marginBottom: '0.5rem'}}>Diagnostic Report Text / PDF Contents</label>
                    <textarea className="form-input" style={{height: '200px', width: '100%', resize: 'vertical'}} placeholder="Paste the raw text of your lab results here..." value={reportText} onChange={e => setReportText(e.target.value)} />
                  </div>
                  <button className="action-btn" onClick={handleAnalyzeReport} disabled={isProcessing} style={{width: '100%', padding: '1.2rem', fontSize: '1.1rem', background: '#3b82f6'}}>
                    {isProcessing ? 'ðŸ¤– Gemini is Analyzing Metrics...' : 'Run AI Triage & Submit Report'}
                  </button>
                </div>
              </div>
            )}
          </main>

          {patientTab === 'records' && (
            <aside className="right-panel" style={{width: '450px', background: '#f8fafc', padding: '2rem', borderLeft: '1px solid #e2e8f0'}}>
              {currentPatient ? (
                <div style={{display: 'flex', flexDirection: 'column', height: '100%'}}>
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem'}}>
                    <h2>Selected Record</h2>
                    <button onClick={() => downloadPdf(currentPatient.name)} className="action-btn" style={{padding: '8px 16px', fontSize: '0.85rem', background: '#2563eb'}}>â†“ Download PDF</button>
                  </div>
                  <div id="prescription-container" style={{background: 'white', padding: '2.5rem', borderRadius: '8px', boxShadow: '0 10px 25px rgba(0,0,0,0.05)', flex: 1, overflowY: 'auto', border: '1px solid #e2e8f0'}}>
                    <div style={{borderBottom: '2px solid #e2e8f0', paddingBottom: '1rem', marginBottom: '1.5rem'}}>
                      <h1 style={{fontSize: '1.6rem', color: '#0f172a', fontWeight: 800}}>MediScribe Clinic</h1>
                    </div>
                    <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem', background: '#f1f5f9', padding: '1rem', borderRadius: '8px', color: '#0f172a'}}>
                      <div><span style={{color: '#64748b'}}>Name</span><h4>{currentPatient.name}</h4></div>
                      <div><span style={{color: '#64748b'}}>Date</span><h4>{new Date(currentPatient.date!).toLocaleDateString()}</h4></div>
                      <div><span style={{color: '#64748b'}}>Age/Gen</span><h4>{currentPatient.age} / {currentPatient.gender}</h4></div>
                      <div><span style={{color: '#64748b'}}>Blood</span><h4>{currentPatient.bloodGroup}</h4></div>
                    </div>
                    <div style={{whiteSpace: 'pre-wrap', fontFamily: '"Inter", sans-serif', color: '#334155', fontSize: '0.95rem', lineHeight: '1.6'}}>
                      {currentPatient.note.split('**').map((part: string, i: number) => i % 2 === 1 ? <strong key={i} style={{color: '#0f172a', display: 'block', marginTop: '1.5rem', marginBottom: '0.5rem', fontSize: '1.05rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '4px'}}>{part}</strong> : <span key={i}>{part.replace('# SOAP Note', '')}</span>)}
                    </div>
                  </div>
                </div>
              ) : <p style={{color: '#94a3b8', textAlign: 'center', marginTop: '5rem'}}>Select a record to view.</p>}
            </aside>
          )}
        </div>

        {/* Patient Appointment Booking Modal */}
        {isModalOpen && (
          <div style={{position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
            <form onSubmit={handleCreateAppointment} style={{background: 'white', padding: '2rem', borderRadius: '12px', width: '100%', maxWidth: '440px', display: 'flex', flexDirection: 'column', gap: '1rem'}}>
              <h2>Schedule with {doctorsList.find(d => d.id === newAppt.doctorId)?.name}</h2>

              {/* Busy Slots Banner */}
              {busySlotsLoading && <div style={{background: '#f0f9ff', padding: '0.75rem', borderRadius: '8px', color: '#0369a1', fontSize: '0.85rem'}}>â³ Loading doctor availability...</div>}
              {!busySlotsLoading && busySlots.length > 0 && (
                <div style={{background: '#fef9c3', border: '1px solid #fde047', padding: '0.75rem 1rem', borderRadius: '8px'}}>
                  <div style={{fontWeight: 700, color: '#713f12', marginBottom: '0.4rem', fontSize: '0.85rem'}}>ðŸ”´ Doctor already booked at these times (unavailable):</div>
                  <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.4rem'}}>
                    {busySlots.map((slot, i) => (
                      <span key={i} style={{background: '#fca5a5', color: '#7f1d1d', padding: '2px 8px', borderRadius: '999px', fontSize: '0.78rem', fontWeight: 600}}>
                        {new Date(slot).toLocaleDateString()} {new Date(slot).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
                      </span>
                    ))}
                  </div>
                  <div style={{color: '#92400e', fontSize: '0.78rem', marginTop: '0.5rem'}}>âš ï¸ Appointments must be at least 30 min apart from these slots.</div>
                </div>
              )}
              {!busySlotsLoading && busySlots.length === 0 && (
                <div style={{background: '#f0fdf4', border: '1px solid #86efac', padding: '0.6rem 1rem', borderRadius: '8px', color: '#166534', fontSize: '0.85rem'}}>âœ… Doctor is fully available this month!</div>
              )}

              <div style={{display: 'flex', gap: '1rem'}}>
                <div style={{flex: 1}}>
                  <label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Your Age*</label>
                  <input required type="number" className="form-input" value={newAppt.patientAge} onChange={e => setNewAppt({...newAppt, patientAge: e.target.value})} />
                </div>
                <div style={{flex: 1}}>
                  <label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Gender*</label>
                  <select required className="form-input" value={newAppt.patientGender} onChange={e => setNewAppt({...newAppt, patientGender: e.target.value})}>
                    <option value="" disabled>Select</option><option value="Male">Male</option><option value="Female">Female</option><option value="Other">Other</option>
                  </select>
                </div>
              </div>
              <div>
                <label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Date & Time Required*</label>
                <input required type="datetime-local" className="form-input" value={newAppt.appointmentDate} onChange={e => setNewAppt({...newAppt, appointmentDate: e.target.value})} />
              </div>
              <div style={{display: 'flex', gap: '1rem', marginTop: '1rem'}}>
                <button type="button" className="action-btn" onClick={() => { setIsModalOpen(false); setBusySlots([]); }} style={{background: '#e2e8f0', color: '#475569', flex: 1}}>Cancel</button>
                <button type="submit" className="action-btn" disabled={isProcessing} style={{flex: 1}}>{isProcessing ? 'Booking...' : 'Confirm Appointment'}</button>
              </div>
            </form>
          </div>
        )}
      </div>
    );
  }

  // ==== DOCTOR VIEW ====
  return (
    <div className="app-window" style={{flexDirection: 'column', position: 'relative'}}>
      <div style={{background: '#ffecba', color: '#6b4d02', padding: '0.4rem', textAlign: 'center', fontSize: '0.8rem', fontWeight: 600}}>
        âš ï¸ DEMONSTRATION TOOL: Do not enter real Patient Health Information (PHI). Not HIPAA compliant.
      </div>

      <div style={{display: 'flex', flex: 1, overflow: 'hidden'}}>
        <aside className="sidebar">
          <div className="logo-area"><div className="logo-icon"><div/><div/><div/></div>MediScribe</div>
          <div className="user-profile">
            <div className="avatar-container" onClick={() => signOut()} style={{cursor: 'pointer'}} title="Sign out">ðŸ©º</div>
            <div className="user-name">{session?.user?.name || 'Doctor'}</div>
          </div>
          <nav className="nav-menu">
            <div className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
              Dashboard
            </div>
            <div className={`nav-item ${activeTab === 'calendar' ? 'active' : ''}`} onClick={() => setActiveTab('calendar')}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
              My Calendar
            </div>
            <div className={`nav-item ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16h16V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              Patient List
            </div>
          </nav>
        </aside>

        <main className="main-area">
          <header className="header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem'}}>
            <div className="greeting">
              <h1>Hello, {session?.user?.name?.split(' ')[0] || 'Doc'}</h1>
              <p>Today is {todayStr}</p>
            </div>
            <div className="header-actions">
              <button className="search-btn">
                <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              </button>
              <button className="action-btn" onClick={startQuickScribe} style={{background: '#8b5cf6', marginRight: '0.5rem'}}>ðŸŽ™ï¸ Quick AI Scribe</button>
              <button className="action-btn" onClick={() => setIsModalOpen(true)}>+ New Appointment</button>
            </div>
          </header>

          {activeTab === 'dashboard' && (
            <>
              {reportsList.length > 0 && (
                <div style={{background: '#fef2f2', border: '1px solid #fecaca', padding: '1.5rem', borderRadius: '16px', marginBottom: '2rem', borderLeft: '8px solid #ef4444'}}>
                  <h3 style={{color: '#b91c1c', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '10px'}}>
                    <span style={{animation: 'pulse 2s infinite'}}>ðŸš¨</span> CRITICAL AI TRIAGE ALERTS
                  </h3>
                  <p style={{color: '#991b1b', marginBottom: '1rem', fontSize: '0.95rem'}}>The Gemini AI Triage system has flagged the following patient uploads as life-threatening or requiring immediate intervention.</p>
                  <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                    {reportsList.map(rep => (
                      <div key={rep._id} style={{background: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)'}}>
                        <div style={{fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem'}}>{rep.patientName} <span style={{color: '#64748b', fontSize: '0.85rem', fontWeight: 400}}>({rep.patientEmail})</span></div>
                        <div style={{color: '#ef4444', fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem'}}>{rep.aiSummary}</div>
                        <div style={{color: '#334155', fontSize: '0.85rem', width: '100%'}}>
                          <strong>Flagged Metrics:</strong>
                          <pre style={{marginTop: '0.5rem', whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0}}>{typeof rep.details === 'string' ? rep.details : JSON.stringify(rep.details, null, 2)}</pre>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="card-row">
                <div className="stat-card purple">
                  <div className="card-top"><div className="avatar-group"><div>+7</div><div style={{background: '#e0bbe4'}}></div><div style={{background: '#9eb9f3'}}></div></div><span>â‹®</span></div>
                  <div className="card-title-lg">Total Patients<br/>Treated</div>
                  <div className="card-bottom"><span>{history.length} patients</span><span>100% Secure</span></div>
                  <div className="progress-bar"><div className="progress-fill" style={{width: '100%'}}></div></div>
                </div>
                <div className="stat-card teal">
                  <div className="card-top"><div className="avatar-group"><div>+</div><div style={{background: '#f3c4fb'}}></div></div></div>
                  <div className="card-title-lg">Upcoming<br/>Appointments</div>
                  <div className="card-bottom"><span>{appointments.length} waiting</span><span>Active</span></div>
                  <div className="progress-bar"><div className="progress-fill" style={{width: '75%'}}></div></div>
                </div>
                <div className="stat-card orange" onClick={() => setIsModalOpen(true)} style={{cursor: 'pointer'}}>
                  <div className="card-top"><div className="avatar-group"><div>+</div><div style={{background: '#fff9b0'}}></div><div style={{background: '#c1ffcf'}}></div></div></div>
                  <div className="card-title-lg">Book New<br/>Consultation</div>
                  <div className="card-bottom"><span>Open Schedule</span></div>
                  <div className="progress-bar"><div className="progress-fill" style={{width: '20%'}}></div></div>
                </div>
              </div>

              <div className="middle-section">
                <div style={{flex: 1}}>
                  <h3 className="section-title">Today's Agenda</h3>
                  {appointments.length === 0 ? (
                    <div style={{padding: '3rem', textAlign: 'center', background: '#f8f9fa', borderRadius: '16px', color: 'var(--text-gray)', border: '2px dashed #e2e8f0'}}>
                      <svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" strokeWidth="1" fill="none" style={{marginBottom: '1rem', color: '#10b981'}}><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line><path d="M9 16l2 2 4-4"></path></svg>
                      <h3 style={{color: '#1e293b', marginBottom: '0.5rem', fontSize: '1.4rem'}}>Your Schedule is Clear!</h3>
                      <p style={{marginBottom: '1.5rem', fontSize: '1.1rem'}}>Get started by adding your first appointment for the day.</p>
                      <button className="action-btn" onClick={() => setIsModalOpen(true)} style={{background: '#8b5cf6', padding: '0.75rem 1.5rem', fontSize: '1.1rem'}}>+ Add New Appointment</button>
                    </div>
                  ) : (
                    <div className="task-list" style={{gap: '1.2rem'}}>
                      {appointments.map((appt) => (
                        <div key={appt.id} className="task-item" style={{background: 'var(--card-bg)', border: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.2rem', paddingLeft: '1.5rem', borderLeftWidth: '6px', borderLeftColor: '#8b5cf6'}}>
                          <div style={{flex: 2}}>
                            <h3 style={{color: 'var(--c-dark)', marginBottom: '0.3rem', fontSize: '1.2rem'}}>{appt.patientName}</h3>
                            <p style={{color: 'var(--text-gray)'}}>{appt.patientAge} yrs â€¢ {appt.patientGender} <span style={{marginLeft: '15px', color: '#8b5cf6'}}>â€¢ Upcoming</span></p>
                          </div>
                          <div style={{textAlign: 'right', flex: 1, paddingRight: '2rem'}}>
                            <div style={{fontSize: '1.1rem', fontWeight: 600, color: '#1e293b'}}>{new Date(appt.appointmentDate).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                            <div style={{color: 'var(--text-gray)', fontSize: '0.85rem'}}>{new Date(appt.appointmentDate).toLocaleDateString()}</div>
                          </div>
                          <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center'}}>
                            <button className="action-btn" onClick={() => router.push(`/consultation/${appt.id}`)} style={{background: '#10b981', padding: '0.5rem 1rem'}}>Start Consultation</button>
                            <button style={{background: 'transparent', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.5rem', cursor: 'pointer', color: '#64748b'}}>...</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {activeTab === 'calendar' && (() => {
            const [year, month] = calendarMonth.split('-').map(Number);
            const firstDay = new Date(year, month - 1, 1).getDay();
            const daysInMonth = new Date(year, month, 0).getDate();
            const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

            const apptsByDay: Record<number, any[]> = {};
            calendarAppointments.forEach(a => {
              const d = new Date(a.appointmentDate);
              if (d.getFullYear() === year && d.getMonth() + 1 === month) {
                const day = d.getDate();
                if (!apptsByDay[day]) apptsByDay[day] = [];
                apptsByDay[day].push(a);
              }
            });

            const prevMonth = () => {
              const d = new Date(year, month - 2, 1);
              setCalendarMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
              setCalendarSelectedDay(null);
            };
            const nextMonth = () => {
              const d = new Date(year, month, 1);
              setCalendarMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
              setCalendarSelectedDay(null);
            };
            const monthLabel = new Date(year, month - 1, 1).toLocaleString('default', { month: 'long', year: 'numeric' });

            const selectedDayAppts = calendarSelectedDay ? (apptsByDay[calendarSelectedDay] || []) : [];

            return (
              <div className="fade-in">
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem'}}>
                  <h1 style={{fontSize: '1.8rem'}}>ðŸ“… My Calendar</h1>
                  <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                    <button onClick={prevMonth} style={{background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.5rem 1rem', cursor: 'pointer', color: 'var(--text-main)', fontSize: '1.1rem'}}>â€¹</button>
                    <span style={{fontWeight: 700, fontSize: '1.1rem', minWidth: '180px', textAlign: 'center'}}>{monthLabel}</span>
                    <button onClick={nextMonth} style={{background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.5rem 1rem', cursor: 'pointer', color: 'var(--text-main)', fontSize: '1.1rem'}}>â€º</button>
                  </div>
                </div>

                <div style={{display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem', alignItems: 'start'}}>
                  <div>
                    {/* Day headers */}
                    <div style={{display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px', marginBottom: '4px'}}>
                      {dayNames.map(d => <div key={d} style={{textAlign: 'center', fontWeight: 700, fontSize: '0.8rem', color: 'var(--text-gray)', padding: '0.5rem 0'}}>{d}</div>)}
                    </div>
                    {/* Calendar grid */}
                    <div style={{display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px'}}>
                      {Array.from({length: firstDay}).map((_, i) => <div key={`e${i}`} />)}
                      {Array.from({length: daysInMonth}).map((_, i) => {
                        const day = i + 1;
                        const dayAppts = apptsByDay[day] || [];
                        const isToday = new Date().getDate() === day && new Date().getMonth() + 1 === month && new Date().getFullYear() === year;
                        const isSelected = calendarSelectedDay === day;
                        return (
                          <div key={day} onClick={() => setCalendarSelectedDay(day === calendarSelectedDay ? null : day)}
                            style={{
                              minHeight: '72px', border: isSelected ? '2px solid #8b5cf6' : isToday ? '2px solid #10b981' : '1px solid var(--border-color)',
                              borderRadius: '10px', padding: '6px', cursor: 'pointer',
                              background: isSelected ? 'rgba(139,92,246,0.08)' : isToday ? 'rgba(16,185,129,0.06)' : 'var(--card-bg)',
                              transition: 'all 0.15s'
                            }}>
                            <div style={{fontWeight: isToday ? 800 : 600, fontSize: '0.85rem', color: isToday ? '#10b981' : 'var(--text-main)', marginBottom: '4px'}}>{day}</div>
                            {dayAppts.slice(0, 2).map((a, idx) => (
                              <div key={idx} style={{background: '#8b5cf6', color: 'white', borderRadius: '4px', padding: '1px 5px', fontSize: '0.68rem', marginBottom: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                                {new Date(a.appointmentDate).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})} {a.patientName}
                              </div>
                            ))}
                            {dayAppts.length > 2 && <div style={{fontSize: '0.68rem', color: '#8b5cf6', fontWeight: 700}}>+{dayAppts.length - 2} more</div>}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Side panel: selected day appointments */}
                  <div style={{background: 'var(--card-bg)', borderRadius: '16px', border: '1px solid var(--border-color)', padding: '1.5rem', minHeight: '300px'}}>
                    <h3 style={{marginBottom: '1rem', fontSize: '1rem', color: 'var(--text-gray)'}}>
                      {calendarSelectedDay ? `Appointments on ${monthLabel.split(' ')[0]} ${calendarSelectedDay}` : 'Select a day to view appointments'}
                    </h3>
                    {calendarSelectedDay ? (
                      selectedDayAppts.length === 0 ? (
                        <div style={{textAlign: 'center', padding: '2rem 0', color: 'var(--text-gray)'}}>
                          <div style={{fontSize: '2rem', marginBottom: '0.5rem'}}>âœ…</div>
                          <p>No appointments this day</p>
                        </div>
                      ) : (
                        <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem'}}>
                          {selectedDayAppts.map((a, i) => (
                            <div key={i} style={{background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: '10px', padding: '0.85rem'}}>
                              <div style={{fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.25rem'}}>{a.patientName}</div>
                              <div style={{fontSize: '0.82rem', color: '#8b5cf6', fontWeight: 600}}>{new Date(a.appointmentDate).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</div>
                              <div style={{fontSize: '0.8rem', color: 'var(--text-gray)', marginTop: '0.25rem'}}>{a.patientAge} yrs â€¢ {a.patientGender}</div>
                            </div>
                          ))}
                        </div>
                      )
                    ) : (
                      <div style={{textAlign: 'center', padding: '2rem 0', color: 'var(--text-gray)'}}>
                        <div style={{fontSize: '2.5rem', marginBottom: '0.5rem', opacity: 0.4}}>ðŸ“…</div>
                        <p>Click any date on the calendar</p>
                      </div>
                    )}
                  </div>
                </div>

                <div style={{marginTop: '1.5rem', display: 'flex', gap: '1.5rem', fontSize: '0.82rem', color: 'var(--text-gray)'}}>
                  <span><span style={{display: 'inline-block', width: '12px', height: '12px', background: '#8b5cf6', borderRadius: '3px', marginRight: '6px'}}></span>Appointment</span>
                  <span><span style={{display: 'inline-block', width: '12px', height: '12px', border: '2px solid #10b981', borderRadius: '3px', marginRight: '6px'}}></span>Today</span>
                </div>
              </div>
            );
          })()}

          {activeTab === 'history' && (
            <div className="fade-in">
              <h1 style={{fontSize: '1.8rem', marginBottom: '1rem'}}>All Consultations Archive</h1>
              <p style={{color: 'var(--text-gray)', marginBottom: '2rem'}}>Searchable archive of every past consultation linked to your account.</p>
              <div className="task-list">
                {history.length === 0 ? <p style={{color: '#94a3b8'}}>No history records found.</p> : history.map((pt, i) => (
                  <div className={`task-item ${i%3===0?'orange':i%3===1?'purple':'teal'}`} key={pt.id} onClick={() => setCurrentPatient(pt)} style={{cursor:'pointer'}}>
                    <div>
                      <h4>{pt.name}</h4>
                      <p>{new Date(pt.date!).toLocaleString()} Â· {pt.gender} Â· {pt.bloodGroup}</p>
                    </div>
                    <div className="circle done"><svg fill="white" viewBox="0 0 24 24" width="16" height="16"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>

        {activeTab === 'history' && (
          <aside className="right-panel">
            <div className="right-header"><h2>Historical Record</h2></div>
            <div className="timeline">
              {currentPatient ? (
                <textarea className="note-textarea-light" value={currentPatient.note} readOnly style={{cursor: 'default'}} />
              ) : (
                <div style={{color: '#94a3b8', textAlign: 'center', marginTop: '10rem'}}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" width="48" height="48" style={{opacity: 0.5, marginBottom: '1rem'}}><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                  <p>Select a historical patient<br/>to view their archived record.</p>
                </div>
              )}
            </div>
          </aside>
        )}
      </div>

      {/* Doctor New Appointment Modal */}
      {isModalOpen && (
        <div style={{position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
          <form onSubmit={handleCreateAppointment} style={{background: 'var(--card-bg)', padding: '2rem', borderRadius: '12px', width: '100%', maxWidth: '500px', display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            <h2>Schedule Appointment</h2>
            <div><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Patient Name*</label><input required type="text" className="form-input" value={newAppt.patientName} onChange={e => setNewAppt({...newAppt, patientName: e.target.value})} /></div>
            <div><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Patient Email*</label><input required type="email" className="form-input" value={newAppt.patientEmail} onChange={e => setNewAppt({...newAppt, patientEmail: e.target.value})} /></div>
            <div style={{display: 'flex', gap: '1rem'}}>
              <div style={{flex: 1}}><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Age*</label><input required type="number" className="form-input" value={newAppt.patientAge} onChange={e => setNewAppt({...newAppt, patientAge: e.target.value})} /></div>
              <div style={{flex: 1}}><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Gender*</label><select required className="form-input" value={newAppt.patientGender} onChange={e => setNewAppt({...newAppt, patientGender: e.target.value})}><option value="" disabled>Select</option><option value="Male">Male</option><option value="Female">Female</option><option value="Other">Other</option></select></div>
            </div>
            <div><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Date & Time*</label><input required type="datetime-local" className="form-input" value={newAppt.appointmentDate} onChange={e => setNewAppt({...newAppt, appointmentDate: e.target.value})} /></div>
            <div style={{display: 'flex', gap: '1rem', marginTop: '1rem'}}>
              <button type="button" className="action-btn" onClick={() => setIsModalOpen(false)} style={{background: '#e2e8f0', color: '#475569', flex: 1}}>Cancel</button>
              <button type="submit" className="action-btn" disabled={isProcessing} style={{flex: 1}}>{isProcessing ? 'Saving...' : 'Book Appointment'}</button>
            </div>
          </form>
        </div>
      )}

      {isQuickScribeOpen && (
        <div style={{position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', zIndex: 2000, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '2rem'}}>
          <div style={{background: '#ffffff', padding: '3rem', borderRadius: '16px', width: '100%', maxWidth: scribeData ? '800px' : '600px', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 20px 50px rgba(0,0,0,0.2)'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <h2 style={{color: '#8b5cf6', margin: 0}}>ðŸŽ™ï¸ Quick AI Scribe</h2>
              <button onClick={() => { setIsQuickScribeOpen(false); if(isDictating) stopQuickScribe(); }} style={{background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: '#94a3b8'}}>&times;</button>
            </div>
            {!scribeData ? (
              <>
                <div style={{padding:'2rem', background:'#f8fafc', borderRadius:'12px', minHeight:'200px', border:'1px solid #e2e8f0', fontSize:'1.1rem', lineHeight:'1.8', color:'#334155'}}>
                  {liveTranscript || <span style={{color:'#94a3b8', fontStyle:'italic'}}>Listening... Walk-in patient consultation. Speak clearly into the microphone.</span>}
                </div>
                {isDictating ? (
                  <button className="action-btn" onClick={stopQuickScribe} disabled={isProcessing} style={{background:'#ef4444', height: '4rem', fontSize: '1.2rem', animation: isProcessing ? 'none' : 'pulse 2s infinite'}}>{isProcessing ? 'Processing AI...' : 'ðŸ›‘ Stop & Process Transcript'}</button>
                ) : (
                  <button className="action-btn" onClick={startQuickScribe} disabled={isProcessing} style={{background:'#10b981', height: '4rem', fontSize: '1.2rem'}}>Start Dictation</button>
                )}
              </>
            ) : (
              <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
                <div style={{display: 'flex', gap: '1rem'}}>
                  <div style={{flex: 1}}><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Patient Name*</label><input required type="text" className="form-input" value={scribeData.name} onChange={e => setScribeData({...scribeData, name: e.target.value})} /></div>
                  <div style={{flex: 1}}><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Patient Email*</label><input required type="email" placeholder="patient@example.com" className="form-input" value={scribeData.patientEmail} onChange={e => setScribeData({...scribeData, patientEmail: e.target.value})} /></div>
                </div>
                <div style={{display: 'flex', gap: '1rem'}}>
                  <div style={{flex: 1}}><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Subjective</label><textarea className="form-input" style={{height:'100px', resize:'vertical'}} value={scribeData.subjective} onChange={e => setScribeData({...scribeData, subjective: e.target.value})} /></div>
                  <div style={{flex: 1}}><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Objective</label><textarea className="form-input" style={{height:'100px', resize:'vertical'}} value={scribeData.objective} onChange={e => setScribeData({...scribeData, objective: e.target.value})} /></div>
                </div>
                <div style={{display: 'flex', gap: '1rem'}}>
                  <div style={{flex: 1}}><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Assessment</label><textarea className="form-input" style={{height:'100px', resize:'vertical'}} value={scribeData.assessment} onChange={e => setScribeData({...scribeData, assessment: e.target.value})} /></div>
                  <div style={{flex: 1}}><label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem'}}>Plan</label><textarea className="form-input" style={{height:'100px', resize:'vertical'}} value={scribeData.plan} onChange={e => setScribeData({...scribeData, plan: e.target.value})} /></div>
                </div>
                <button className="action-btn" onClick={saveQuickScribe} disabled={isProcessing} style={{height: '3.5rem', fontSize: '1.1rem', background: '#10b981', marginTop: '1rem'}}>{isProcessing ? 'Saving...' : 'Save Walk-In Consultation'}</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
