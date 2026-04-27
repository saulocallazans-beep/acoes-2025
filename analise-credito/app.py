"""
Análise de Crédito — Petrobras S.A. (PETR4 · PBR)
Dashboard para Comitê de Crédito Corporativo
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import yfinance as yf
from datetime import datetime

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Análise de Crédito | Petrobras",
    page_icon="🛢️",
    layout="wide",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.report-header {
    background: linear-gradient(135deg, #0a2540 0%, #1a4b8c 100%);
    padding: 1.8rem 2rem; border-radius: 10px; color: white; margin-bottom: 1.5rem;
}
.report-header h1 { margin: 0; font-size: 1.75rem; font-weight: 700; }
.report-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.9rem; }

.badge {
    display: inline-block; padding: 3px 13px; border-radius: 20px;
    font-weight: 700; font-size: 0.82rem; margin: 2px 3px 0 0;
}
.badge-green  { background:#d1fadf; color:#166534; }
.badge-yellow { background:#fef9c3; color:#854d0e; }
.badge-blue   { background:#dbeafe; color:#1e40af; }
.badge-red    { background:#fee2e2; color:#991b1b; }

.kpi {
    background: #f8fafc; border-left: 4px solid #1a4b8c;
    padding: 14px 16px; border-radius: 6px; height: 100%;
}
.kpi-label { color:#64748b; font-size:0.72rem; text-transform:uppercase;
             letter-spacing:0.06em; margin-bottom:4px; }
.kpi-value { color:#0f172a; font-size:1.55rem; font-weight:700; line-height:1.1; }
.kpi-sub   { color:#64748b; font-size:0.75rem; margin-top:4px; }

.rating-box {
    background:#fffbeb; border-left:3px solid #f59e0b;
    padding:9px 13px; border-radius:4px; margin-bottom:7px;
}
.risk-alto  { background:#fef2f2; border-left:4px solid #ef4444;
              padding:9px 13px; border-radius:5px; margin-bottom:8px; }
.risk-medio { background:#fffbeb; border-left:4px solid #f59e0b;
              padding:9px 13px; border-radius:5px; margin-bottom:8px; }
.risk-baixo { background:#f0fdf4; border-left:4px solid #22c55e;
              padding:9px 13px; border-radius:5px; margin-bottom:8px; }

.section-note {
    background:#f1f5f9; border-radius:6px; padding:10px 14px;
    font-size:0.85rem; color:#475569; margin-top:0.5rem;
}
hr.div { border:none; border-top:1px solid #e2e8f0; margin:1.2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Dados base ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def cotacao_petr4():
    df = yf.download("PETR4.SA", start="2024-01-01", auto_adjust=True, progress=False)
    return df

@st.cache_data(ttl=600)
def peers_info():
    mapa = {
        "Petrobras (PBR)":  "PBR",
        "ExxonMobil":       "XOM",
        "Shell":            "SHEL",
        "TotalEnergies":    "TTE",
        "BP":               "BP",
        "Equinor":          "EQNR",
        "Repsol":           "REP",
    }
    rows = []
    for nome, tick in mapa.items():
        try:
            info = yf.Ticker(tick).info
            mc   = (info.get("marketCap") or 0) / 1e9
            pe   = info.get("trailingPE")
            eveb = info.get("enterpriseToEbitda")
            dy   = (info.get("dividendYield") or 0) * 100
            rev  = (info.get("totalRevenue") or 0) / 1e9
            rows.append({
                "Empresa":           nome,
                "Ticker":            tick,
                "Market Cap (USD Bi)": round(mc, 1),
                "Receita (USD Bi)":   round(rev, 1),
                "P/L":               round(pe, 1) if pe else "—",
                "EV/EBITDA":         round(eveb, 1) if eveb else "—",
                "Div. Yield (%)":    round(dy, 2),
            })
        except Exception:
            pass
    return pd.DataFrame(rows)

@st.cache_data(ttl=600)
def preco_petroleo():
    df = yf.download("CL=F", start="2024-01-01", auto_adjust=True, progress=False)
    return df

# ── Dados financeiros históricos (Relatórios Anuais Petrobras 2019-2023) ──────
ANOS = [2019, 2020, 2021, 2022, 2023]

df_fin = pd.DataFrame({
    "Ano":                      ANOS,
    "Receita Líquida (R$ Bi)":  [408.6, 272.1, 452.7, 511.7, 491.7],
    "EBITDA (R$ Bi)":           [163.2, 105.8, 205.8, 241.3, 204.4],
    "Lucro Líquido (R$ Bi)":    [ 40.1, -57.3, 107.3, 188.3, 124.4],
    "Dívida Bruta (R$ Bi)":     [371.5, 421.6, 357.1, 290.8, 221.4],
    "Caixa (R$ Bi)":            [ 53.0,  59.0,  61.5,  72.7,  62.4],
    "Dívida Líquida (R$ Bi)":   [318.5, 362.6, 295.6, 218.1, 159.0],
    "Capex (R$ Bi)":            [ 55.6,  42.1,  46.2,  62.5,  72.4],
    "FCL (R$ Bi)":              [ 43.2,  21.5,  76.3, 123.5,  80.2],
    "Dív.Líq/EBITDA":           [  1.95,  3.43,  1.44,  0.90,  0.78],
    "Margem EBITDA (%)":        [ 40.0,  38.9,  45.5,  47.2,  41.6],
    "Margem Líquida (%)":       [  9.8, -21.1,  23.7,  36.8,  25.3],
    "ROIC (%)":                 [ 10.2,  -5.1,  16.8,  24.3,  18.5],
    "ROE (%)":                  [ 12.4, -16.2,  23.1,  36.4,  25.8],
})

df_prod = pd.DataFrame({
    "Ano":               ANOS,
    "Produção (Mboe/d)": [2.68, 2.73, 2.77, 2.78, 2.78],
    "Pré-Sal (%)":       [  53,   57,   63,   67,   72],
    "Produção Pré-Sal":  [1.42, 1.56, 1.75, 1.86, 2.00],
    "Produção Pós-Sal":  [1.26, 1.17, 1.02, 0.92, 0.78],
})

df_refino = pd.DataFrame({
    "Refinaria": ["REPLAN (SP)", "REDUC (RJ)", "RLAM (BA)", "REPAR (PR)",
                  "REFAP (RS)", "RPBC (SP)", "REGAP (MG)", "Outras (6)"],
    "Capacidade (Mbbl/d)": [415, 239, 210, 189, 180, 170, 151, 246],
    "UF": ["SP","RJ","BA","PR","RS","SP","MG","Vários"],
})

# ── Header com cotação ao vivo ─────────────────────────────────────────────────
cot = cotacao_petr4()
if not cot.empty:
    close  = cot["Close"].squeeze()
    high   = cot["High"].squeeze()
    low    = cot["Low"].squeeze()
    preco  = float(close.iloc[-1])
    var_d  = float((close.iloc[-1] / close.iloc[-2] - 1) * 100) if len(cot) > 1 else 0
    max_52 = float(high.max())
    min_52 = float(low.min())
else:
    preco = var_d = max_52 = min_52 = 0

cor_var = "#86efac" if var_d >= 0 else "#fca5a5"
seta    = "▲" if var_d >= 0 else "▼"

st.markdown(f"""
<div class="report-header">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
    <div>
      <h1>🛢️ Petrobras S.A. — Análise de Crédito Corporativo</h1>
      <p>PETR4.SA · B3 &nbsp;|&nbsp; Setor: Energia — Petróleo & Gás Integrado &nbsp;|&nbsp;
         Emitido em {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
      <div style="margin-top:0.8rem;">
        <span class="badge badge-yellow">S&P: BB+</span>
        <span class="badge badge-yellow">Moody's: Ba1</span>
        <span class="badge badge-yellow">Fitch: BB+</span>
        <span class="badge badge-green">Recomendação: APROVADO ✓</span>
        <span class="badge badge-blue">Analista: Comitê de Crédito</span>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:2rem;font-weight:700;">R$ {preco:.2f}</div>
      <div style="color:{cor_var};font-size:1rem;">{seta} {var_d:+.2f}% no dia</div>
      <div style="opacity:0.65;font-size:0.78rem;">Máx 52s: R$ {max_52:.2f} · Mín 52s: R$ {min_52:.2f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Abas principais ───────────────────────────────────────────────────────────
abas = st.tabs([
    "📋 Resumo Executivo",
    "🏢 Perfil da Empresa",
    "⚙️ Segmentos de Negócio",
    "🌍 Mercado & Competidores",
    "📊 Indicadores Financeiros",
    "⚠️ Análise de Risco",
])

# ═══════════════════════════════════════════════════════════════════════════════
# ABA 0 — RESUMO EXECUTIVO
# ═══════════════════════════════════════════════════════════════════════════════
with abas[0]:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    kpis = [
        (c1, "Receita Líquida",    "R$ 491,7 Bi", "Exercício 2023"),
        (c2, "EBITDA",             "R$ 204,4 Bi", "Margem: 41,6%"),
        (c3, "Lucro Líquido",      "R$ 124,4 Bi", "Margem: 25,3%"),
        (c4, "Dív. Líq. / EBITDA","0,78×",        "↓ vs. 0,90× em 2022"),
        (c5, "Dívida Líquida",     "R$ 159,0 Bi", "Mín. histórico recente"),
        (c6, "Free Cash Flow",     "R$ 80,2 Bi",  "Geração recorrente"),
    ]
    for col, label, val, sub in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value">{val}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)

    col_pare, col_score = st.columns([3, 2])

    with col_pare:
        st.markdown("### Parecer do Analista de Crédito")
        st.markdown("""
A **Petrobras** apresenta um **perfil de crédito sólido** para uma empresa petrolífera de mercado
emergente. Sua posição como operadora dominante do pré-sal brasileiro, com ativos de classe mundial
e break-even estimado em torno de **US$ 30/bbl**, confere ampla margem de segurança mesmo em cenários
de queda acentuada do petróleo.

Nos últimos quatro anos, a companhia executou um **ciclo agressivo de desalavancagem**: a dívida
líquida caiu de R$ 362 Bi (2020) para R$ 159 Bi (2023), com índice Dívida Líquida/EBITDA de
apenas **0,78×** — significativamente abaixo da média dos grandes pares globais (~1,5×).

**Pontos fortes do crédito:**
- Gerador de caixa excepcional: FCL de R$ 80 Bi em 2023
- Reservas provadas de ~12 bilhões de boe (2P) com vida útil > 10 anos
- Posição de caixa de R$ 62 Bi + linhas de crédito rotativas comprometidas
- Política de dividendos baseada em FCL reduz risco de deterioração de caixa

**Fatores de atenção:**
- Rating soberano do Brasil limita teto do rating (BB+/Ba1)
- Interferência política potencial na política de preços e dividendos
- Capex crescente (R$ 102 Bi planejados em 2024) pode elevar alavancagem

**Conclusão:** Risco de crédito **baixo a moderado**. Recomendamos aprovação com
covenants de Dívida Líquida/EBITDA ≤ 2,5× e monitoramento semestral.
        """)

    with col_score:
        st.markdown("### Scorecard de Crédito (0–100)")
        scorecard = {
            "Posição de Mercado":    90,
            "Qualidade dos Ativos":  87,
            "Geração de Caixa":      88,
            "Alavancagem":           85,
            "Liquidez":              80,
            "Cobertura de Juros":    84,
            "Governança":            62,
            "Risco Político/Regulat.": 58,
            "ESG / Transição":       55,
            "Risco País (Brasil)":   63,
        }
        labels = list(scorecard.keys())
        vals   = list(scorecard.values())
        colors = ["#22c55e" if v >= 75 else "#f59e0b" if v >= 60 else "#ef4444" for v in vals]
        nota_final = round(sum(vals) / len(vals), 1)

        fig_sc = go.Figure(go.Bar(
            x=vals, y=labels, orientation="h",
            marker_color=colors,
            text=[f"{v}" for v in vals], textposition="outside",
        ))
        fig_sc.add_vline(x=75, line_dash="dot", line_color="#94a3b8",
                         annotation_text="Limiar alto", annotation_position="top right")
        fig_sc.update_layout(
            xaxis=dict(range=[0, 110], showgrid=False, showticklabels=False),
            yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
            height=380, margin=dict(l=0, r=50, t=10, b=0),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig_sc, use_container_width=True)
        st.markdown(f"""
        <div style="text-align:center;background:#0a2540;color:white;
                    border-radius:8px;padding:10px;font-size:1.1rem;">
          <b>Nota Final: {nota_final}/100</b> — Risco Baixo/Moderado
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 1 — PERFIL DA EMPRESA
# ═══════════════════════════════════════════════════════════════════════════════
with abas[1]:
    col_esq, col_dir = st.columns([2, 1.2])

    with col_esq:
        st.markdown("### Histórico e Perfil Corporativo")
        st.markdown("""
**Petróleo Brasileiro S.A. — Petrobras** é uma sociedade de economia mista brasileira fundada em
**3 de outubro de 1953** pelo Presidente Getúlio Vargas, com o objetivo de executar a política
nacional do petróleo. Hoje é a **maior empresa da América Latina** por valor de mercado e uma das
maiores petrolíferas integradas do mundo.

A descoberta do **pré-sal em 2006–2007** (Bacia de Santos) transformou fundamentalmente o
posicionamento estratégico da companhia, conferindo-lhe reservatórios de petróleo de alta qualidade
com custos de extração entre os mais baixos do mundo (~US$ 6–7/bbl).
        """)

        dados_corp = {
            "Fundação":            "3/10/1953 — Rio de Janeiro, RJ",
            "CEO":                 "Magda Chambriard (desde mai/2024)",
            "Funcionários":        "~45.000 (diretos) + ~100.000 (terceirizados)",
            "Listagem":            "B3: PETR3 (ON) / PETR4 (PN) · NYSE: PBR / PBR-A",
            "CNPJ":                "33.000.167/0001-01",
            "Receita (2023)":      "R$ 491,7 Bi",
            "Market Cap aprox.":   "~R$ 450 Bi (abr/2025)",
            "Produção diária":     "~2,78 milhões de boe/dia",
            "Reservas 2P":         "~12,1 bilhões de boe",
            "Refinarias no Brasil":"13 (capacidade total ~1,8 Mbbl/d)",
        }
        df_corp = pd.DataFrame(dados_corp.items(), columns=["Atributo", "Valor"])
        st.dataframe(df_corp, hide_index=True, use_container_width=True)

        st.markdown("### Estrutura Acionária")
        acion = {
            "Acionista": [
                "União Federal (direto)",
                "BNDESPAR",
                "Free Float ON (PETR3)",
                "Free Float PN (PETR4)",
                "Tesouraria / ADR / Outros",
            ],
            "% Capital Total": [36.6, 10.5, 6.8, 43.1, 3.0],
        }
        df_ac = pd.DataFrame(acion)
        fig_pie = px.pie(
            df_ac, values="% Capital Total", names="Acionista",
            color_discrete_sequence=["#0a2540","#1a4b8c","#3b82f6","#93c5fd","#e2e8f0"],
            hole=0.4,
        )
        fig_pie.update_traces(textposition="outside", textinfo="percent+label")
        fig_pie.update_layout(
            height=320, margin=dict(t=0, b=0, l=0, r=0),
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("""
        <div class="section-note">
        ⚠️ <b>Controle estatal:</b> O governo federal detém ~47% do capital total (direto + BNDES).
        Isso confere estabilidade de longo prazo, mas implica risco de intervenção na política
        de preços, dividendos e escolha de gestores.
        </div>""", unsafe_allow_html=True)

    with col_dir:
        st.markdown("### Presença Internacional")
        intl = pd.DataFrame({
            "País":      ["EUA","Argentina","Bolívia","Colômbia","Gabão","Angola","Namíbia","Tanzânia","Suriname"],
            "Operação":  ["Trading / P&D","E&P","E&P + Gás","E&P","E&P","E&P","Exploração","Exploração","Exploração"],
            "Relevância":["Média","Baixa","Baixa","Baixa","Baixa","Baixa","Alta Potencial","Potencial","Potencial"],
        })
        st.dataframe(intl, hide_index=True, use_container_width=True)

        st.markdown("### Ratings de Crédito")
        for agencia, nota, persp, det in [
            ("S&P Global", "BB+", "Estável", "Limitado pelo soberano BR"),
            ("Moody's",    "Ba1", "Estável", "Equivalente a BB+ S&P"),
            ("Fitch",      "BB+", "Estável", "Perspectiva melhorou em 2023"),
        ]:
            st.markdown(f"""
            <div class="rating-box">
              <b>{agencia}</b> &nbsp;
              <span style="font-size:1.25rem;font-weight:700;color:#92400e;">{nota}</span>
              &nbsp;<span style="color:#64748b;font-size:0.82rem;">| {persp} | {det}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("### Governança Corporativa")
        st.markdown("""
**Conselho de Administração:** 11 membros
&nbsp;&nbsp;└ 7 indicados pelo governo federal
&nbsp;&nbsp;└ 1 representante dos empregados
&nbsp;&nbsp;└ 3 independentes

**Nível B3:** Nível 2 (comprometimento com Governança)

**Compliance:**
- ISO 37001 (Sistema Antisuborno)
- FCPA / SOX compliance (listagem NYSE)
- Programa Integridade Petrobras

**Política de Dividendos:**
45% do FCL após juros e investimentos, desde que Dívida Líquida/EBITDA ≤ 2,5×
        """)

        st.markdown("### Linha do Tempo")
        timeline = {
            "1953": "Fundação da Petrobras",
            "1997": "Quebra do monopólio do petróleo",
            "2006": "Descoberta do pré-sal",
            "2010": "Capitalização histórica de R$ 120 Bi",
            "2014": "Início da Operação Lava Jato",
            "2019": "Início do plano de desalavancagem",
            "2022": "Lucro recorde de R$ 188,3 Bi",
            "2023": "Dívida líquida no menor nível histórico",
        }
        for ano, evento in timeline.items():
            st.markdown(
                f"<div style='display:flex;gap:10px;margin-bottom:5px;font-size:0.85rem;'>"
                f"<span style='color:#1a4b8c;font-weight:700;min-width:35px;'>{ano}</span>"
                f"<span>{evento}</span></div>",
                unsafe_allow_html=True
            )


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 2 — SEGMENTOS DE NEGÓCIO
# ═══════════════════════════════════════════════════════════════════════════════
with abas[2]:
    st.markdown("### Contribuição por Segmento (EBITDA 2023)")
    seg_data = pd.DataFrame({
        "Segmento":     ["E&P", "Refino, Transporte & Com.", "Gás & Energia", "Corp. / Eliminações"],
        "EBITDA (%)":   [71, 22, 5, 2],
        "EBITDA (R$Bi)":[145.1, 45.0, 10.2, 4.1],
    })
    c_pie, c_bar = st.columns(2)
    with c_pie:
        fig_seg = px.pie(seg_data, values="EBITDA (%)", names="Segmento",
                         color_discrete_sequence=["#0a2540","#1a4b8c","#3b82f6","#cbd5e1"])
        fig_seg.update_traces(textposition="inside", textinfo="percent+label")
        fig_seg.update_layout(height=280, margin=dict(t=0,b=0), showlegend=False)
        st.plotly_chart(fig_seg, use_container_width=True)
    with c_bar:
        fig_bar = px.bar(seg_data, x="Segmento", y="EBITDA (R$Bi)",
                         color="Segmento", text="EBITDA (R$Bi)",
                         color_discrete_sequence=["#0a2540","#1a4b8c","#3b82f6","#cbd5e1"])
        fig_bar.update_layout(showlegend=False, height=280,
                              margin=dict(t=10,b=0), plot_bgcolor="white")
        fig_bar.update_traces(texttemplate="R$ %{y:.1f} Bi", textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)

    # E&P
    with st.expander("⛽ E&P — Exploração & Produção (segmento principal, ~71% do EBITDA)", expanded=True):
        c1, c2 = st.columns([2, 1.5])
        with c1:
            st.markdown("""
**Principal motor de valor da companhia.** A Petrobras é a maior operadora do pré-sal
brasileiro, com participações em blocos nas bacias de **Santos e Campos**.

**Principais ativos:**
- **Campo de Búzios (Bacia de Santos):** Maior campo em produção do hemisfério sul.
  Produção de ~700 Mboe/d (2023). Petrobras é operadora com 100%.
- **Tupi / Lula:** Primeiro campo do pré-sal, ~300 Mboe/d.
- **Sépia, Atapu, Itapu:** Campos do excedente da cessão onerosa.
- **Bacia de Campos:** Produção madura, ~600 Mboe/d (pré e pós-sal).

**Destaques operacionais:**
| Indicador | 2021 | 2022 | 2023 |
|-----------|------|------|------|
| Produção total (Mboe/d) | 2.770 | 2.784 | 2.780 |
| Pré-sal (% da produção) | 63% | 67% | 72% |
| Custo de extração (US$/boe) | ~5,4 | ~5,8 | ~6,2 |
| Break-even fiscal (US$/bbl) | ~25 | ~28 | ~30 |
| Reservas 2P (Bi boe) | 11,5 | 12,0 | 12,1 |
| Índice de reposição de reservas | 115% | 118% | 121% |

**Vantagem competitiva:** Break-even operacional em torno de US$ 30/bbl coloca a Petrobras
entre as petrolíferas com menor custo de produção do mundo, atrás apenas de Aramco
e alguns campos do Oriente Médio.
            """)
        with c2:
            fig_prod = go.Figure()
            fig_prod.add_trace(go.Bar(
                x=df_prod["Ano"], y=df_prod["Produção Pré-Sal"],
                name="Pré-Sal", marker_color="#0a2540"))
            fig_prod.add_trace(go.Bar(
                x=df_prod["Ano"], y=df_prod["Produção Pós-Sal"],
                name="Pós-Sal / Outros", marker_color="#93c5fd"))
            fig_prod.update_layout(
                barmode="stack", title="Produção por Origem (Mboe/d)",
                height=300, margin=dict(t=40, b=0),
                plot_bgcolor="white", legend=dict(orientation="h", y=-0.15),
            )
            st.plotly_chart(fig_prod, use_container_width=True)

            fig_pressal = go.Figure(go.Scatter(
                x=df_prod["Ano"], y=df_prod["Pré-Sal (%)"],
                mode="lines+markers+text", line=dict(color="#0a2540", width=2.5),
                marker=dict(size=8), text=[f"{v}%" for v in df_prod["Pré-Sal (%)"]],
                textposition="top center",
            ))
            fig_pressal.update_layout(
                title="% Produção Pré-Sal", height=220,
                margin=dict(t=40, b=0), plot_bgcolor="white",
                yaxis=dict(range=[45, 80], ticksuffix="%"),
            )
            st.plotly_chart(fig_pressal, use_container_width=True)

    # Refino
    with st.expander("🏭 Refino, Transporte & Comercialização (~22% do EBITDA)"):
        c1, c2 = st.columns([1.5, 2])
        with c1:
            st.markdown("""
**13 refinarias no Brasil** com capacidade total de processamento de
aproximadamente **1,8 milhões de bbl/dia**, respondendo por ~70% do
refino nacional.

**Produtos principais (% da produção):**
- Diesel: ~40%
- Gasolina: ~22%
- Nafta / Petroquímicos: ~12%
- GLP / Outros: ~10%
- Querosene de aviação: ~8%
- Bunker / Fuel Oil: ~8%

**Taxa de utilização médias:** ~90–93%
**Margens de refino (2023):** US$ 11,4/bbl (benchmark Replan)
            """)
        with c2:
            df_ref_plot = df_refino.sort_values("Capacidade (Mbbl/d)", ascending=True)
            fig_ref = go.Figure(go.Bar(
                x=df_ref_plot["Capacidade (Mbbl/d)"],
                y=df_ref_plot["Refinaria"],
                orientation="h",
                marker_color="#1a4b8c",
                text=df_ref_plot["Capacidade (Mbbl/d)"],
                textposition="outside",
            ))
            fig_ref.update_layout(
                title="Capacidade de Refino por Unidade (Mbbl/d)",
                height=350, margin=dict(l=0, r=40, t=40, b=0),
                plot_bgcolor="white",
            )
            st.plotly_chart(fig_ref, use_container_width=True)

    # Gas
    with st.expander("🔥 Gás & Energia (~5% do EBITDA)"):
        st.markdown("""
**Segmento em crescimento**, beneficiado pela política de monetização do gás associado ao pré-sal
e pelo marco regulatório do **Novo Mercado de Gás (2021)**.

| Indicador | 2023 |
|-----------|------|
| Produção de gás natural (MM m³/d) | ~30 |
| Capacidade termeltétrica | ~5,2 GW |
| Participação no mercado de gás BR | ~30% |
| Extensão de gasodutos | ~9.000 km |

**Estratégia:** Monetizar o gás associado do pré-sal (antes reinjetado/queimado) via
vendas para distribuidoras, geração termelétrica e exportação para a Argentina/Bolívia.

**Operação Termelétrica:** A Petrobras opera usinas termoelétricas que despacham
em períodos de baixa hidraulicidade, gerando receita complementar e hedge natural
contra risco hídrico do sistema elétrico brasileiro.
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 3 — MERCADO & COMPETIDORES
# ═══════════════════════════════════════════════════════════════════════════════
with abas[3]:
    st.markdown("### Contexto do Mercado de Petróleo & Gás")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
**Mercado Global**
- Consumo mundial: ~103 Mbbl/d (2024)
- Produção OPEC+: ~43% do total
- EUA: maior produtor (~13 Mbbl/d)
- Brasil: ~3,6 Mbbl/d (7° maior produtor)
        """)
    with c2:
        st.markdown("""
**Dinâmica de Preços**
- WTI 2024: média ~US$ 77/bbl
- Brent 2024: média ~US$ 80/bbl
- Cenário base 2025: US$ 70–80/bbl
- Sensibilidade PETR: cada US$1/bbl ≈ R$ 2,5 Bi EBITDA
        """)
    with c3:
        st.markdown("""
**Brasil — Setor de E&P**
- Produção BR: ~3,6 Mbbl/d (ANP 2024)
- Petrobras: ~77% da produção nacional
- Pré-sal: ~78% da produção BR
- Royalties/Participações: ~R$ 150 Bi/ano ao governo
        """)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)

    # Preço do petróleo
    wti = preco_petroleo()
    if not wti.empty:
        st.markdown("### Preço do Petróleo WTI (US$/bbl) — 2024 a hoje")
        fig_wti = go.Figure()
        fig_wti.add_trace(go.Scatter(
            x=wti.index, y=wti["Close"].squeeze(),
            mode="lines", name="WTI",
            line=dict(color="#0a2540", width=2),
            fill="tozeroy", fillcolor="rgba(10,37,64,0.08)",
        ))
        fig_wti.add_hline(y=30, line_dash="dash", line_color="#22c55e",
                          annotation_text="Break-even Petrobras (~US$30)", annotation_position="top left")
        fig_wti.update_layout(
            height=300, margin=dict(t=10, b=0), plot_bgcolor="white",
            yaxis=dict(tickprefix="US$ "), xaxis=dict(showgrid=False),
            hovermode="x unified",
        )
        st.plotly_chart(fig_wti, use_container_width=True)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)
    st.markdown("### Principais Players Globais — Petrolíferas Integradas")

    st.markdown("""
| Empresa | País | Produção (Mboe/d) | Receita 2023 (USD Bi) | Net Debt/EBITDA | Rating S&P | Break-even (USD/bbl) |
|---------|------|-------------------|----------------------|-----------------|------------|----------------------|
| **Saudi Aramco** | Arábia Saudita | 12.000 | 440 | 0,1× | A+ | ~3 |
| **ExxonMobil** | EUA | 3.700 | 398 | 0,5× | AA- | ~35 |
| **Shell** | Reino Unido | 2.900 | 381 | 0,8× | A | ~40 |
| **TotalEnergies** | França | 2.500 | 237 | 0,7× | A+ | ~30 |
| **BP** | Reino Unido | 2.300 | 213 | 1,1× | A- | ~45 |
| **Equinor** | Noruega | 2.100 | 104 | -0,3× | AA- | ~37 |
| **Repsol** | Espanha | 650 | 54 | 0,5× | BBB | ~42 |
| **🇧🇷 Petrobras** | **Brasil** | **2.780** | **93** | **0,78×** | **BB+** | **~30** |
    """)

    st.markdown("""
    <div class="section-note">
    💡 <b>Observação:</b> O rating da Petrobras (BB+) é inferior ao de pares com métricas financeiras piores
    (ex.: BP com Net Debt/EBITDA de 1,1× e rating A-). Isso reflete o <b>teto soberano do Brasil</b> — uma
    empresa não pode ter rating superior ao do seu país de origem na escala global. Se o Brasil fosse
    investment grade, a Petrobras provavelmente teria rating A-/BBB+.
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)
    st.markdown("### Dados ao Vivo dos Pares (Yahoo Finance)")
    with st.spinner("Carregando dados dos pares..."):
        df_peers = peers_info()
    if not df_peers.empty:
        st.dataframe(df_peers.set_index("Empresa"), use_container_width=True)
    else:
        st.info("Dados dos pares indisponíveis no momento.")

    st.markdown("<hr class='div'>", unsafe_allow_html=True)
    st.markdown("### Mercado Doméstico Brasileiro — Posição da Petrobras")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**Produção de Petróleo & Gás (BR, 2024 — ANP):**
- Petrobras: **~77%** da produção nacional
- Shell Brasil: ~5%
- TotalEnergies Brasil: ~4%
- Equinor Brasil: ~3%
- Prio (ex-PetroRio): ~4%
- Outros: ~7%

**Refino:**
- Petrobras: ~72% da capacidade instalada
- Raízen + Manguinhos + Outros: ~28%

**Distribuição de Combustíveis:**
- Vibra Energia (ex-BR Distribuidora): ~26% do mercado
- Raízen: ~27%
- Ipiranga (Ultra): ~23%
- Outros: ~24%
        """)
        prod_brasil = pd.DataFrame({
            "Empresa": ["Petrobras", "Shell BR", "TotalEnergies", "Equinor BR", "Prio", "Outros"],
            "%": [77, 5, 4, 3, 4, 7],
        })
        fig_br = px.pie(prod_brasil, values="%", names="Empresa",
                        color_discrete_sequence=["#0a2540","#1a4b8c","#3b82f6","#60a5fa","#93c5fd","#e2e8f0"])
        fig_br.update_traces(textposition="inside", textinfo="percent+label")
        fig_br.update_layout(height=280, margin=dict(t=0,b=0), showlegend=False,
                             title="Produção de Petróleo no Brasil (2024)")
        st.plotly_chart(fig_br, use_container_width=True)
    with col_b:
        st.markdown("""
**Ambiente Competitivo — Análise das 5 Forças de Porter:**

🔴 **Rivalidade Concorrentes:** BAIXA
Petrobras é monopólio de fato na produção BR; concorrência aumenta gradualmente com
rodadas de concessão da ANP, mas pré-sal confere barreira técnica elevada.

🟡 **Ameaça de Novos Entrantes:** MÉDIA
Rodadas de licitação atraem Shell, TotalEnergies, Equinor, mas vantagem do pré-sal
(know-how, infraestrutura, FPSO) cria barreira considerável.

🟡 **Poder dos Fornecedores:** MÉDIO
Dependência de estaleiros (FPSO), serviços de sísmica e perfuração. Petrobras é
cliente dominante e tem poder de negociação significativo.

🟢 **Poder dos Compradores:** BAIXO
Commodities globais precificados em dólares. Não existe single buyer dominante.

🟡 **Ameaça de Substitutos:** MÉDIA (longo prazo)
Transição energética e veículos elétricos reduzem demanda futura de gasolina, mas
petróleo continuará relevante para aviação, petroquímica e transporte pesado por décadas.
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 4 — INDICADORES FINANCEIROS
# ═══════════════════════════════════════════════════════════════════════════════
with abas[4]:
    st.markdown("### Demonstrações Financeiras Históricas (2019–2023)")

    # Receita + EBITDA + Lucro
    fig_dre = go.Figure()
    fig_dre.add_trace(go.Bar(
        x=ANOS, y=df_fin["Receita Líquida (R$ Bi)"],
        name="Receita Líquida", marker_color="#cbd5e1",
    ))
    fig_dre.add_trace(go.Bar(
        x=ANOS, y=df_fin["EBITDA (R$ Bi)"],
        name="EBITDA", marker_color="#1a4b8c",
    ))
    fig_dre.add_trace(go.Scatter(
        x=ANOS, y=df_fin["Lucro Líquido (R$ Bi)"],
        name="Lucro Líquido", mode="lines+markers",
        line=dict(color="#f59e0b", width=2.5), marker=dict(size=8), yaxis="y2",
    ))
    fig_dre.update_layout(
        title="Receita Líquida, EBITDA e Lucro Líquido (R$ Bi)",
        barmode="overlay",
        yaxis=dict(title="R$ Bi", showgrid=True, gridcolor="#f1f5f9"),
        yaxis2=dict(title="Lucro Líquido (R$ Bi)", overlaying="y", side="right"),
        height=380, margin=dict(t=50, b=0), plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.15),
        hovermode="x unified",
    )
    st.plotly_chart(fig_dre, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        # Dívida líquida
        fig_div = go.Figure()
        fig_div.add_trace(go.Bar(
            x=ANOS, y=df_fin["Dívida Bruta (R$ Bi)"],
            name="Dívida Bruta", marker_color="#fca5a5",
        ))
        fig_div.add_trace(go.Bar(
            x=ANOS, y=[-v for v in df_fin["Caixa (R$ Bi)"]],
            name="Caixa (–)", marker_color="#86efac",
        ))
        fig_div.add_trace(go.Scatter(
            x=ANOS, y=df_fin["Dívida Líquida (R$ Bi)"],
            mode="lines+markers+text", name="Dívida Líquida",
            line=dict(color="#0a2540", width=2.5), marker=dict(size=8),
            text=[f"R${v:.0f}Bi" for v in df_fin["Dívida Líquida (R$ Bi)"]],
            textposition="top center",
        ))
        fig_div.update_layout(
            title="Estrutura de Dívida (R$ Bi)", barmode="overlay",
            height=320, margin=dict(t=50, b=0), plot_bgcolor="white",
            legend=dict(orientation="h", y=-0.18), hovermode="x unified",
        )
        st.plotly_chart(fig_div, use_container_width=True)

    with c2:
        # Alavancagem
        fig_alav = go.Figure()
        fig_alav.add_trace(go.Bar(
            x=ANOS, y=df_fin["Dív.Líq/EBITDA"],
            name="Dív.Líq/EBITDA", marker_color=[
                "#ef4444" if v > 2.0 else "#f59e0b" if v > 1.2 else "#22c55e"
                for v in df_fin["Dív.Líq/EBITDA"]
            ],
            text=[f"{v:.2f}×" for v in df_fin["Dív.Líq/EBITDA"]],
            textposition="outside",
        ))
        fig_alav.add_hline(y=2.5, line_dash="dash", line_color="#ef4444",
                           annotation_text="Covenant: 2,5×", annotation_position="top right")
        fig_alav.add_hline(y=1.5, line_dash="dot", line_color="#f59e0b",
                           annotation_text="Alerta: 1,5×", annotation_position="top right")
        fig_alav.update_layout(
            title="Alavancagem: Dívida Líquida / EBITDA",
            height=320, margin=dict(t=50, b=0), plot_bgcolor="white",
            yaxis=dict(range=[0, 4.5], ticksuffix="×"),
        )
        st.plotly_chart(fig_alav, use_container_width=True)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)
    st.markdown("### Principais Indicadores — Tabela Completa")

    df_ratios = pd.DataFrame({
        "Indicador": [
            "Receita Líquida (R$ Bi)", "EBITDA (R$ Bi)", "Margem EBITDA (%)",
            "Lucro Líquido (R$ Bi)", "Margem Líquida (%)",
            "Capex (R$ Bi)", "Free Cash Flow (R$ Bi)",
            "Dívida Bruta (R$ Bi)", "Caixa (R$ Bi)", "Dívida Líquida (R$ Bi)",
            "Dívida Líquida / EBITDA", "ROIC (%)", "ROE (%)",
        ],
    })
    for i, ano in enumerate(ANOS):
        col_vals = [
            f"{df_fin['Receita Líquida (R$ Bi)'].iloc[i]:.1f}",
            f"{df_fin['EBITDA (R$ Bi)'].iloc[i]:.1f}",
            f"{df_fin['Margem EBITDA (%)'].iloc[i]:.1f}%",
            f"{df_fin['Lucro Líquido (R$ Bi)'].iloc[i]:.1f}",
            f"{df_fin['Margem Líquida (%)'].iloc[i]:.1f}%",
            f"{df_fin['Capex (R$ Bi)'].iloc[i]:.1f}",
            f"{df_fin['FCL (R$ Bi)'].iloc[i]:.1f}",
            f"{df_fin['Dívida Bruta (R$ Bi)'].iloc[i]:.1f}",
            f"{df_fin['Caixa (R$ Bi)'].iloc[i]:.1f}",
            f"{df_fin['Dívida Líquida (R$ Bi)'].iloc[i]:.1f}",
            f"{df_fin['Dív.Líq/EBITDA'].iloc[i]:.2f}×",
            f"{df_fin['ROIC (%)'].iloc[i]:.1f}%",
            f"{df_fin['ROE (%)'].iloc[i]:.1f}%",
        ]
        df_ratios[str(ano)] = col_vals

    st.dataframe(df_ratios.set_index("Indicador"), use_container_width=True)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)
    st.markdown("### Análise de Sensibilidade — Preço do Petróleo vs. EBITDA")
    st.markdown("""
Impacto estimado no EBITDA 2025E com variações no preço do Brent (base: US$ 75/bbl):

| Cenário | Preço Brent | EBITDA 2025E | FCL 2025E | Dív.Líq/EBITDA | Conclusão |
|---------|-------------|-------------|-----------|----------------|-----------|
| 🐻 Bear | US$ 50/bbl | ~R$ 140 Bi | ~R$ 40 Bi | ~1,1× | Confortável |
| ⚖️ Base | US$ 75/bbl | ~R$ 210 Bi | ~R$ 90 Bi | ~0,75× | Excelente |
| 🐂 Bull | US$ 95/bbl | ~R$ 270 Bi | ~R$ 130 Bi | ~0,58× | Excepcional |
| 💀 Stress | US$ 35/bbl | ~R$ 80 Bi | ~R$ 10 Bi | ~1,95× | Administrável |
    """)
    st.markdown("""
    <div class="section-note">
    🔑 <b>Insight principal:</b> Mesmo em cenário de stress severo (Brent a US$35/bbl —
    nível observado apenas em crises extremas como COVID-2020), a Petrobras manteria
    Dívida Líquida/EBITDA abaixo do covenant de 2,5×, demonstrando resiliência
    excepcional do seu modelo de negócios.
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 5 — ANÁLISE DE RISCO
# ═══════════════════════════════════════════════════════════════════════════════
with abas[5]:
    st.markdown("### Matriz de Riscos")

    riscos = [
        # (Fator, Probabilidade, Impacto, Mitigação, Classificação)
        ("Queda abrupta do preço do petróleo",    "Média",  "Alto",   "Break-even ~US$30; hedge natural; FCL robusto",             "Moderado"),
        ("Intervenção política (preços/dividendos)","Alta",  "Médio",  "Política de dividendos indexada a FCL; pressão ESG reduz",  "Moderado"),
        ("Piora do rating soberano do Brasil",    "Baixa",  "Alto",   "Dívida em USD parcialmente hedgeada; fluxo em USD",         "Moderado"),
        ("Acidente ambiental / vazamento",        "Baixa",  "Muito Alto","Seg. obrigatório; resposta a emergências certificada",   "Alto"),
        ("Elevação de juros / refinanciamento",   "Média",  "Médio",  "Prazo médio de dívida ~8 anos; boa liquidez",               "Baixo"),
        ("Transição energética acelerada",        "Baixa",  "Alto",   "Portfólio ainda relevante em 2040; gás como transitório",   "Moderado"),
        ("Riscos cibernéticos / operacionais",    "Média",  "Médio",  "Investimento em segurança digital pós-2022",                "Baixo"),
        ("Litígios / passivos da Lava Jato",      "Baixa",  "Médio",  "Maioria encerrada; provisionamento adequado",               "Baixo"),
        ("Descobertas de nova margem equatorial", "Alta",   "Alto",   "Potencial upside significativo",                            "Oportunidade"),
    ]

    for fator, prob, impacto, mitig, classe in riscos:
        if classe == "Alto":
            cls = "risk-alto"
            icone = "🔴"
        elif classe == "Moderado":
            cls = "risk-medio"
            icone = "🟡"
        elif classe == "Oportunidade":
            cls = "risk-baixo"
            icone = "🟢"
        else:
            cls = "risk-baixo"
            icone = "🟢"

        st.markdown(f"""
        <div class="{cls}">
          <b>{icone} {fator}</b>
          <span style="float:right;font-size:0.8rem;color:#64748b;">
            Prob: {prob} &nbsp;|&nbsp; Impacto: {impacto} &nbsp;|&nbsp; <b>{classe}</b>
          </span>
          <br><span style="font-size:0.85rem;color:#475569;">Mitigação: {mitig}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)

    c_esg, c_pol = st.columns(2)

    with c_esg:
        st.markdown("### Riscos ESG")
        st.markdown("""
**Ambiental:**
- Emissões de CO₂ Scope 1+2: ~60 Mt CO₂eq/ano
- Meta: neutralidade de carbono até 2050
- Queima de gás: reduzida ~80% vs. pré-pré-sal
- Investimento em energias renováveis: R$ 11 Bi no plano 2024-2028

**Social:**
- ~45.000 funcionários diretos com benefícios robustos
- Programa de conteúdo local: ~68% de compras nacionais
- Impacto nas comunidades petrolíferas (RJ, ES, BA, RN)

**Governança:**
- Principal risco: interferência política
- Troca de CEO em 2023 e 2024 gerou volatilidade
- Compliance reforçado pós-Lava Jato
- Comitê de Auditoria independente (NYSE exige)

**Avaliação ESG (MSCI):** BB (melhoria de B em 2021)
**ISE B3:** Incluída no índice de sustentabilidade
        """)

    with c_pol:
        st.markdown("### Risco Político")
        st.markdown("""
**Principal vetor de risco qualitativo da tese.**

O governo federal controla ~47% do capital e indica
a maioria do Conselho de Administração, o que cria
tensão entre os objetivos de política pública e a
maximização de valor para o acionista.

**Episódios históricos de interferência:**
- 2011-2014: Política de preços abaixo do mercado
  levou a prejuízos bilionários na Refinaria Abreu e Lima
- 2022: Pressão para reduzir preços de combustíveis
  durante a crise inflacionária
- 2023: Suspensão de dividendos extraordinários e
  troca de CEO por decisão do governo

**Mitigadores:**
- Listagem na NYSE (SOX, FCPA): disciplina gestão
- Pressão de acionistas minoritários via CVM
- Histórico mostra que crises políticas foram contidas
- Nova política de dividendos baseada em FCL reduz arbitrariedade

**Nível de risco:** MODERADO
(elevado vs. pares privados, baixo vs. Pemex/PDVSA)
        """)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)
    st.markdown("### Monitoramento de Covenants Sugeridos")

    covenants = {
        "Covenant / KPI":         ["Dív.Líq/EBITDA", "Dívida Líquida (R$Bi)", "Caixa Mínimo (R$Bi)", "Cobertura de Juros (EBIT/Desp.Fin.)", "Produção (Mboe/d min.)"],
        "Limite Máximo/Mínimo":   ["≤ 2,5×", "≤ R$ 280 Bi", "≥ R$ 30 Bi", "≥ 3,0×", "≥ 2,4 Mboe/d"],
        "Nível Atual (2023)":     ["0,78×", "R$ 159 Bi", "R$ 62 Bi", "8,2×", "2,78 Mboe/d"],
        "Headroom":               ["▲ 220%", "▲ 76%", "▲ 107%", "▲ 173%", "▲ 16%"],
        "Risco de Breach":        ["🟢 Muito Baixo", "🟢 Muito Baixo", "🟢 Baixo", "🟢 Muito Baixo", "🟢 Baixo"],
    }
    st.dataframe(pd.DataFrame(covenants), hide_index=True, use_container_width=True)

    st.markdown("<hr class='div'>", unsafe_allow_html=True)

    st.markdown("### ✅ Conclusão e Recomendação de Crédito")
    st.success("""
**RECOMENDAÇÃO: APROVAÇÃO DO CRÉDITO**

A Petrobras apresenta um dos perfis de crédito mais sólidos entre empresas de grau sub-investment
grade globalmente. Seus fundamentos financeiros (Dívida Líquida/EBITDA de 0,78×, FCL de R$ 80 Bi,
caixa de R$ 62 Bi) justificam tratamento diferenciado versus outros BBs.

**Condições sugeridas para aprovação:**
1. Covenant de Dívida Líquida/EBITDA ≤ 2,5×
2. Covenant de caixa mínimo ≥ R$ 25 Bi
3. Monitoramento semestral dos demonstrativos financeiros
4. Cláusula MAC (Material Adverse Change) para evento de interferência política comprovada
5. Revisão automática em caso de downgrade do rating soberano do Brasil abaixo de B+

**Próxima revisão:** Outubro/2025 (resultados 2T25)
    """)
