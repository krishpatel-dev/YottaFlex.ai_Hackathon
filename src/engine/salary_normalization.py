"""
salary_normalization.py
-----------------------
Core salary normalization functions: currency conversion, FTE adjustment,
band validation, compa-ratio and band-position calculations.
"""

from __future__ import annotations

import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REFERENCE_DATE = datetime.date(2026, 10, 22)

FX_TO_INR: dict[str, float] = {
    "INR": 1.0,
    "USD": 83.5,
    "GBP": 105.2,
    "EUR": 90.1,
    "SGD": 62.3,
    "AED": 22.73,
}

SUPPORTED_CURRENCIES: set[str] = set(FX_TO_INR.keys())


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class CurrencyMissingError(Exception):
    """Raised when a currency code is not present in the FX rate table."""

    def __init__(self, currency: str, available: set[str] | None = None) -> None:
        self.currency = currency
        self.available = available or set(FX_TO_INR.keys())
        super().__init__(
            f"Currency '{currency}' not found in FX rate table. "
            f"Supported: {sorted(self.available)}"
        )


class FTEError(Exception):
    """Raised when an FTE fraction is outside the valid (0, 1] range."""

    def __init__(self, fte_fraction: float) -> None:
        self.fte_fraction = fte_fraction
        super().__init__(
            f"Invalid FTE fraction {fte_fraction!r}. "
            "Value must be in the range (0.0, 1.0] inclusive."
        )


class ExpiredBandError(Exception):
    """Raised when only an expired compensation band is found for an employee."""

    def __init__(
        self,
        band_id: str,
        expiry_date: datetime.date,
        evaluation_date: datetime.date,
    ) -> None:
        self.band_id = band_id
        self.expiry_date = expiry_date
        self.evaluation_date = evaluation_date
        super().__init__(
            f"Band '{band_id}' expired on {expiry_date} "
            f"(evaluation date: {evaluation_date})."
        )


# ---------------------------------------------------------------------------
# normalize_currency
# ---------------------------------------------------------------------------


def normalize_currency(
    amount: float,
    from_currency: str,
    to_currency: str = "INR",
    fx_rates: dict[str, float] = FX_TO_INR,
    raise_on_missing: bool = True,
) -> Optional[float]:
    """Convert *amount* from *from_currency* to *to_currency* using *fx_rates*.

    The function supports any currency pair as long as both currencies have an
    entry in *fx_rates* (assumed to map every currency → INR).  Conversion is
    performed via the INR pivot:

        result = amount * (fx_rates[from_currency] / fx_rates[to_currency])

    Parameters
    ----------
    amount:
        The monetary amount to convert.  May be negative (e.g. adjustments).
    from_currency:
        ISO 4217 currency code of the source amount.
    to_currency:
        ISO 4217 currency code of the target.  Defaults to "INR".
    fx_rates:
        Mapping of currency code → INR equivalent.  Defaults to ``FX_TO_INR``.
    raise_on_missing:
        If ``True`` (default), raises :class:`CurrencyMissingError` when a
        currency is absent from *fx_rates*.  If ``False``, logs a warning and
        returns ``None``.

    Returns
    -------
    float | None
        Converted amount, or ``None`` if a currency is missing and
        *raise_on_missing* is ``False``.

    Raises
    ------
    CurrencyMissingError
        When a currency code is not in *fx_rates* and *raise_on_missing* is
        ``True``.
    """
    available = set(fx_rates.keys())

    for code in (from_currency, to_currency):
        if code not in fx_rates:
            if raise_on_missing:
                raise CurrencyMissingError(code, available)
            logger.warning(
                "Currency '%s' not found in FX rate table; returning None. "
                "Supported: %s",
                code,
                sorted(available),
            )
            return None

    if from_currency == to_currency:
        return float(amount)

    # Pivot through INR
    amount_in_inr = float(amount) * fx_rates[from_currency]
    result = amount_in_inr / fx_rates[to_currency]
    return result


# ---------------------------------------------------------------------------
# normalize_fte
# ---------------------------------------------------------------------------


