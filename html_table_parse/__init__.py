__version__ = '0.2.1'

from collections import defaultdict as _defaultdict
from functools import partial as _partial
from re import compile as _rc

from lxml import html as _html

normalize_spaces = _partial(_rc(r'\s+').sub, ' ')


def to_list(html_str: str, index: int = 0) -> list[list]:
    """Parse HTML table and return as list of lists (rows)."""
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
    """Parse a single table element into rows of data with colspan/rowspan support."""
    rows = table_element.xpath('.//tr')

    if not rows:
        return []

    # Determine if first row is a header (contains any th)
    first_row_cells = rows[0].xpath('.//td | .//th')
    has_header = any(cell.tag == 'th' for cell in first_row_cells)

    # Parse all rows with colspan/rowspan support
    parsed_rows = []
    rowspan_map = {}  # (col_index) -> remaining_rowspan

    for row_idx, row in enumerate(rows):
        cells = row.xpath('.//td | .//th')
        row_data = []
        col_idx = 0

        # Handle active rowspans from previous rows
        while col_idx in rowspan_map and rowspan_map[col_idx] > 0:
            row_data.append('')
            rowspan_map[col_idx] -= 1
            if rowspan_map[col_idx] == 0:
                del rowspan_map[col_idx]
            col_idx += 1

        for cell in cells:
            # Skip to next available column if rowspan is active
            while col_idx in rowspan_map and rowspan_map[col_idx] > 0:
                row_data.append('')
                rowspan_map[col_idx] -= 1
                if rowspan_map[col_idx] == 0:
                    del rowspan_map[col_idx]
                col_idx += 1

            # Get cell properties
            text = _clean_text(cell)
            colspan = int(cell.get('colspan', 1))
            rowspan = int(cell.get('rowspan', 1))

            # Add the cell text (colspan times)
            for _ in range(colspan):
                row_data.append(text)

            # Handle rowspan
            if rowspan > 1:
                for i in range(colspan):
                    rowspan_map[col_idx + i] = rowspan - 1

            col_idx += colspan

        # Check if this row should be a header
        is_header_row = row_idx == 0 and has_header

        # Only add non-empty rows (or header rows)
        if any(row_data) or is_header_row:
            parsed_rows.append(row_data)

    return parsed_rows


def _clean_text(element) -> str:
    """Extract and clean text from an HTML element."""
    if element is None:
        return ''
    text = element.text_content()
    text = normalize_spaces(text).strip()
    return text


def to_dict(html: str, index: int = 0) -> dict[str, list]:
    """
    Uses first row as headers.
    Returns a dictionary with column names as keys and lists of values as values.
    Handles duplicate headers by appending numbers.
    """
    rows = to_list(html, index)

    if not rows:
        return {}

    headers = rows[0]
    data_rows = rows[1:]

    # Handle duplicate headers by making them unique
    unique_headers = []
    header_count = _defaultdict(int)

    for header in headers:
        if header_count[header] > 0:
            unique_header = f'{header}_{header_count[header] + 1}'
        else:
            unique_header = header
        unique_headers.append(unique_header)
        header_count[header] += 1

    result = {header: [] for header in unique_headers}

    for row in data_rows:
        padded_row = row + [''] * (len(unique_headers) - len(row))
        padded_row = padded_row[: len(unique_headers)]

        for header, value in zip(unique_headers, padded_row):
            result[header].append(value)

    return result


def to_dicts(html: str, index: int = 0) -> list[dict]:
    """
    Returns a list of dicts, one per data row, using first row as headers.
    Handles duplicate headers by numbering them.
    """
    rows = to_list(html, index)

    if not rows:
        return []

    headers = rows[0]
    data_rows = rows[1:]

    # Make headers unique
    unique_headers = []
    header_count = _defaultdict(int)

    for header in headers:
        if header_count[header] > 0:
            unique_header = f'{header}_{header_count[header] + 1}'
        else:
            unique_header = header
        unique_headers.append(unique_header)
        header_count[header] += 1

    result = []
    for row in data_rows:
        padded_row = row + [''] * (len(unique_headers) - len(row))
        padded_row = padded_row[: len(unique_headers)]
        result.append(dict(zip(unique_headers, padded_row)))

    return result
