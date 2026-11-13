"""Pure normalization of schema fields; no private values in error messages."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re


MONTHS = {name: number for number, name in enumerate(
    ('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'), 1)}


def header(value):
    return re.sub(r'[_\s]+', ' ', value.strip().lower())


def phone(value):
    digits = re.sub(r'[^0-9]', '', value)
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    if not re.fullmatch(r'[6-9][0-9]{9}', digits):
        raise ValueError('invalid_phone')
    return '+91' + digits


def calendar_date(value):
    if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        return date.fromisoformat(value).isoformat()
    numeric = re.fullmatch(r'([0-9]{2})([/-])([0-9]{2})\2([0-9]{4})', value)
    if numeric:
        day, _, month, year = numeric.groups()
        return date(int(year), int(month), int(day)).isoformat()
    named = re.fullmatch(r'([0-9]{2})-([A-Za-z]{3})-([0-9]{4})', value)
    if named:
        day, month, year = named.groups()
        if month.lower() in MONTHS:
            return date(int(year), MONTHS[month.lower()], int(day)).isoformat()
    raise ValueError('Invalid date')


def amount(value):
    cleaned = re.sub(r'^(?:₹|rs\.?|inr)\s*', '', value, flags=re.IGNORECASE).replace(',', '')
    if not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)', cleaned):
        raise ValueError('Invalid decimal')
    try:
        number = Decimal(cleaned)
        if number < 0:
            raise ValueError('Invalid decimal')
        return format(abs(number).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'f')
    except InvalidOperation:
        raise ValueError('Invalid decimal') from None


def normalize_row(fields, raw):
    """Return normalized values, first rejection, and accepted-row warning count."""
    values, warnings = {}, 0
    for field in fields:
        name, kind = field['name'], field['type']
        value = raw.get(name, '').strip()
        if not value:
            if field.get('required'):
                return None, 'missing_required:' + name, 0
            values[name] = None
            continue
        if kind not in {'string', 'phone', 'date', 'decimal', 'enum'}:
            raise ValueError('Unsupported schema field type')
        try:
            if kind == 'phone':
                value = phone(value)
            elif kind == 'date':
                value = calendar_date(value)
            elif kind == 'decimal':
                value = amount(value)
            elif kind == 'enum':
                value = value.lower()
                if value not in [item.lower() for item in field['values']]:
                    raise ValueError('Invalid enum')
        except ValueError:
            if kind == 'phone':
                return None, 'invalid_phone', 0
            if field.get('required'):
                # The supplied schemas require only strings and phone. No rejection
                # code is specified for an invalid required date/decimal/enum.
                raise ValueError('Invalid required typed field; schema needs a rejection policy') from None
            value = None
            warnings += 1
        values[name] = value
    return values, None, warnings


def apply_defaults(fields, values):
    """Resolve defaults for use, without persisting them as incoming updates."""
    resolved = values.copy()
    for field in fields:
        name = field['name']
        if resolved.get(name) is None and 'default' in field:
            resolved[name] = field['default']
    return resolved
