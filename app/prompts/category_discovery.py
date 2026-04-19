CATEGORY_DISCOVERY_SYSTEM = """\
You are an expert document organizer. Analyze collections of documents and identify
meaningful categories that help users find and manage their information.
Always respond with valid JSON only."""

CATEGORY_DISCOVERY_TEMPLATE = """\
Analyze these documents and discover meaningful organization categories.

Documents:
{documents_sample}

Existing categories (do NOT duplicate): {current_categories}

Return exactly this JSON structure:
{{
    "discovered_categories": [
        {{
            "name": "Category Name",
            "description": "What documents belong here",
            "color": "#HEX6CHAR",
            "icon": "single emoji",
            "confidence": 0.85
        }}
    ],
    "insights": "1-2 sentences about patterns observed in the document collection"
}}

Rules:
- Suggest 2-8 NEW categories not in the existing list
- Categories should be broad enough to hold 3+ documents
- Names should be intuitive for non-technical users (e.g. "Financial Records", "Meeting Notes")
- Use distinct hex colors for visual differentiation
- confidence: float 0.0-1.0"""
