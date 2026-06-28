import pytest

from html_table_parse import normalize_spaces, to_dict, to_list


class TestNormalizeSpaces:
    """Tests for the normalize_spaces function."""

    def test_basic_whitespace(self):
        assert normalize_spaces('hello   world') == 'hello world'
        assert normalize_spaces('hello\t\tworld') == 'hello world'
        assert normalize_spaces('hello\n\nworld') == 'hello world'
        assert normalize_spaces('  hello  world  ') == ' hello world '

    def test_multiple_spaces(self):
        assert normalize_spaces('a    b     c') == 'a b c'

    def test_empty_string(self):
        assert normalize_spaces('') == ''
        assert normalize_spaces('   ') == ' '


class TestToList:
    """Tests for the to_list function."""

    def test_simple_table(self):
        html = """
        <table>
            <tr><th>Name</th><th>Age</th><th>City</th></tr>
            <tr><td>Alice</td><td>30</td><td>NYC</td></tr>
            <tr><td>Bob</td><td>25</td><td>LA</td></tr>
        </table>
        """
        expected = [
            ['Name', 'Age', 'City'],
            ['Alice', '30', 'NYC'],
            ['Bob', '25', 'LA'],
        ]
        assert to_list(html) == expected

    def test_table_without_headers(self):
        html = """
        <table>
            <tr><td>Alice</td><td>30</td><td>NYC</td></tr>
            <tr><td>Bob</td><td>25</td><td>LA</td></tr>
        </table>
        """
        expected = [['Alice', '30', 'NYC'], ['Bob', '25', 'LA']]
        assert to_list(html) == expected

    def test_table_with_mixed_th_and_td(self):
        html = """
        <table>
            <tr><th>Name</th><th>Age</th><td>City</td></tr>
            <tr><td>Alice</td><td>30</td><td>NYC</td></tr>
        </table>
        """
        # The first row has mixed th/td, but our parser only checks if ALL are th
        # So this will treat the first row as data, not headers
        expected = [['Name', 'Age', 'City'], ['Alice', '30', 'NYC']]
        assert to_list(html) == expected

    def test_table_with_whitespace(self):
        html = """
        <table>
            <tr>
                <th>  Name  </th>
                <th>  Age   </th>
            </tr>
            <tr>
                <td>  Alice  </td>
                <td>  30  </td>
            </tr>
        </table>
        """
        expected = [['Name', 'Age'], ['Alice', '30']]
        assert to_list(html) == expected

    def test_table_with_empty_cells(self):
        html = """
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>Alice</td><td></td></tr>
            <tr><td></td><td>30</td></tr>
            <tr><td></td><td></td></tr>
        </table>
        """
        # Empty rows should be skipped
        expected = [['Name', 'Age'], ['Alice', ''], ['', '30']]
        assert to_list(html) == expected

    def test_table_with_multiple_tables(self):
        html = """
        <table id="table1">
            <tr><th>Col1</th><th>Col2</th></tr>
            <tr><td>1</td><td>2</td></tr>
        </table>
        <table id="table2">
            <tr><th>A</th><th>B</th></tr>
            <tr><td>X</td><td>Y</td></tr>
        </table>
        """
        expected_table0 = [['Col1', 'Col2'], ['1', '2']]
        expected_table1 = [['A', 'B'], ['X', 'Y']]
        assert to_list(html, index=0) == expected_table0
        assert to_list(html, index=1) == expected_table1

    def test_no_tables(self):
        html = '<div>No tables here</div>'
        with pytest.raises(ValueError, match='No tables found in HTML'):
            to_list(html)

    def test_index_out_of_range(self):
        html = '<table><tr><td>1</td></tr></table>'
        with pytest.raises(ValueError, match='Table index 1 out of range'):
            to_list(html, index=1)

    def test_table_with_rowspan(self):
        html = """
        <table>
            <tr><th>Name</th><th>Details</th></tr>
            <tr><td rowspan="2">Alice</td><td>Age: 30</td></tr>
            <tr><td>City: NYC</td></tr>
        </table>
        """
        # Basic parser doesn't handle rowspan specially
        expected = [
            ['Name', 'Details'],
            ['Alice', 'Age: 30'],
            ['Alice', 'City: NYC'],
        ]
        assert to_list(html) == expected

    def test_table_with_colspan(self):
        html = """
        <table>
            <tr><th colspan="2">Name</th><th>Age</th></tr>
            <tr><td>John</td><td>Doe</td><td>40</td></tr>
        </table>
        """
        # Basic parser doesn't handle colspan specially
        expected = [['Name', 'Name', 'Age'], ['John', 'Doe', '40']]
        assert to_list(html) == expected

    def test_complex_nested_elements(self):
        html = """
        <table>
            <tr><th>Name</th><th>Info</th></tr>
            <tr><td><b>Alice</b></td><td><span>Age: 30</span></td></tr>
        </table>
        """
        expected = [['Name', 'Info'], ['Alice', 'Age: 30']]
        assert to_list(html) == expected

    def test_table_with_thead_and_tbody(self):
        html = """
        <table>
            <thead>
                <tr><th>Name</th><th>Age</th></tr>
            </thead>
            <tbody>
                <tr><td>Alice</td><td>30</td></tr>
                <tr><td>Bob</td><td>25</td></tr>
            </tbody>
        </table>
        """
        expected = [['Name', 'Age'], ['Alice', '30'], ['Bob', '25']]
        assert to_list(html) == expected


