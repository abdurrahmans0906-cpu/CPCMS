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
      <div className="panel" style={{ marginBottom: '12px' }}>
        <h2>Metadata Comparison</h2>
        <table>
          <thead>
            <tr>
              <th style={{ width: '150px' }}>Attribute</th>
              <th>v{fromMetadata.version_label} (From)</th>
              <th>v{toMetadata.version_label} (To)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>File Name</td>
              <td>{fromMetadata.original_name}</td>
              <td>{toMetadata.original_name}</td>
            </tr>
            <tr>
              <td>File Size</td>
              <td>{fromMetadata.size_bytes} bytes</td>
              <td>{toMetadata.size_bytes} bytes</td>
            </tr>
            <tr>
              <td>SHA-256 Hash</td>
              <td><code>{fromMetadata.sha256?.substring(0, 16)}...</code></td>
              <td><code>{toMetadata.sha256?.substring(0, 16)}...</code></td>
            </tr>
            <tr>
              <td>Author</td>
              <td>{fromMetadata.author}</td>
              <td>{toMetadata.author}</td>
            </tr>
            <tr>
              <td>Date</td>
              <td>{fromMetadata.date ? new Date(fromMetadata.date).toLocaleString() : '-'}</td>
              <td>{toMetadata.date ? new Date(toMetadata.date).toLocaleString() : '-'}</td>
            </tr>
            <tr>
              <td>Change Description</td>
              <td>{fromMetadata.description}</td>
              <td>{toMetadata.description}</td>
            </tr>
            <tr>
              <td>Git Commit SHA</td>
              <td>{fromMetadata.commit_sha ? <code>{fromMetadata.commit_sha.substring(0, 7)}</code> : 'None'}</td>
              <td>{toMetadata.commit_sha ? <code>{toMetadata.commit_sha.substring(0, 7)}</code> : 'None'}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h2>File Line Differences</h2>
          {isText && (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>
                +{addedCount} added, -{removedCount} removed
              </span>
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
          )}
        </div>

        {!isText ? (
          <p style={{ color: 'var(--muted-text)', fontStyle: 'italic' }}>
            {message || 'Binary files: line-by-line diff is not available.'}
          </p>
        ) : lines.length === 0 ? (
          <p style={{ color: 'var(--muted-text)' }}>No text differences detected between these versions.</p>
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
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
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
