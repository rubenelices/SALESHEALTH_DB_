"""
Formatters reutilizables del dashboard.

Separados de styles.py para que el código de presentación (formateo numérico,
badges, etiquetas) no se mezcle con el CSS global.
"""
from __future__ import annotations


# ═══════════════════════════════════════════════════════════════════════
#  FORMATEO NUMÉRICO
# ═══════════════════════════════════════════════════════════════════════
def fmt_eur(v: float | None, decimals: int = 0) -> str:
    """Formatea un número como euros con separador de miles (estilo ES)."""
    if v is None:
        return '—'
    try:
        return f'{v:,.{decimals}f} €'.replace(',', '·').replace('.', ',').replace('·', '.')
    except (ValueError, TypeError):
        return '—'


def fmt_int(v: float | int | None) -> str:
    """Formatea un entero con separador de miles (estilo ES)."""
    if v is None:
        return '—'
    try:
        return f'{int(v):,}'.replace(',', '.')
    except (ValueError, TypeError):
        return '—'


def fmt_pct(v: float | None, decimals: int = 1) -> str:
    """Formatea como porcentaje. Acepta valores en 0..1 o 0..100 (auto)."""
    if v is None:
        return '—'
    try:
        if abs(v) <= 1.5:
            v = v * 100
        return f'{v:.{decimals}f}%'.replace('.', ',')
    except (ValueError, TypeError):
        return '—'


def fmt_num(v: float | None, decimals: int = 2) -> str:
    """Formatea un número decimal genérico con separador de miles."""
    if v is None:
        return '—'
    try:
        return f'{v:,.{decimals}f}'.replace(',', '·').replace('.', ',').replace('·', '.')
    except (ValueError, TypeError):
        return '—'


def fmt_millones(v: float | None, decimals: int = 2) -> str:
    """Formatea un número grande como millones (ej. 9.678.678 → 9,68 M€)."""
    if v is None:
        return '—'
    try:
        return f'{v / 1e6:.{decimals}f} M€'.replace('.', ',')
    except (ValueError, TypeError):
        return '—'


# ═══════════════════════════════════════════════════════════════════════
#  BADGES Y ETIQUETAS
# ═══════════════════════════════════════════════════════════════════════
def badge(text: str, kind: str) -> str:
    """Devuelve un badge HTML.

    kind admitidos: alto | medio | bajo | churn | active | vip
    """
    return f'<span class="badge badge-{kind}">{text}</span>'


def segmento_badge(segmento: str) -> str:
    """Devuelve el badge HTML correcto para un segmento CLTV."""
    seg_lower = (segmento or '').lower()
    if seg_lower in ('alto', 'medio', 'bajo'):
        return badge(segmento, seg_lower)
    return str(segmento) if segmento else '—'


def estado_badge(en_riesgo: bool) -> str:
    """Devuelve el badge de estado (activo / en riesgo)."""
    return badge('🔴 En riesgo', 'churn') if en_riesgo else badge('🟢 Activo', 'active')