def normalize_fte(
    annual_salary: float,
    fte_fraction: float,
    raise_on_invalid: bool = True,
) -> float:
    """Convert a part-time annual salary to its full-time equivalent.

    Formula::

        fte_salary = annual_salary / fte_fraction

    A full-time employee (fte_fraction == 1.0) is returned unchanged.

    Parameters
    ----------
    annual_salary:
        The raw annual salary figure (already in a consistent currency).
    fte_fraction:
        The employee's FTE fraction, e.g. 0.5 for a half-time worker.
        Must satisfy 0 < fte_fraction <= 1.0.
    raise_on_invalid:
        If ``True`` (default), raises :class:`FTEError` for out-of-range
        values.  If ``False``, clamps to 1.0 and logs a warning.

    Returns
    -------
    float
        Full-time equivalent annual salary.

    Raises
    ------
    FTEError
        When *fte_fraction* is ``<= 0`` or ``> 1.0`` and *raise_on_invalid*
        is ``True``.
    """
    if fte_fraction <= 0.0 or fte_fraction > 1.0:
        if raise_on_invalid:
            raise FTEError(fte_fraction)
        logger.warning(
            "Invalid FTE fraction %s; clamping to 1.0 (no FTE adjustment applied).",
            fte_fraction,
        )
        fte_fraction = 1.0

    return float(annual_salary) / fte_fraction


# ---------------------------------------------------------------------------
# normalize_salary
# ---------------------------------------------------------------------------


