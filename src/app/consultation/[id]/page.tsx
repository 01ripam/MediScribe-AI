'use client';

import { useState, useEffect, useRef, use } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';

export default function ConsultationWorkspace({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  
  const router = useRouter();
  const { data: session, status } = useSession();
  const [appointment, setAppointment] = useState<any>(null);
  const [isDictating, setIsDictating] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [manualData, setManualData] = useState({ subjective: '', objective: '', assessment: '', plan: '' });
  const [activeMode, setActiveMode] = useState<'IDLE'|'MANUAL'|'AI'>('IDLE');
  const [isProcessing, setIsProcessing] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (status === 'unauthenticated' || (session?.user as any)?.role !== 'DOCTOR') {
      router.push('/');
      return;
    }
    fetch(`/api/appointments/${id}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) router.push('/');
        else setAppointment(data);
      });
  }, [id, status, session, router]);

  const startDictation = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert("Your browser does not support Speech Recognition. Please use Chrome.");
      return;
    }
    
    setActiveMode('AI');
    const SpeechRecognition = (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let currentTranscript = '';
      for (let i = 0; i < event.results.length; i++) {
        currentTranscript += event.results[i][0].transcript;
      }
      setLiveTranscript(currentTranscript);
    };

    recognition.onerror = (event: any) => console.error("Speech error", event);
    
    recognition.start();
    recognitionRef.current = recognition;
    setIsDictating(true);
  };

  const stopDictation = async () => {
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

        setManualData({
          subjective: aiData.subjective || '',
          objective: aiData.objective || '',
          assessment: aiData.assessment || '',
          plan: aiData.plan || ''
        });
        
        setActiveMode('MANUAL'); // Switch to manual edit mode for review
      } catch (err: any) {
        alert("Failed to process transcript: " + err.message);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const saveConsultation = async () => {
    setIsProcessing(true);
    try {
      // 1. Save Consultation
      const consultRes = await fetch('/api/patients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: appointment.patientName,
          patientEmail: appointment.patientEmail,
          age: appointment.patientAge,
          gender: appointment.patientGender,
          ...manualData
        })
      });
      const consultData = await consultRes.json();
      if (!consultRes.ok) throw new Error(consultData.error);

      // 2. Patch Appointment
      await fetch(`/api/appointments/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'COMPLETED', consultationId: consultData.patient.id })
      });

      router.push('/');
    } catch (err: any) {
      alert("Error saving: " + err.message);
      setIsProcessing(false);
    }
  };

  if (!appointment) return <div style={{padding:'3rem', textAlign:'center'}}>Loading Workspace...</div>;

  return (
    <div className="app-window" style={{ display: 'flex' }}>
      {/* Left Sidebar (Acts as full-screen splash initially) */}
      <aside 
        className="sidebar" 
        style={{ 
          width: activeMode === 'IDLE' ? '100%' : '350px', 
          background: activeMode === 'IDLE' ? '#ffffff' : '#f8fafc', 
          padding: activeMode === 'IDLE' ? '5rem' : '2rem',
          transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: activeMode === 'IDLE' ? 'center' : 'stretch',
          justifyContent: activeMode === 'IDLE' ? 'center' : 'flex-start',
          borderRight: activeMode === 'IDLE' ? 'none' : '1px solid #e2e8f0'
        }}
      >
        <div style={{ textAlign: activeMode === 'IDLE' ? 'center' : 'left', maxWidth: '600px', width: '100%', transition: 'all 0.3s ease' }}>
          <h2 style={{color: '#0f172a', marginBottom: '2rem', fontSize: activeMode === 'IDLE' ? '2rem' : '1.5rem'}}>Consultation Workspace</h2>
          
          <div style={{background:'white', padding:'1.5rem', borderRadius:'12px', boxShadow: activeMode === 'IDLE' ? '0 10px 25px rgba(0,0,0,0.1)' : '0 4px 6px rgba(0,0,0,0.05)', marginBottom:'2rem', border: '1px solid #e2e8f0'}}>
            <p style={{fontSize:'0.8rem', color:'#64748b', textTransform:'uppercase'}}>Patient</p>
            <h3 style={{fontSize:'1.4rem', color:'#1e293b', marginBottom:'0.5rem'}}>{appointment.patientName}</h3>
            <p style={{fontSize:'0.9rem', color:'#475569'}}>{appointment.patientAge} years old • {appointment.patientGender}</p>
            <p style={{fontSize:'0.85rem', color:'#94a3b8', marginTop:'0.5rem'}}>{new Date(appointment.appointmentDate).toLocaleString()}</p>
          </div>

          <div style={{display:'flex', flexDirection: activeMode === 'IDLE' ? 'row' : 'column', gap:'1rem', justifyContent: 'center'}}>
            <button className="action-btn" onClick={() => setActiveMode('MANUAL')} style={{background:'#f1f5f9', color:'#334155', flex: 1, padding: '1rem'}}>✏️ Start Manual Note</button>
            
            {isDictating ? (
               <button className="action-btn" onClick={stopDictation} style={{background:'#ef4444', animation:'pulse 2s infinite', flex: 1, padding: '1rem'}}>🛑 Stop</button>
            ) : (
               <button className="action-btn" onClick={startDictation} style={{background:'#8b5cf6', flex: 1, padding: '1rem'}}>🎙️ Start AI Scribe</button>
            )}
          </div>
        </div>
      </aside>

      {/* Right Canvas (Slides in) */}
      <main 
        className="main-area" 
        style={{ 
          background: '#ffffff', 
          padding: '3rem', 
          flex: activeMode === 'IDLE' ? 0 : 1, 
          overflowY: 'auto',
          opacity: activeMode === 'IDLE' ? 0 : 1,
          transform: activeMode === 'IDLE' ? 'translateX(100px)' : 'translateX(0)',
          pointerEvents: activeMode === 'IDLE' ? 'none' : 'auto',
          transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          display: activeMode === 'IDLE' ? 'none' : 'block'
        }}
      >
        {activeMode === 'AI' && (
          <div style={{maxWidth: '800px', margin: '0 auto'}}>
            <h2 style={{color:'#8b5cf6', marginBottom:'1rem', display:'flex', alignItems:'center', gap:'10px'}}>
              <span style={{display:'inline-block', width:'12px', height:'12px', background:'#ef4444', borderRadius:'50%', animation:'pulse 1.5s infinite'}}/> 
              Live Transcript
            </h2>
            <div style={{padding:'2rem', background:'#f8fafc', borderRadius:'16px', minHeight:'300px', border:'1px solid #e2e8f0', fontSize:'1.1rem', lineHeight:'1.8', color:'#334155'}}>
               {liveTranscript || <span style={{color:'#94a3b8', fontStyle:'italic'}}>Listening... Make sure to speak clearly into the microphone.</span>}
            </div>
            {isProcessing && <div style={{marginTop:'2rem', textAlign:'center', color:'#64748b'}}>Processing SOAP Note via Gemini AI...</div>}
          </div>
        )}

        {activeMode === 'MANUAL' && (
          <div style={{maxWidth: '800px', margin: '0 auto'}}>
            <h2 style={{color:'#1e293b', marginBottom:'2rem'}}>Clinical Note Editor</h2>
            
            <div style={{display:'flex', flexDirection:'column', gap:'1.5rem'}}>
              <div>
                <label style={{display:'block', fontWeight:600, marginBottom:'0.5rem', color:'#475569'}}>Subjective (S)</label>
                <textarea className="form-input" style={{height:'120px', resize:'vertical'}} value={manualData.subjective} onChange={e => setManualData({...manualData, subjective: e.target.value})} />
              </div>
              <div>
                <label style={{display:'block', fontWeight:600, marginBottom:'0.5rem', color:'#475569'}}>Objective (O)</label>
                <textarea className="form-input" style={{height:'120px', resize:'vertical'}} value={manualData.objective} onChange={e => setManualData({...manualData, objective: e.target.value})} />
              </div>
              <div>
                <label style={{display:'block', fontWeight:600, marginBottom:'0.5rem', color:'#475569'}}>Assessment (A)</label>
                <textarea className="form-input" style={{height:'120px', resize:'vertical'}} value={manualData.assessment} onChange={e => setManualData({...manualData, assessment: e.target.value})} />
              </div>
              <div>
                <label style={{display:'block', fontWeight:600, marginBottom:'0.5rem', color:'#475569'}}>Plan (P)</label>
                <textarea className="form-input" style={{height:'120px', resize:'vertical'}} value={manualData.plan} onChange={e => setManualData({...manualData, plan: e.target.value})} />
              </div>

              <button className="action-btn" onClick={saveConsultation} disabled={isProcessing} style={{marginTop:'2rem', background:'#10b981', padding:'1rem', fontSize:'1.1rem'}}>
                {isProcessing ? 'Saving...' : 'Save & Complete Appointment'}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
