"""Dashboard Streamlit — motor S01 certificado com fonte mínima verificada."""
from pathlib import Path
import sys
import base64

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from backend.motor import ActuarialEngine, BASE_RATES, InvalidRate, validate_rate
from backend.public_source import PublicActuarialEngine
from frontend.presentation import comparison_table

st.set_page_config(page_title='ARIMA · Simulador Atuarial - Sensibilidade dos Juros', layout='wide')
st.markdown(f'<style>{(ROOT / "frontend/style.css").read_text(encoding="utf8")}</style>', unsafe_allow_html=True)
logo_data = base64.b64encode((ROOT / 'frontend/assets/logo-arima.png').read_bytes()).decode('ascii')
# Arquivo institucional intacto; complemento tipográfico separado, aprovado pelo gestor.
brand_lockup = (f'<div class="brand-lockup"><img class="institutional-logo" src="data:image/png;base64,{logo_data}" alt="Logomarca ARIMA">'
                '<span class="brand-description">CONSULTORIA<br>ATUARIAL</span></div>')


@st.cache_resource(show_spinner=False)
def load_engine():
    # Somente a estrutura imutável de fórmulas é mantida; nenhum resultado é cacheado.
    return PublicActuarialEngine()


def reset_rates():
    st.session_state['rate_previdenciario'] = '4,91'
    st.session_state['rate_financeiro'] = '5,42'


@st.fragment
def panel(plan, key):
    regime = 'REGIME DE CAPITALIZAÇÃO' if plan == 'Previdenciário' else 'REGIME DE REPARTIÇÃO SIMPLES'
    icon = ('<circle cx="32" cy="14" r="9"/><circle cx="12" cy="23" r="6"/><circle cx="52" cy="23" r="6"/>'
            '<path d="M17 57V42a15 15 0 0 1 30 0v15ZM2 57V39a10 10 0 0 1 13-9v27ZM49 57V30a10 10 0 0 1 13 9v18Z"/>'
            if plan == 'Previdenciário' else
            '<ellipse cx="39" cy="13" rx="18" ry="8"/><path d="M21 19v9c0 10 36 10 36 0v-9c-9 9-27 9-36 0ZM21 34v9c0 10 36 10 36 0v-9c-9 9-27 9-36 0ZM24 48v8c8 7 33 4 33-5v-3c-9 7-24 7-33 0"/><circle cx="13" cy="46" r="12"/>')
    st.markdown(f'<div class="plan-heading"><svg viewBox="0 0 64 64" aria-hidden="true">{icon}</svg>'
                f'<div><h2>Plano {plan}</h2><p>{regime}</p></div></div>', unsafe_allow_html=True)
    default = str(BASE_RATES[plan]).replace('.', ',')
    if key not in st.session_state:
        st.session_state[key] = default
    field, reference = st.columns([1.7, 1], vertical_alignment='center')
    with field:
        raw = st.text_input(f'Taxa de juros — {plan} (% ao ano)', key=key,
                            help='De 0,00 a 20,00. Precisão de 0,01 ponto percentual. Confirme com Enter ou saia do campo.')
    with reference:
        st.markdown(f'<div class="reference-rate">Taxa padrão DRAA 2026<strong>{default}%</strong></div>', unsafe_allow_html=True)
    try:
        rate = validate_rate(raw)
    except InvalidRate as exc:
        st.error(str(exc))
        st.caption('Indicadores indisponíveis para esta entrada. Corrija a taxa ou restaure o padrão.')
        return
    try:
        engine = load_engine()
        baseline = engine.calculate(plan, BASE_RATES[plan])
        simulated = engine.calculate(plan, rate)
    except Exception:
        # Não expor células, fórmulas, caminhos ou detalhes de infraestrutura.
        st.error('Não foi possível calcular. A fonte atuarial está indisponível ou inválida.')
        return
    st.markdown(comparison_table(plan, simulated, baseline), unsafe_allow_html=True)


st.markdown('<header class="brand">'
            + brand_lockup +
            '<div class="brand-title"><h1>Simulador Atuarial - Sensibilidade dos Juros</h1>'
            '<p>RPPS do Município de São Luís — DRAA 2026</p></div>'
            '<div class="brand-values">PLANEJAMENTO<br>SEGURANÇA<br>RESULTADOS</div></header>', unsafe_allow_html=True)
_, help_column = st.columns([7, 1])
with help_column:
    with st.popover('Manual da tela', width='stretch'):
        st.markdown((ROOT / 'frontend/manual.txt').read_text(encoding='utf8'))

left, right = st.columns(2, gap='small')
with left:
    with st.container(key='panel_previdenciario'):
        panel('Previdenciário', 'rate_previdenciario')
with right:
    with st.container(key='panel_financeiro'):
        panel('Financeiro', 'rate_financeiro')

with st.container(key='reset_area'):
    _, reset, note, _ = st.columns([1, 1.2, 2.3, .5], vertical_alignment='center')
    with reset:
        st.button('Restaurar padrão', key='restore_rates', on_click=reset_rates, width='stretch', icon=':material/restart_alt:')
    with note:
        st.markdown('<p class="reset-note">Retorna às taxas de 4,91% (Previdenciário) e 5,42% (Financeiro)<br>'
                    'e recalcula todos os indicadores.</p>', unsafe_allow_html=True)
st.markdown('<footer class="executive-footer">'
            + brand_lockup +
            '<div><strong>Simulador Atuarial - Sensibilidade dos Juros</strong> &nbsp;|&nbsp; DRAA 2026'
            '<small>Ferramenta de simulação para análise de sensibilidade da taxa de juros.</small></div>'
            '<p>Confiança técnica para decisões sustentáveis.</p></footer>'
            '<p class="scope-note">Bases fornecidas do DRAA 2026, sem auditoria documental independente. '
            'Variação = simulado − base; percentual sobre |base|. Base zero: não aplicável.</p>', unsafe_allow_html=True)
