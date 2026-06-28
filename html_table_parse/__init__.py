__version__ = '0.0.1.dev0'

from functools import partial as _partial
from re import compile as _rc

from lxml import html as _html

normalize_spaces = _partial(_rc(r'\s+').sub, ' ')


def to_list(html_str: str, index: int = 0) -> list[list]:
    """
    Parse HTML table and return as list of lists (rows).
    Uses lxml for robust HTML parsing.

    Args:
        html_str: HTML string containing table(s)
        index: Which table to extract (0-based)

    Returns:
        List of rows, where each row is a list of cell values
    """
    tree = _html.fromstring(html_str)
    tables = tree.xpath('//table')

    if not tables:
        raise ValueError('No tables found in HTML')

    if index >= len(tables):
        raise ValueError(
            f'Table index {index} out of range (found {len(tables)} tables)'
        )

    table = tables[index]
    return _parse_table(table)


def _parse_table(table_element) -> list[list]:
    """Parse a single table element into rows of data."""

    # First, find all rows
    rows = table_element.xpath('.//tr')

    if not rows:
        return []

    # Check if there's a header (th) in the first row
    header_row = rows[0]
    header_cells = header_row.xpath('.//th')

    data_rows = []

    # Parse header row if it exists
    if header_cells:
        headers = [_clean_text(cell) for cell in header_cells]
        data_rows.append(headers)
        # Start from second row for data
        rows_to_parse = rows[1:]
    else:
        rows_to_parse = rows

    # Parse data rows
    for row in rows_to_parse:
        cells = row.xpath('.//td | .//th')
        row_data = [_clean_text(cell) for cell in cells]

        # Skip empty rows
        if any(row_data):
            data_rows.append(row_data)

    return data_rows


def _clean_text(element) -> str:
    """Extract and clean text from an HTML element."""
    if element is None:
        return ''

    # Get text content
    text = element.text_content()

    # Clean up whitespace and normalize
    text = normalize_spaces(text).strip()

    return text


def to_dict(html: str, index: int = 0) -> dict[str, list]:
    """
    Uses first row as headers.
    Returns a dictionary with column names as keys and lists of values as values.
    """
    rows = to_list(html, index)

    if not rows:
        return {}

    # First row is headers
    headers = rows[0]
    data_rows = rows[1:]

    # Initialize dictionary with empty lists for each header
    result = {header: [] for header in headers}

    # Fill in data
    for row in data_rows:
        # Pad row if it's shorter than headers (missing cells)
        padded_row = row + [''] * (len(headers) - len(row))
        # Truncate if longer (extra cells)
        padded_row = padded_row[: len(headers)]

        # Add each value to its corresponding column
        for header, value in zip(headers, padded_row):
            result[header].append(value)

    return result
