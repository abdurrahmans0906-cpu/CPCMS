import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { DiffViewer } from '../components/DiffViewer';

describe('DiffViewer Component', () => {
  const fromMeta = {
    version_label: '1.0',
    original_name: 'srs_v1.md',
    size_bytes: 120,
    sha256: 'abc1234567890def1234567890',
    author: 'Rahul Sharma',
    date: '2026-09-01T10:00:00Z',
    description: 'Initial SRS draft',
    commit_sha: 'a1b2c3d',
  };

  const toMeta = {
    version_label: '1.1',
    original_name: 'srs_v2.md',
    size_bytes: 150,
    sha256: 'fed0987654321cba0987654321',
    author: 'Priya Nair',
    date: '2026-09-05T12:00:00Z',
    description: 'Added authentication requirements',
    commit_sha: 'e5f6g7h',
  };

  const unifiedDiffSample = `--- v1.0
+++ v1.1
@@ -1,3 +1,4 @@
 # Software Requirements
-Old introduction section
+Updated introduction section
+Section 2: Authentication Requirements`;

  it('renders metadata comparison correctly', () => {
    render(
      <DiffViewer
        fromMetadata={fromMeta}
        toMetadata={toMeta}
        unifiedDiff={unifiedDiffSample}
        addedCount={2}
        removedCount={1}
        isText={true}
      />
    );

    expect(screen.getByText('Metadata Comparison')).toBeDefined();
    expect(screen.getByText('v1.0 (From)')).toBeDefined();
    expect(screen.getByText('v1.1 (To)')).toBeDefined();
    expect(screen.getByText('srs_v1.md')).toBeDefined();
    expect(screen.getByText('srs_v2.md')).toBeDefined();
    expect(screen.getByText('+2 added, -1 removed')).toBeDefined();
  });

  it('toggles between unified and side-by-side diff modes', () => {
    render(
      <DiffViewer
        fromMetadata={fromMeta}
        toMetadata={toMeta}
        unifiedDiff={unifiedDiffSample}
        addedCount={2}
        removedCount={1}
        isText={true}
      />
    );

    const sideBySideBtn = screen.getByText('Side by Side');
    fireEvent.click(sideBySideBtn);

    expect(screen.getByText('v1.0')).toBeDefined();
    expect(screen.getByText('v1.1')).toBeDefined();
  });

  it('displays binary file message when isText is false', () => {
    render(
      <DiffViewer
        fromMetadata={fromMeta}
        toMetadata={toMeta}
        unifiedDiff={null}
        addedCount={0}
        removedCount={0}
        isText={false}
        message="Binary files cannot be diffed textually."
      />
    );

    expect(screen.getByText('Binary files cannot be diffed textually.')).toBeDefined();
  });
});
