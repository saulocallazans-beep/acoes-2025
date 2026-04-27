"""
app_credito.py — Análise de Crédito Corporativo (Web)
Uso: streamlit run analise-credito/app_credito.py
"""

import re
import requests
import feedparser
import pandas as pd
import streamlit as st
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_cnpj(v: str) -> str:
    return re.sub(r"\D", "", v)

def fmt_cnpj(cnpj: str) -> str:
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

def fmt_brl(valor) -> str:
    try:
        return f"R$ {float(valor):_.2f}".replace("_", ".").replace(".", ",", 1).replace(",", ".", 1)
    except Exception:
        return str(valor)

# ── Consultas ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_cnpj(cnpj: str) -> dict:
    r = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=15)
    r.raise_for_status()
    return r.json()


def check_pgfn(cnpj: str) -> dict:
    """Consulta PGFN via Playwright headless (reCAPTCHA v3 costuma auto-resolver)."""
    resultado = {"status": "—", "devedores": [], "erro": None}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
            )
            page = ctx.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            )

            page.goto("https://www.listadevedores.pgfn.gov.br/", wait_until="networkidle", timeout=30_000)

            input_sel = 'input[type="text"], input[placeholder*="CNPJ"], input[name="ni"]'
            page.wait_for_selector(input_sel, timeout=10_000)
            page.fill(input_sel, fmt_cnpj(cnpj))

            btn_sel = 'button[type="submit"], button:has-text("Pesquisar"), button:has-text("Buscar")'
            try:
                page.click(btn_sel)
            except Exception:
                page.keyboard.press("Enter")

            page.wait_for_timeout(4_000)
            body = page.locator("body").inner_text().lower()

            sem_divida = ["não há dados", "nenhum devedor", "não foram encontrados", "não consta"]
            if any(m in body for m in sem_divida):
                resultado["status"] = "✅ REGULAR — Não consta na lista de devedores"
            else:
                try:
                    rows = page.locator("table tbody tr").all()
                    for row in rows:
                        cells = [c.strip() for c in row.locator("td").all_text_contents() if c.strip()]
                        if cells:
                            resultado["devedores"].append(cells)
                except Exception:
                    pass

                if resultado["devedores"]:
                    resultado["status"] = f"🔴 DEVEDOR — {len(resultado['devedores'])} registro(s)"
                elif "devedor" in body or "débito" in body:
                    resultado["status"] = "🔴 DEVEDOR — Consta na lista"
                else:
                    resultado["status"] = "⚠️ Resultado inconclusivo (verifique manualmente)"

            browser.close()
    except Exception as exc:
        resultado["erro"] = str(exc)
        resultado["status"] = "⚠️ Consulta não concluída automaticamente"

    return resultado


@st.cache_data(ttl=600, show_spinner=False)
def fetch_news(nome: str) -> list[dict]:
    query = f'"{nome}" fraude OR falência OR investigação OR "recuperação judicial" OR irregularidade OR calote'
    url = (
        "https://news.google.com/rss/search"
        f"?q={requests.utils.quote(query)}&hl=pt-BR&gl=BR&ceid=BR:pt-BR"
    )
    try:
        feed = feedparser.parse(url)
        return [
            {
                "Data": e.get("published", "")[:16],
                "Fonte": e.get("source", {}).get("title", "—"),
                "Título": e.get("title", ""),
                "Link": e.get("link", ""),
            }
            for e in feed.entries[:10]
        ]
    except Exception:
        return []


# ── Configuração da página ─────────────────────────────────────────────────────

st.set_page_config(
    page_title="Análise de Crédito",
    page_icon="🏦",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f8fafc; }
