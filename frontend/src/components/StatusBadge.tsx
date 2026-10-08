import React from 'react';

interface StatusBadgeProps {
  status: string;
  isLocked?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, isLocked }) => {
  const normalized = status.toLowerCase().replace(/\s+/g, '_');
  const displayStatus = status.replace(/_/g, ' ').toUpperCase();

  return (
    <span style={{ display: 'inline-flex', gap: '6px', alignItems: 'center' }}>
      <span className={`status-badge ${normalized}`}>
        <span className="status-dot" />
        {displayStatus}
      </span>
      {isLocked && (
        <span className="status-badge locked">
          <span className="status-dot" />
          LOCKED
        </span>
      )}
    </span>
  );
};
