DOCUMENT_ANALYSIS_SYSTEM = """\
You are an expert document analyst with deep experience in knowledge management.
Your task is to analyze documents and extract structured information that helps users
organize, search, and understand their documents.
Always respond with valid JSON only — no explanation, no markdown fences."""

DOCUMENT_ANALYSIS_TEMPLATE = """\
Analyze the following document and return ONLY a valid JSON object.

Filename: {filename}
File type: {file_type}
Content (up to {char_limit} characters):

{text}

Available categories: {categories}

Return exactly this JSON structure:
{{
    "summary": "3-5 sentence summary of the document",
    "key_points": ["key point 1", "key point 2", "key point 3"],
    "entities": {{
        "people": ["name1", "name2"],
        "organizations": ["org1", "org2"],
        "dates": ["date1", "date2"],
        "locations": ["loc1", "loc2"]
    }},
    "action_items": ["action 1", "action 2"],
    "tags": ["tag1", "tag2", "tag3"],
    "suggested_category": "best matching category name",
    "category_confidence": 0.85,
    "document_type": "contract|invoice|report|email|meeting_notes|presentation|spreadsheet|other",
    "sentiment": "positive|neutral|negative",
    "is_time_sensitive": false,
    "estimated_importance": 0.7,
    "timeline_events": [
        {
            "title": "Contract term",
            "description": "Optional detail",
            "date": "2026-05-15",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "confidence": 0.88,
            "source_quote": "Optional supporting quote from the document",
            "page_number": 2,
            "category": "contract_period",
            "source": "extracted"
        }
    ]
}}

Rules:
- summary: 3-5 complete sentences describing the document
- key_points: 3-7 most important facts or conclusions
- tags: 3-8 relevant lowercase single-word or short-phrase tags
- suggested_category: choose from available categories or propose a new descriptive one
- category_confidence: float 0.0-1.0 indicating confidence in the category
- estimated_importance: float 0.0-1.0"""


def build_document_analysis_prompt(
    *,
    filename: str,
    file_type: str,
    char_limit: int,
    text: str,
    categories: str,
) -> str:
    """Render the AI analysis prompt without using str.format on JSON braces."""

    prompt = DOCUMENT_ANALYSIS_TEMPLATE
    replacements = {
        "{filename}": filename,
        "{file_type}": file_type,
        "{char_limit}": str(char_limit),
        "{text}": text,
        "{categories}": categories,
    }
    for token, value in replacements.items():
        prompt = prompt.replace(token, value)
    return prompt


# Timeline extraction rules
# - Extract explicit dates and date ranges for: effective dates, contract periods, project periods, deadlines, invoice dates, due dates, meeting/review/renewal/termination/delivery dates.
# - Prefer ISO-8601 dates (YYYY-MM-DD).
# - Use date for milestones; use start_date/end_date for ranges.
# - Include confidence 0.0-1.0 and source_quote/page_number when available.
# - If nothing is found, return an empty timeline_events array.
