import React, { useState } from 'react';

export interface DiffViewerProps {
  fromMetadata: Record<string, any>;
  toMetadata: Record<string, any>;
  unifiedDiff: string | null;
  addedCount: number;
  removedCount: number;
  isText: boolean;
  message?: string | null;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  fromMetadata,
  toMetadata,
  unifiedDiff,
  addedCount,
  removedCount,
  isText,
  message,
}) => {
  const [viewMode, setViewMode] = useState<'unified' | 'side-by-side'>('unified');

  const lines = unifiedDiff ? unifiedDiff.split('\n') : [];

  return (
    <div style={{ margin: '12px 0' }}>
      <div className="panel" style={{ marginBottom: '16px' }}>
        <div className="panel-header">
          <h2>Metadata Comparison</h2>
        </div>
        <table>
          <thead>
            <tr>
              <th style={{ width: '160px' }}>Attribute</th>
              <th>v{fromMetadata.version_label} (From)</th>
              <th>v{toMetadata.version_label} (To)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>File Name</strong></td>
              <td>{fromMetadata.original_name}</td>
              <td>{toMetadata.original_name}</td>
            </tr>
            <tr>
              <td><strong>File Size</strong></td>
              <td>{fromMetadata.size_bytes} bytes</td>
              <td>{toMetadata.size_bytes} bytes</td>
            </tr>
            <tr>
              <td><strong>SHA-256 Hash</strong></td>
              <td><code>{fromMetadata.sha256?.substring(0, 16)}...</code></td>
              <td><code>{toMetadata.sha256?.substring(0, 16)}...</code></td>
            </tr>
            <tr>
              <td><strong>Author</strong></td>
              <td>{fromMetadata.author}</td>
              <td>{toMetadata.author}</td>
            </tr>
            <tr>
              <td><strong>Timestamp</strong></td>
              <td>{fromMetadata.date ? new Date(fromMetadata.date).toLocaleString() : '-'}</td>
              <td>{toMetadata.date ? new Date(toMetadata.date).toLocaleString() : '-'}</td>
            </tr>
            <tr>
              <td><strong>Change Description</strong></td>
              <td>{fromMetadata.description}</td>
              <td>{toMetadata.description}</td>
            </tr>
            <tr>
              <td><strong>Git Commit SHA</strong></td>
              <td>{fromMetadata.commit_sha ? <code>{fromMetadata.commit_sha.substring(0, 7)}</code> : 'None'}</td>
              <td>{toMetadata.commit_sha ? <code>{toMetadata.commit_sha.substring(0, 7)}</code> : 'None'}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>File Line Differences</h2>
          {isText && (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span className="status-badge approved">
                +{addedCount} ADDED
              </span>
              <span className="status-badge rejected">
                -{removedCount} REMOVED
              </span>
              <div style={{ display: 'flex', gap: '4px', marginLeft: '8px' }}>
                <button
                  type="button"
                  className={viewMode === 'unified' ? 'primary' : ''}
                  onClick={() => setViewMode('unified')}
                >
                  Unified
                </button>
                <button
                  type="button"
                  className={viewMode === 'side-by-side' ? 'primary' : ''}
                  onClick={() => setViewMode('side-by-side')}
                >
                  Side by Side
                </button>
              </div>
            </div>
          )}
        </div>

        {!isText ? (
          <p style={{ color: 'var(--muted-text)', fontStyle: 'italic', margin: 0 }}>
            {message || 'Binary files: line-by-line diff is not available.'}
          </p>
        ) : lines.length === 0 ? (
          <p style={{ color: 'var(--muted-text)', margin: 0 }}>No text differences detected between these versions.</p>
        ) : viewMode === 'unified' ? (
          <div className="diff-container" data-testid="unified-diff">
            {lines.map((line, idx) => {
              let lineClass = '';
              if (line.startsWith('+') && !line.startsWith('+++')) lineClass = 'diff-line-add';
              else if (line.startsWith('-') && !line.startsWith('---')) lineClass = 'diff-line-remove';
              else if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) lineClass = 'diff-line-info';
              return (
                <div key={idx} className={lineClass}>
                  {line}
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <h3>v{fromMetadata.version_label}</h3>
              <div className="diff-container">
                {lines
                  .filter((l) => !l.startsWith('+') || l.startsWith('+++'))
                  .map((line, idx) => (
                    <div
                      key={idx}
                      className={line.startsWith('-') && !line.startsWith('---') ? 'diff-line-remove' : ''}
                    >
                      {line}
                    </div>
                  ))}
              </div>
            </div>
            <div>
              <h3>v{toMetadata.version_label}</h3>
              <div className="diff-container">
                {lines
                  .filter((l) => !l.startsWith('-') || l.startsWith('---'))
                  .map((line, idx) => (
                    <div
                      key={idx}
                      className={line.startsWith('+') && !line.startsWith('+++') ? 'diff-line-add' : ''}
                    >
                      {line}
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
