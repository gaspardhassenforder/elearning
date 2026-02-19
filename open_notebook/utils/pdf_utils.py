"""PDF page boundary extraction utilities.

Uses PyMuPDF (fitz) to extract per-page text offsets from PDF files,
enabling mapping of text chunks to their originating page numbers.
"""

from typing import Optional

from loguru import logger


def extract_page_texts(file_path: str) -> list[tuple[int, str]]:
    """Extract text content per page from a PDF file.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        List of (page_number, page_text) tuples where page_number is 1-indexed.
        Returns empty list if file is not a PDF or extraction fails.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF (fitz) not available - page number extraction disabled")
        return []

    try:
        doc = fitz.open(file_path)
        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages.append((page_num + 1, text))  # 1-indexed
        doc.close()
        logger.debug(f"Extracted text from {len(pages)} pages of {file_path}")
        return pages
    except Exception as e:
        logger.warning(f"Failed to extract page texts from {file_path}: {e}")
        return []


def determine_page_number(
    chunk_text: str,
    page_texts: list[tuple[int, str]],
    match_length: int = 80,
) -> Optional[int]:
    """Determine which PDF page a text chunk belongs to.

    Uses the first N characters of the chunk to find its originating page
    via substring matching against per-page text content.

    Args:
        chunk_text: The text chunk to locate.
        page_texts: List of (page_number, page_text) from extract_page_texts().
        match_length: Number of characters from chunk start to use for matching.

    Returns:
        1-indexed page number, or None if no match found.
    """
    if not page_texts or not chunk_text:
        return None

    # Use the first N chars of the chunk as a search anchor
    anchor = chunk_text[:match_length].strip()
    if not anchor:
        return None

    # Normalize whitespace for fuzzy matching
    anchor_normalized = " ".join(anchor.split()).lower()

    for page_num, page_text in page_texts:
        page_normalized = " ".join(page_text.split()).lower()
        if anchor_normalized in page_normalized:
            return page_num

    # Fallback: try with shorter anchor (40 chars) for better fuzzy matching
    if match_length > 40:
        short_anchor = " ".join(chunk_text[:40].strip().split()).lower()
        if short_anchor:
            for page_num, page_text in page_texts:
                page_normalized = " ".join(page_text.split()).lower()
                if short_anchor in page_normalized:
                    return page_num

    return None