.header-card {
    background: linear-gradient(135deg, #0a2540 0%, #1e40af 100%);
    padding: 1.6rem 2rem; border-radius: 10px; color: white; margin-bottom: 1.5rem;
}
.header-card h2 { margin: 0; font-size: 1.5rem; font-weight: 700; }
.header-card p  { margin: 0.3rem 0 0; opacity: 0.8; font-size: 0.85rem; }
.badge {
    display: inline-block; padding: 2px 12px; border-radius: 20px;
    font-size: 0.78rem; font-weight: 700; margin: 3px 3px 0 0;
}
.badge-green  { background:#d1fadf; color:#166534; }
.badge-red    { background:#fee2e2; color:#991b1b; }
.badge-blue   { background:#dbeafe; color:#1e40af; }
.badge-yellow { background:#fef9c3; color:#854d0e; }
.kpi { background:white; border-left:4px solid #1e40af; padding:12px 16px; border-radius:6px; }
.kpi-label { color:#64748b; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em; }
.kpi-value { color:#0f172a; font-size:1.3rem; font-weight:700; }
hr.sec { border:none; border-top:1px solid #e2e8f0; margin:1rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-card">
  <h2>🏦 Análise de Crédito Corporativo</h2>
  <p>Receita Federal · PGFN · Notícias · Quadro Societário</p>
</div>
""", unsafe_allow_html=True)

# ── Formulário ────────────────────────────────────────────────────────────────

with st.form("form_cnpj"):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        cnpj_raw = st.text_input(
            "CNPJ",
            placeholder="00.000.000/0001-00",
            label_visibility="collapsed",
        )
    with col_btn:
        submitted = st.form_submit_button("Consultar →", type="primary", use_container_width=True)

# ── Processamento ─────────────────────────────────────────────────────────────

if submitted:
    cnpj = clean_cnpj(cnpj_raw)
    if len(cnpj) != 14:
        st.error("CNPJ inválido. Verifique o número digitado.")
        st.stop()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        with st.spinner("Receita Federal..."):
            try:
                dados = fetch_cnpj(cnpj)
                dados_ok = True
            except Exception as e:
                st.error(f"Erro na consulta da Receita Federal: {e}")
                st.stop()

    with col_b:
        with st.spinner("PGFN (Lista de Devedores)..."):
            pgfn = check_pgfn(cnpj)

    nome = dados.get("razao_social") or cnpj
    with col_c:
        with st.spinner(f"Notícias sobre {nome[:25]}..."):
            noticias = fetch_news(nome)

    # ── Card de resumo ────────────────────────────────────────────────────────

    sit = dados.get("descricao_situacao_cadastral", "")
    sit_color = "badge-green" if sit.upper() == "ATIVA" else "badge-red"
    pgfn_color = "badge-green" if "REGULAR" in pgfn["status"].upper() else "badge-yellow"

    st.markdown(f"""
    <div class="header-card" style="background:linear-gradient(135deg,#0f172a,#1e3a5f);">
      <h2>{dados.get('razao_social','—')}</h2>
      <p>{fmt_cnpj(cnpj)} &nbsp;|&nbsp; {dados.get('municipio','')}/{dados.get('uf','')}
         &nbsp;|&nbsp; Abertura: {dados.get('data_inicio_atividade','—')}</p>
      <div style="margin-top:.6rem;">
        <span class="badge {sit_color}">{sit or '—'}</span>
        <span class="badge {pgfn_color}">PGFN: {pgfn['status'][:40]}</span>
        <span class="badge badge-blue">{dados.get('porte','—')}</span>
        <span class="badge badge-blue">Capital: {fmt_brl(dados.get('capital_social',0))}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Abas ──────────────────────────────────────────────────────────────────

    aba1, aba2, aba3, aba4, aba5 = st.tabs([
        "📋 Dados Cadastrais",
        "👥 Quadro Societário",
        "🏭 CNAEs",
        "⚠️ PGFN",
        "📰 Notícias",
    ])

    # ── Aba 1 — Dados Cadastrais ──────────────────────────────────────────────
    with aba1:
        col1, col2 = st.columns(2)

        cadastro_esq = {
            "Razão Social":       dados.get("razao_social", "—"),
            "Nome Fantasia":      dados.get("nome_fantasia") or "—",
            "CNPJ":               fmt_cnpj(dados.get("cnpj", "")),
            "Situação Cadastral": sit,
            "Data da Situação":   dados.get("data_situacao_cadastral") or "—",
            "Motivo":             dados.get("descricao_motivo_situacao_cadastral") or "—",
            "Natureza Jurídica":  dados.get("natureza_juridica", "—"),
            "Porte":              dados.get("porte", "—"),
            "Capital Social":     fmt_brl(dados.get("capital_social", 0)),
            "Matriz / Filial":    dados.get("descricao_identificador_matriz_filial", "—"),
        }
        cadastro_dir = {
            "Data de Abertura":   dados.get("data_inicio_atividade", "—"),
            "Regime Tributário":  str(dados.get("regime_tributario", "—")),
            "Simples Nacional":   "Sim" if dados.get("opcao_pelo_simples") else "Não",
            "MEI":                "Sim" if dados.get("opcao_pelo_mei") else "Não",
            "CNAE Principal":     f"{dados.get('cnae_fiscal','')} — {dados.get('cnae_fiscal_descricao','—')}",
            "Endereço":           " ".join(filter(None, [
                                      dados.get("descricao_tipo_de_logradouro",""),
                                      dados.get("logradouro",""), dados.get("numero",""),
                                      dados.get("complemento","") or "",
                                      dados.get("bairro",""),
                                  ])),
            "Município / UF":     f"{dados.get('municipio','')}/{dados.get('uf','')}",
            "CEP":                dados.get("cep", "—"),
            "Telefone":           " / ".join(filter(None,[dados.get("ddd_telefone_1",""), dados.get("ddd_telefone_2","")])) or "—",
            "E-mail":             dados.get("email") or "—",
        }

        with col1:
            st.dataframe(
                pd.DataFrame(cadastro_esq.items(), columns=["Campo", "Valor"]),
                hide_index=True, use_container_width=True,
            )
        with col2:
            st.dataframe(
                pd.DataFrame(cadastro_dir.items(), columns=["Campo", "Valor"]),
                hide_index=True, use_container_width=True,
            )

        st.markdown("<hr class='sec'>", unsafe_allow_html=True)
        st.caption(
            "📄 Para gerar o Comprovante de Inscrição oficial (PDF com validade jurídica), acesse: "
            f"[Receita Federal →](https://solucoes.receita.fazenda.gov.br/servicos/cnpjreva/Cnpjreva_Solicitacao.asp)"
            " (requer resolução manual de hCaptcha)"
        )

    # ── Aba 2 — Quadro Societário ─────────────────────────────────────────────
    with aba2:
        socios = dados.get("qsa", [])
        if not socios:
            st.info("Nenhum sócio informado para este CNPJ.")
        else:
            df_socios = pd.DataFrame([
                {
                    "Nome":              s.get("nome_socio", "—"),
                    "Qualificação":      s.get("qualificacao_socio", "—"),
                    "CPF / CNPJ":        s.get("cnpj_cpf_do_socio", "—"),
                    "Faixa Etária":      s.get("faixa_etaria") or "—",
                    "Data de Entrada":   s.get("data_entrada_sociedade") or "—",
                    "Rep. Legal":        s.get("nome_representante_legal") or "—",
                    "Qualif. Rep.":      s.get("qualificacao_representante_legal") or "—",
                }
                for s in socios
            ])
            st.dataframe(df_socios, hide_index=True, use_container_width=True)
            st.caption(f"{len(socios)} membro(s) no Quadro de Sócios e Administradores (QSA)")

    # ── Aba 3 — CNAEs ─────────────────────────────────────────────────────────
    with aba3:
        st.markdown(f"**CNAE Principal:** `{dados.get('cnae_fiscal','')}` — {dados.get('cnae_fiscal_descricao','—')}")
        st.markdown("<hr class='sec'>", unsafe_allow_html=True)

        cnaes_sec = dados.get("cnaes_secundarios", [])
        if not cnaes_sec:
            st.info("Nenhum CNAE secundário cadastrado.")
        else:
            df_cnaes = pd.DataFrame([
                {"Código": str(c.get("codigo", "")), "Descrição": c.get("descricao", "")}
                for c in cnaes_sec
            ])
            st.dataframe(df_cnaes, hide_index=True, use_container_width=True)
            st.caption(f"{len(cnaes_sec)} atividade(s) econômica(s) secundária(s)")

    # ── Aba 4 — PGFN ─────────────────────────────────────────────────────────
    with aba4:
        status_pgfn = pgfn["status"]
        if "REGULAR" in status_pgfn.upper():
            st.success(status_pgfn)
        elif "DEVEDOR" in status_pgfn.upper():
            st.error(status_pgfn)
        else:
            st.warning(status_pgfn)

        if pgfn.get("erro"):
            st.caption(f"Detalhe técnico: {pgfn['erro']}")

        devedores = pgfn.get("devedores", [])
        if devedores:
            st.markdown("**Registros encontrados:**")
            df_dev = pd.DataFrame(devedores)
            st.dataframe(df_dev, hide_index=True, use_container_width=True)

        st.markdown("<hr class='sec'>", unsafe_allow_html=True)
        pgfn_url = "https://www.listadevedores.pgfn.gov.br/"
        st.caption(
            f"Consulta automática via headless browser. Para resultado definitivo: "
            f"[Lista de Devedores PGFN →]({pgfn_url})"
        )

    # ── Aba 5 — Notícias ──────────────────────────────────────────────────────
    with aba5:
        if not noticias:
            st.success("Nenhuma notícia negativa encontrada para esta empresa.")
        else:
            for n in noticias:
                st.markdown(
                    f"**{n['Data']}** — {n['Fonte']}  \n"
                    f"[{n['Título']}]({n['Link']})"
                )
                st.markdown("<hr class='sec'>", unsafe_allow_html=True)
            st.caption(
                "Fonte: Google News RSS. Verifique os links originais antes de registrar no parecer."
            )
