"""Formatação e comparação dos resultados certificados, sem cálculo atuarial."""
from decimal import Decimal, ROUND_HALF_UP
from html import escape

METRICS = (
    ('guaranteed_assets', 'Ativos garantidores'),
    ('adjusted_assets', 'Ativo atuarial ajustado'),
    ('liabilities', 'Passivo atuarial'),
    ('result', 'Resultado atuarial'),
)


def decimal_br(value: Decimal) -> str:
    value = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if value == 0:
        value = abs(value)
    return f'{value:,.2f}'.translate(str.maketrans({',': '.', '.': ','}))


def currency(value: Decimal) -> str:
    return f'R$ {decimal_br(value)}'


def difference(simulated: Decimal, base: Decimal):
    delta = simulated - base
    return delta, None if base == 0 else delta / abs(base) * 100


def percentage(value: Decimal | None) -> str:
    return 'não aplicável' if value is None else f'{decimal_br(value)}%'


def metric_html(label: str, value: Decimal, base: Decimal, result=False) -> str:
    delta, pct = difference(value, base)
    sign_class = 'negative' if value < 0 else 'positive' if value > 0 else 'neutral'
    emphasis = ' result' if result else ''
    meaning = ('Déficit' if value < 0 else 'Superávit' if value > 0 else 'Equilíbrio') if result else ''
    return (
        f'<section class="metric{emphasis}" aria-label="{escape(label)}">'
        f'<div class="metric-label">{escape(label)} <span>{meaning}</span></div>'
        f'<div class="metric-value {sign_class}">{currency(value)}</div>'
        f'<div class="metric-base">DRAA 2026: <strong>{currency(base)}</strong></div>'
        f'<div class="metric-delta">Variação: <strong>{currency(delta)}</strong>'
        f' <span>({percentage(pct)})</span></div></section>'
    )


PLAN_METRICS = {
    'Previdenciário': (('guaranteed_assets', 'Ativos garantidores'), ('gross_assets', 'Ativo atuarial'),
                       ('liabilities', 'Passivo atuarial'), ('result', 'Resultado atuarial')),
    'Financeiro': (('guaranteed_assets', 'Ativos garantidores'), ('adjusted_assets', 'Ativo atuarial ajustado'),
                   ('liabilities', 'Passivo atuarial'), ('result', 'Resultado atuarial')),
}


def adjusted_assets_help(simulated, baseline) -> str:
    """Memória explicativa da apresentação; os valores vêm do motor certificado."""
    def column(title, result):
        return (
            f'<section><strong>{title}</strong><dl>'
            f'<div><dt>Ativo atuarial bruto</dt><dd>{currency(result.gross_assets)}</dd></div>'
            '<div><dt>(−) Exclusão atuarial dos Aportes Insuficiência</dt>'
            f'<dd>{currency(result.exclusion)}</dd></div>'
            f'<div><dt>(=) Ativo atuarial ajustado</dt><dd>{currency(result.adjusted_assets)}</dd></div>'
            '</dl></section>'
        )

    return (
        '<details class="adjusted-help"><summary aria-label="Abrir composição do Ativo Atuarial Ajustado" '
        'title="Ver composição do Ativo Atuarial Ajustado">?</summary>'
        '<div class="adjusted-help-card"><strong>Composição do Ativo Atuarial Ajustado</strong>'
        f'<div class="adjusted-help-columns">{column("DRAA 2026", baseline)}{column("Simulado", simulated)}</div>'
        '<small>Acione novamente o ícone ? para fechar.</small></div></details>'
    )


def comparison_table(plan, simulated, baseline):
    """Apresenta campos certificados; não recompõe fórmulas atuariais."""
    rows = []
    for attr, label in PLAN_METRICS[plan]:
        value, base = getattr(simulated, attr), getattr(baseline, attr)
        delta, pct = difference(value, base)
        result = attr == 'result'
        meaning = ('Déficit' if value < 0 else 'Superávit' if value > 0 else 'Equilíbrio') if result else ''
        label_html = escape(label)
        if plan == 'Financeiro' and attr == 'adjusted_assets':
            label_html = f'<span>{label_html}</span>{adjusted_assets_help(simulated, baseline)}'
        rows.append(
            f'<tr class="{"result-row" if result else "indicator-row"}" data-indicator="{attr}">'
            f'<th scope="row"><div class="indicator-label-line">{label_html}</div>'
            f'<small class="result-meaning">{meaning}</small></th>'
            f'<td class="{"negative" if base < 0 else ""}">{currency(base)}</td>'
            f'<td class="{"negative" if value < 0 else ""}">{currency(value)}</td>'
            f'<td class="variation">{currency(delta)}<small>({percentage(pct)})</small></td></tr>'
        )
    kind = 'previdenciario' if plan == 'Previdenciário' else 'financeiro'
    return (
        f'<div class="comparison-wrap" tabindex="0" role="region" aria-label="Comparação do Plano {plan}">'
        f'<table class="comparison {kind}" aria-label="Indicadores do Plano {plan}">'
        '<thead><tr><th scope="col">Indicador</th><th scope="col">DRAA 2026<small>Valor de referência</small></th>'
        '<th scope="col">Simulado<small>Com a taxa informada</small></th>'
        '<th scope="col">Variação<small>Simulado − Base</small></th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )
