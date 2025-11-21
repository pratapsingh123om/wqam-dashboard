import React from 'react';

interface DashboardHeaderProps {
  modelPath: string; // This will likely be a prop or state from App.tsx
  onDownloadSampleReport: () => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ modelPath, onDownloadSampleReport }) => {
  return (
    <div style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#e6eef6' }}>
      <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
        <img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='36' height='36' viewBox='0 0 24 24' fill='%237c3aed'><path d='M12 2L2 7v10l10 5 10-5V7z'/></svg>" alt="logo" style={{ borderRadius: '8px' }} />
        <div>
          <div style={{ fontWeight: '800' }}>WQAM Dashboard — Demo</div>
          <div className="small muted">Water Quality AI Monitoring — dark demo</div>
        </div>
      </div>
      <div className="top-actions">
        <div className="small muted">Model file (placeholder):</div>
        <div style={{ fontFamily: 'monospace', background: 'rgba(255,255,255,0.02)', padding: '6px 10px', borderRadius: '8px', fontSize: '0.85rem', color: '#cfe8ff' }} id="modelPath">{modelPath}</div>
        <button onClick={onDownloadSampleReport} className="btn-primary">Download sample report</button>
      </div>
    </div>
  );
};

export default DashboardHeader;
