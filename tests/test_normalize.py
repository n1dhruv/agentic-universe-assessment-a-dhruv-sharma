"""Exact examples for the lead schema rules."""

import pytest

from solution.normalize import amount, apply_defaults, calendar_date, header, normalize_row, phone


@pytest.mark.parametrize('raw', [
    '9876543210', '+91 98765 43210', '09876543210',
    '91-98765-43210', '(+91) 9876543210', '+919876543210',
])
def test_phone_formats(raw):
    assert phone(raw) == '+919876543210'


@pytest.mark.parametrize('raw', ['', '123', '5876543210', '+1 415 555 0134', '00919876543210', 'N/A'])
def test_invalid_phone(raw):
    with pytest.raises(ValueError, match='invalid_phone'):
        phone(raw)


@pytest.mark.parametrize('raw', ['2026-12-01', '01/12/2026', '01-12-2026', '01-dEc-2026'])
def test_date_formats(raw):
    assert calendar_date(raw) == '2026-12-01'


@pytest.mark.parametrize('raw', ['31/02/2026', '2026-13-01', 'tomorrow', '01-xyz-2026', '29/02/2025'])
def test_impossible_dates(raw):
    with pytest.raises(ValueError):
        calendar_date(raw)


def test_day_first_and_leap_year():
    assert calendar_date('03/04/2026') == '2026-04-03'
    assert calendar_date('29/02/2024') == '2024-02-29'


@pytest.mark.parametrize('raw,expected', [
    ('₹1,234.565', '1234.57'), ('Rs. 20', '20.00'), ('rS20', '20.00'),
    ('inr 0', '0.00'), ('1.005', '1.01'), ('0', '0.00'), ('-0.00', '0.00'),
])
def test_currency_and_half_up_rounding(raw, expected):
    assert amount(raw) == expected


@pytest.mark.parametrize('raw', ['-1', '-0.001', 'N/A', 'NaN', 'Infinity', 'twelve', '', '1e3'])
def test_invalid_currency(raw):
    with pytest.raises(ValueError):
        amount(raw)


def test_header_normalization():
    assert header('  Mobile__  No ') == 'mobile no'


def test_warning_discarded_if_later_required_field_fails():
    fields = [{'name': 'date', 'type': 'date'}, {'name': 'name', 'type': 'string', 'required': True}]
    assert normalize_row(fields, {'date': 'soon'}) == (None, 'missing_required:name', 0)


def test_defaults_are_resolved_without_mutating_merged_values():
    fields = [{'name': 'language', 'default': 'en'}]
    incoming = {'language': None}
    assert apply_defaults(fields, incoming) == {'language': 'en'}
    assert incoming == {'language': None}
    assert apply_defaults(fields, {'language': 'hi'}) == {'language': 'hi'}
