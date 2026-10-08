import React from 'react';

interface StatusBadgeProps {
  status: string;
  isLocked?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, isLocked }) => {
  const normalized = status.toLowerCase().replace(/\s+/g, '_');
  const displayStatus = status.toUpperCase();

  return (
    <span style={{ display: 'inline-flex', gap: '4px', alignItems: 'center' }}>
      <span className={`status-badge ${normalized}`}>
        {displayStatus}
      </span>
      {isLocked && (
        <span className="status-badge locked">
          LOCKED
        </span>
      )}
    </span>
  );
};