class TestToDict:
    """Tests for the to_dict function."""

    def test_simple_table(self):
        html = """
        <table>
            <tr><th>Name</th><th>Age</th><th>City</th></tr>
            <tr><td>Alice</td><td>30</td><td>NYC</td></tr>
            <tr><td>Bob</td><td>25</td><td>LA</td></tr>
        </table>
        """
        expected = {
            'Name': ['Alice', 'Bob'],
            'Age': ['30', '25'],
            'City': ['NYC', 'LA'],
        }
        assert to_dict(html) == expected

    def test_table_without_headers(self):
        html = """
        <table>
            <tr><td>Alice</td><td>30</td><td>NYC</td></tr>
            <tr><td>Bob</td><td>25</td><td>LA</td></tr>
        </table>
        """
        # If no headers, first row becomes headers
        expected = {'Alice': ['Bob'], '30': ['25'], 'NYC': ['LA']}
        assert to_dict(html) == expected

    def test_table_with_missing_cells(self):
        html = """
        <table>
            <tr><th>Name</th><th>Age</th><th>City</th></tr>
            <tr><td>Alice</td><td>30</td></tr>
            <tr><td>Bob</td><td>25</td><td>LA</td></tr>
        </table>
        """
        expected = {
            'Name': ['Alice', 'Bob'],
            'Age': ['30', '25'],
            'City': ['', 'LA'],  # Missing cell gets empty string
        }
        assert to_dict(html) == expected

    def test_table_with_extra_cells(self):
        html = """
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>Alice</td><td>30</td><td>NYC</td></tr>
            <tr><td>Bob</td><td>25</td></tr>
        </table>
        """
        expected = {'Name': ['Alice', 'Bob'], 'Age': ['30', '25']}
        assert to_dict(html) == expected

    def test_empty_table(self):
        html = '<table></table>'
        assert to_dict(html) == {}

    def test_table_with_only_headers(self):
        html = """
        <table>
            <tr><th>Name</th><th>Age</th></tr>
        </table>
        """
        expected = {'Name': [], 'Age': []}
        assert to_dict(html) == expected

    def test_table_with_whitespace_in_headers(self):
        html = """
        <table>
            <tr><th>  Name  </th><th>  Age   </th></tr>
            <tr><td>  Alice  </td><td>  30  </td></tr>
        </table>
        """
        expected = {'Name': ['Alice'], 'Age': ['30']}
        assert to_dict(html) == expected

    def test_duplicate_headers(self):
        html = """
        <table>
            <tr><th>Name</th><th>Name</th><th>Age</th></tr>
            <tr><td>Alice</td><td>Bob</td><td>30</td></tr>
        </table>
        """
        # Duplicate headers are allowed, but will overwrite in dict
        # This is a limitation of using dict with duplicate keys
        expected = {'Name': ['Bob'], 'Age': ['30']}
        assert to_dict(html) == expected

    def test_multiple_tables_with_dict(self):
        html = """
        <table id="table1">
            <tr><th>Col1</th><th>Col2</th></tr>
            <tr><td>1</td><td>2</td></tr>
        </table>
        <table id="table2">
            <tr><th>A</th><th>B</th></tr>
            <tr><td>X</td><td>Y</td></tr>
        </table>
        """
        expected_table0 = {'Col1': ['1'], 'Col2': ['2']}
        expected_table1 = {'A': ['X'], 'B': ['Y']}
        assert to_dict(html, index=0) == expected_table0
        assert to_dict(html, index=1) == expected_table1


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_real_world_example(self):
        html = """
        <html>
            <body>
                <h1>Employee Data</h1>
                <table class="employees">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Department</th>
                            <th>Salary</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>001</td>
                            <td>John Smith</td>
                            <td>Engineering</td>
                            <td>75,000</td>
                        </tr>
                        <tr>
                            <td>002</td>
                            <td>Jane Doe</td>
                            <td>Marketing</td>
                            <td>65,000</td>
                        </tr>
                        <tr>
                            <td>003</td>
                            <td>Bob Johnson</td>
                            <td>Sales</td>
                            <td>70,000</td>
                        </tr>
                    </tbody>
                </table>
            </body>
        </html>
        """

        expected_list = [
            ['ID', 'Name', 'Department', 'Salary'],
            ['001', 'John Smith', 'Engineering', '75,000'],
            ['002', 'Jane Doe', 'Marketing', '65,000'],
            ['003', 'Bob Johnson', 'Sales', '70,000'],
        ]

        expected_dict = {
            'ID': ['001', '002', '003'],
            'Name': ['John Smith', 'Jane Doe', 'Bob Johnson'],
            'Department': ['Engineering', 'Marketing', 'Sales'],
            'Salary': ['75,000', '65,000', '70,000'],
        }

        assert to_list(html) == expected_list
        assert to_dict(html) == expected_dict


# Run tests with: pytest test_module.py -v
# Or with coverage: pytest test_module.py --cov=your_module --cov-report=term-missing
