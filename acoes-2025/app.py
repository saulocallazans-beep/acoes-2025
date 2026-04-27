import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import date

ACOES = {
    "Petrobras (PETR4)": "PETR4.SA",
    "Itaú (ITUB4)": "ITUB4.SA",
    "Vale (VALE3)": "VALE3.SA",
}

st.set_page_config(page_title="Cotações 2025", page_icon="📈", layout="wide")
st.title("📈 Cotações de Ações — 2025")

with st.sidebar:
    st.header("Selecione a ação")
    nome_acao = st.radio("", list(ACOES.keys()))

ticker = ACOES[nome_acao]

@st.cache_data(ttl=300)
def carregar_dados(ticker):
    df = yf.download(ticker, start="2025-01-01", end=date.today().isoformat(), progress=False)
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    return df

with st.spinner("Carregando dados..."):
    df = carregar_dados(ticker)

if df.empty:
    st.error("Não foi possível carregar os dados. Tente novamente.")
    st.stop()

preco_atual = float(df["Close"].iloc[-1])
preco_anterior = float(df["Close"].iloc[-2]) if len(df) > 1 else preco_atual
variacao = ((preco_atual - preco_anterior) / preco_anterior) * 100
maxima = float(df["High"].max())
minima = float(df["Low"].min())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Preço atual", f"R$ {preco_atual:.2f}", f"{variacao:+.2f}%")
col2.metric("Variação do dia", f"{variacao:+.2f}%")
col3.metric("Máxima 2025", f"R$ {maxima:.2f}")
col4.metric("Mínima 2025", f"R$ {minima:.2f}")

st.subheader(f"Gráfico Candlestick — {nome_acao}")

fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    increasing_line_color="#26a69a",
    decreasing_line_color="#ef5350",
)])

fig.update_layout(
    xaxis_title="Data",
    yaxis_title="Preço (R$)",
    xaxis_rangeslider_visible=False,
    height=500,
    plot_bgcolor="#0e1117",
    paper_bgcolor="#0e1117",
    font_color="#fafafa",
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Últimos 10 pregões")
tabela = df[["Open", "High", "Low", "Close", "Volume"]].tail(10).sort_index(ascending=False).copy()
tabela.index = tabela.index.strftime("%d/%m/%Y")
tabela.columns = ["Abertura", "Máxima", "Mínima", "Fechamento", "Volume"]
for col in ["Abertura", "Máxima", "Mínima", "Fechamento"]:
    tabela[col] = tabela[col].map(lambda x: f"R$ {x:.2f}")
tabela["Volume"] = tabela["Volume"].map(lambda x: f"{int(x):,}".replace(",", "."))
st.dataframe(tabela, use_container_width=True)
