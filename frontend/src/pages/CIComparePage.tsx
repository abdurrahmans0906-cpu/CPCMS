import React from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiRequest, SchemaCIOut } from '../api/client';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { DiffViewer } from '../components/DiffViewer';

export const CIComparePage: React.FC = () => {
  const { ciId } = useParams<{ ciId: string }>();
  const [searchParams] = useSearchParams();
  const fromVersionId = searchParams.get('from');
  const toVersionId = searchParams.get('to');

  const { data: ci } = useQuery<SchemaCIOut>({
    queryKey: ['ci', ciId],
    queryFn: () => apiRequest(`/cis/${ciId}`),
    enabled: !!ciId,
  });

  const { data: compareResult, isLoading, error } = useQuery<any>({
    queryKey: ['ci-compare', ciId, fromVersionId, toVersionId],
    queryFn: () => apiRequest(`/cis/${ciId}/compare?from=${fromVersionId}&to=${toVersionId}`),
    enabled: !!ciId && !!fromVersionId && !!toVersionId,
  });

  if (isLoading) return <div>Loading diff...</div>;

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Dashboard', to: '/' },
          { label: ci ? `Team ${ci.team_id}` : 'Team', to: ci ? `/teams/${ci.team_id}` : '#' },
          { label: ci ? `${ci.ci_code} Comparison` : 'Version Comparison' },
        ]}
      />

      <h1>Version Comparison: {ci?.ci_code} ({ci?.name})</h1>

      {error && <div className="banner banner-error">{(error as any).message || 'Failed to compare versions.'}</div>}

      {compareResult && (
        <DiffViewer
          fromMetadata={compareResult.from_metadata}
          toMetadata={compareResult.to_metadata}
          unifiedDiff={compareResult.unified_diff}
          addedCount={compareResult.added_count}
          removedCount={compareResult.removed_count}
          isText={compareResult.is_text}
          message={compareResult.message}
        />
      )}
    </div>
  );
};
