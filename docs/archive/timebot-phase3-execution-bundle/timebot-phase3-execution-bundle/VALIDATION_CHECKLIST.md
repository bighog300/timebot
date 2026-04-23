# Validation Checklist

## Search
- [ ] plain text search returns ranked results
- [ ] filters work together: category + source + date + file type + favorite
- [ ] facets return counts that match filtered corpus
- [ ] suggestions return stable autocomplete values
- [ ] snippets/highlights are populated for matched text

## Semantic and hybrid search
- [ ] semantic search returns relevant fuzzy matches
- [ ] similar-documents endpoint excludes the source document from final response
- [ ] hybrid search works with Qdrant enabled
- [ ] hybrid search degrades gracefully with Qdrant disabled
- [ ] result deduplication preserves best score explanation

## Relationships
- [ ] relationship detection writes `DocumentRelationship` rows
- [ ] duplicate pairs are flagged with a stronger confidence threshold
- [ ] repeated runs do not create duplicate rows
- [ ] related-documents endpoint can filter by relationship type

## Timeline
- [ ] timeline endpoint supports day/week/month grouping
- [ ] documents with no extracted dates fall back to upload date
- [ ] category/source filters change the timeline output correctly

## Insights
- [ ] overview endpoint returns dashboard aggregates
- [ ] duplicate insights expose cluster counts
- [ ] relationship insights expose top clusters or connected components
- [ ] category analytics expose distribution and drift/refinement suggestions

## Operations
- [ ] embeddings can be backfilled for all existing documents
- [ ] relationships can be backfilled safely
- [ ] all new env/config requirements are documented
- [ ] new tests pass locally or in Docker