def normalize_salary(
    annual_salary: float,
    currency_code: str,
    fte_fraction: float,
    fx_rates: dict[str, float] = FX_TO_INR,
) -> dict:
    """Full normalization pipeline: currency → INR, then FTE adjustment.

    Applies :func:`normalize_currency` followed by :func:`normalize_fte`.
    Errors are captured in the returned ``errors`` list rather than raised, so
    callers can process a whole batch and collect failures.

    Parameters
    ----------
    annual_salary:
        Raw annual salary in *currency_code*.
    currency_code:
        ISO 4217 source currency.
    fte_fraction:
        FTE fraction in (0, 1].
    fx_rates:
        FX rate mapping.  Defaults to :data:`FX_TO_INR`.

    Returns
    -------
    dict
        Keys:

        * ``normalized_inr`` – salary converted to INR (or ``None`` on error).
        * ``fte_adjusted_inr`` – FTE-normalised INR amount (or ``None``).
        * ``original_salary`` – the input *annual_salary* value.
        * ``currency_code`` – the input *currency_code*.
        * ``fte_fraction`` – the input *fte_fraction*.
        * ``conversion_rate`` – the INR rate used (or ``None`` on error).
        * ``errors`` – list of error message strings encountered.
    """
    errors: list[str] = []
    normalized_inr: Optional[float] = None
    fte_adjusted_inr: Optional[float] = None
    conversion_rate: Optional[float] = None

    # Step 1 – Currency normalisation
    try:
        normalized_inr = normalize_currency(
            annual_salary,
            from_currency=currency_code,
            to_currency="INR",
            fx_rates=fx_rates,
            raise_on_missing=True,
        )
        conversion_rate = fx_rates.get(currency_code)
    except CurrencyMissingError as exc:
        errors.append(str(exc))

    # Step 2 – FTE adjustment
    if normalized_inr is not None:
        try:
            fte_adjusted_inr = normalize_fte(
                normalized_inr,
                fte_fraction=fte_fraction,
                raise_on_invalid=True,
            )
        except FTEError as exc:
            errors.append(str(exc))

    return {
        "normalized_inr": normalized_inr,
        "fte_adjusted_inr": fte_adjusted_inr,
        "original_salary": annual_salary,
        "currency_code": currency_code,
        "fte_fraction": fte_fraction,
        "conversion_rate": conversion_rate,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# validate_band_active
# ---------------------------------------------------------------------------


def validate_band_active(
    band_effective_date: datetime.date,
    band_expiry_date: Optional[datetime.date],
    evaluation_date: datetime.date,
) -> tuple[bool, str]:
    """Check whether a compensation band is active on *evaluation_date*.

    A band is considered active when:

    * ``band_effective_date <= evaluation_date``, **and**
    * ``band_expiry_date`` is ``None`` OR ``evaluation_date <= band_expiry_date``.

    Parameters
    ----------
    band_effective_date:
        The date from which the band becomes active.
    band_expiry_date:
        The date after which the band is no longer active.  ``None`` means
        the band has no set expiry (open-ended).
    evaluation_date:
        The date on which to assess band validity.

    Returns
    -------
    tuple[bool, str]
        ``(is_valid, reason_message)`` where *is_valid* is ``True`` when the
        band is active on *evaluation_date*.

    Raises
    ------
    ExpiredBandError
        When the band has expired (``band_expiry_date < evaluation_date``).
    """
    if evaluation_date < band_effective_date:
        return (
            False,
            f"Band not yet effective: effective from {band_effective_date}, "
            f"evaluated on {evaluation_date}.",
        )

    if band_expiry_date is not None and evaluation_date > band_expiry_date:
        raise ExpiredBandError(
            band_id="<unknown>",  # caller may override message if needed
            expiry_date=band_expiry_date,
            evaluation_date=evaluation_date,
        )

    return (
        True,
        f"Band is active on {evaluation_date} "
        f"(effective {band_effective_date} – "
        f"{'open-ended' if band_expiry_date is None else str(band_expiry_date)}).",
    )


# ---------------------------------------------------------------------------
# compute_compa_ratio
# ---------------------------------------------------------------------------


def compute_compa_ratio(salary_normalized_fte: float, band_midpoint: float) -> float:
    """Compute the compa-ratio of a salary relative to the band midpoint.

    Compa-Ratio = (normalized_fte_salary / band_midpoint) × 100

    A compa-ratio of 100 means the salary equals the band midpoint exactly.

    Parameters
    ----------
    salary_normalized_fte:
        The FTE-adjusted, INR-normalised annual salary.
    band_midpoint:
        The midpoint of the applicable compensation band (INR).

    Returns
    -------
    float
        Compa-ratio as a percentage (e.g. 95.0 means 95 % of midpoint).

    Raises
    ------
    ValueError
        When *band_midpoint* is ``<= 0``.
    """
    if band_midpoint <= 0:
        raise ValueError(
            f"band_midpoint must be positive; received {band_midpoint!r}."
        )
    return (float(salary_normalized_fte) / float(band_midpoint)) * 100.0


# ---------------------------------------------------------------------------
# compute_band_position
# ---------------------------------------------------------------------------


def compute_band_position(
    salary: float,
    band_min: float,
    band_max: float,
) -> tuple[float, str]:
    """Compute where within the compensation band a salary falls.

    Band Position = (salary − band_min) / (band_max − band_min)

    * Position  < 0  → salary is below the band.
    * 0 ≤ Position ≤ 1  → salary is within the band.
    * Position  > 1  → salary is above the band.

    Parameters
    ----------
    salary:
        The (FTE-adjusted, normalised) annual salary.
    band_min:
        Lower boundary of the compensation band (same currency as *salary*).
    band_max:
        Upper boundary of the compensation band (same currency as *salary*).

    Returns
    -------
    tuple[float, str]
        ``(position, status)`` where *status* is one of ``"BELOW_BAND"``,
        ``"WITHIN_BAND"``, or ``"ABOVE_BAND"``.

    Raises
    ------
    ValueError
        When ``band_max <= band_min`` (degenerate band).
    """
    band_range = float(band_max) - float(band_min)
    if band_range <= 0:
        raise ValueError(
            f"band_max ({band_max}) must be strictly greater than "
            f"band_min ({band_min})."
        )

    position = (float(salary) - float(band_min)) / band_range

    if position < 0.0:
        status = "BELOW_BAND"
    elif position > 1.0:
        status = "ABOVE_BAND"
    else:
        status = "WITHIN_BAND"

    return position, status


# ---------------------------------------------------------------------------
# classify_compa_ratio
# ---------------------------------------------------------------------------


def classify_compa_ratio(compa_ratio: float) -> str:
    """Classify a compa-ratio into a named tier.

    Thresholds
    ----------
    * ``< 80``      → ``"SIGNIFICANTLY_BELOW"``
    * ``80 – <90``  → ``"BELOW"``
    * ``90 – 110``  → ``"TARGET"``
    * ``>110 – 120``→ ``"ABOVE"``
    * ``> 120``     → ``"SIGNIFICANTLY_ABOVE"``

    Parameters
    ----------
    compa_ratio:
        Compa-ratio percentage (e.g. 95.0).

    Returns
    -------
    str
        One of the five classification labels.
    """
    if compa_ratio < 80.0:
        return "SIGNIFICANTLY_BELOW"
    if compa_ratio < 90.0:
        return "BELOW"
    if compa_ratio <= 110.0:
        return "TARGET"
    if compa_ratio <= 120.0:
        return "ABOVE"
    return "SIGNIFICANTLY_ABOVE"
