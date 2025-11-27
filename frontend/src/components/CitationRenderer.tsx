import { useEffect, useMemo, useState } from 'react';
import type { Citation } from '../types';

interface CitationRendererProps {
  citations: Citation[];
}

export function CitationRenderer({ citations }: CitationRendererProps) {
  const [activeId, setActiveId] = useState<string | null>(null);

  const cleanedCitations = useMemo(
    () => citations.filter((citation) => !!citation?.source_file),
    [citations]
  );

  useEffect(() => {
    setActiveId(cleanedCitations[0]?.id ?? null);
  }, [cleanedCitations]);

  if (!cleanedCitations || cleanedCitations.length === 0) {
    return null;
  }

  const activeCitation = cleanedCitations.find((citation) => citation.id === activeId);

  return (
    <div className="citations compact">
      <div className="citations-header">
        <strong>Sources ({cleanedCitations.length})</strong>
        <span>Tap a chip to preview the snippet.</span>
      </div>
      <div className="citations-pills">
        {cleanedCitations.map((citation) => (
          <button
            key={citation.id}
            type="button"
            className={`citation-pill ${citation.id === activeId ? 'active' : ''}`}
            onClick={() => setActiveId(citation.id)}
          >
            <span className="citation-pill__file">{citation.source_file}</span>
            <span className="citation-pill__page">Pg {citation.page_number}</span>
          </button>
        ))}
      </div>
      {activeCitation && (
        <div className="citation-snippet-card">
          <p className="snippet-label">Highlighted text</p>
          <p className="citation-snippet">{activeCitation.snippet}</p>
        </div>
      )}
    </div>
  );
}

