#!/usr/bin/env python3
"""
consulta_cnpj.py — Análise de crédito via terminal
Uso: python consulta_cnpj.py <CNPJ>
"""

import sys
import re
import asyncio
import requests
import feedparser
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from playwright.async_api import async_playwright

console = Console()


def clean_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj)


def fmt_cnpj(cnpj: str) -> str:
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def fmt_brl(valor) -> str:
    try:
        return f"R$ {float(valor):_.2f}".replace("_", ".").replace(".", ",", 1).replace(",", ".", 1)
    except Exception:
        return str(valor)


# ── 1. Receita Federal via Brasil API ─────────────────────────────────────────

def fetch_cnpj(cnpj: str) -> dict:
    r = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=15)
    r.raise_for_status()
    return r.json()


# ── 2. PGFN via Playwright (browser real para resolver reCAPTCHA) ─────────────

async def fetch_pgfn(cnpj: str) -> dict:
    """
    Abre o browser, navega até listadevedores.pgfn.gov.br,
    pesquisa o CNPJ e retorna o resultado como dict.
    """
    resultado = {"status": None, "devedores": []}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        page = await browser.new_page()

        await page.goto(
            "https://www.listadevedores.pgfn.gov.br/",
            wait_until="networkidle",
            timeout=30_000,
        )

        # Preenche o campo de busca
        input_sel = 'input[type="text"], input[placeholder*="CNPJ"], input[placeholder*="CPF"], input[name="ni"]'
        try:
            await page.wait_for_selector(input_sel, timeout=10_000)
            await page.fill(input_sel, fmt_cnpj(cnpj))
        except Exception:
            resultado["status"] = "Não foi possível localizar o campo de pesquisa"
            await browser.close()
            return resultado

        # Clica em pesquisar
        btn_sel = 'button[type="submit"], button:has-text("Pesquisar"), button:has-text("Buscar")'
        try:
            await page.click(btn_sel)
        except Exception:
            await page.keyboard.press("Enter")

        # Aguarda resposta da página
        await page.wait_for_timeout(4_000)

        body_text = await page.locator("body").inner_text()
        body_lower = body_text.lower()

        # Verifica se há resultado de "sem dívida"
        sem_divida_markers = [
            "não há dados",
            "nenhum devedor",
            "não foram encontrados",
            "não consta",
            "sem débitos",
        ]
        if any(m in body_lower for m in sem_divida_markers):
            resultado["status"] = "REGULAR — Não consta na lista de devedores"
            await browser.close()
            return resultado

        # Tenta extrair tabela de dívidas
        try:
            rows = await page.locator("table tbody tr").all()
            for row in rows:
                cells = await row.locator("td").all_text_contents()
                cells = [c.strip() for c in cells if c.strip()]
                if cells:
                    resultado["devedores"].append(cells)
        except Exception:
            pass

        if resultado["devedores"]:
            resultado["status"] = f"DEVEDOR — {len(resultado['devedores'])} registro(s) encontrado(s)"
        elif "devedor" in body_lower or "débito" in body_lower:
            resultado["status"] = "DEVEDOR — Consta na lista (detalhes no browser)"
        else:
            resultado["status"] = "Resultado indeterminado — verifique o browser"

        await browser.close()

    return resultado


# ── 3. Notícias negativas via Google News RSS ─────────────────────────────────

def fetch_news(nome: str) -> list[dict]:
    query = f'"{nome}" fraude OR falência OR investigação OR "recuperação judicial" OR irregularidade OR preso OR calote'
    url = (
        "https://news.google.com/rss/search"
        f"?q={requests.utils.quote(query)}&hl=pt-BR&gl=BR&ceid=BR:pt-BR"
    )
    try:
        feed = feedparser.parse(url)
        return [
            {
                "data": e.get("published", "")[:16],
                "fonte": e.get("source", {}).get("title", "—"),
                "titulo": e.get("title", ""),
            }
            for e in feed.entries[:8]
        ]
    except Exception as exc:
        return [{"data": "", "fonte": "Erro", "titulo": str(exc)}]


# ── Funções de exibição ────────────────────────────────────────────────────────

def show_cadastral(d: dict):
    console.print(Panel("[bold]DADOS CADASTRAIS[/bold]", style="cyan", expand=False))

    sit = d.get("descricao_situacao_cadastral", "")
    sit_color = "green" if sit.upper() == "ATIVA" else "red"

    endereco = " ".join(filter(None, [
        d.get("descricao_tipo_de_logradouro", ""),
        d.get("logradouro", ""),
        d.get("numero", ""),
        d.get("complemento", "") or "",
        "—",
        d.get("bairro", ""),
        "—",
        d.get("municipio", "") + "/" + d.get("uf", ""),
        "CEP",
        d.get("cep", ""),
    ]))

    fone = " / ".join(filter(None, [d.get("ddd_telefone_1", ""), d.get("ddd_telefone_2", "")]))

    linhas = [
        ("Razão Social",       d.get("razao_social", "—")),
        ("Nome Fantasia",      d.get("nome_fantasia", "—") or "—"),
        ("CNPJ",               fmt_cnpj(d.get("cnpj", ""))),
        ("Situação",           f"[{sit_color}]{sit}[/{sit_color}]"),
        ("Data Situação",      d.get("data_situacao_cadastral", "—") or "—"),
        ("Motivo",             d.get("descricao_motivo_situacao_cadastral", "—") or "—"),
        ("Natureza Jurídica",  d.get("natureza_juridica", "—")),
        ("Porte",              d.get("porte", "—")),
        ("Capital Social",     fmt_brl(d.get("capital_social", 0))),
        ("Matriz / Filial",    d.get("descricao_identificador_matriz_filial", "—")),
        ("Data Abertura",      d.get("data_inicio_atividade", "—")),
        ("Regime Tributário",  str(d.get("regime_tributario", "—"))),
        ("Simples Nacional",   "✓ Sim" if d.get("opcao_pelo_simples") else "✗ Não"),
        ("MEI",                "✓ Sim" if d.get("opcao_pelo_mei") else "✗ Não"),
        ("CNAE Principal",     f"{d.get('cnae_fiscal', '')} — {d.get('cnae_fiscal_descricao', '—')}"),
        ("Endereço",           endereco),
        ("Telefone",           fone or "—"),
        ("E-mail",             d.get("email", "—") or "—"),
    ]

    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column(style="bold dim", width=22)
    t.add_column()
    for campo, valor in linhas:
        t.add_row(campo, valor)
    console.print(t)


def show_cnaes(d: dict):
    cnaes = d.get("cnaes_secundarios", [])
    if not cnaes:
        return
    console.print(Panel(f"[bold]CNAEs SECUNDÁRIOS ({len(cnaes)})[/bold]", style="cyan", expand=False))
    t = Table(box=box.SIMPLE, show_header=True)
    t.add_column("Código", width=10)
    t.add_column("Descrição")
    for c in cnaes:
        t.add_row(str(c.get("codigo", "")), c.get("descricao", ""))
    console.print(t)


def show_socios(d: dict):
    socios = d.get("qsa", [])
    console.print(Panel(f"[bold]QUADRO SOCIETÁRIO — {len(socios)} membro(s)[/bold]", style="cyan", expand=False))
    if not socios:
        console.print("  [dim]Nenhum sócio informado[/dim]\n")
        return
    t = Table(box=box.SIMPLE, show_header=True)
    t.add_column("Nome", style="bold")
    t.add_column("Qualificação")
    t.add_column("CPF / CNPJ do Sócio")
    t.add_column("Faixa Etária")
    t.add_column("Data Entrada")
    for s in socios:
        t.add_row(
            s.get("nome_socio", "—"),
            s.get("qualificacao_socio", "—"),
            s.get("cnpj_cpf_do_socio", "—"),
            s.get("faixa_etaria", "—") or "—",
            s.get("data_entrada_sociedade", "—") or "—",
        )
    console.print(t)


def show_pgfn(resultado: dict):
    status = resultado.get("status", "—")
    color = "green" if "REGULAR" in (status or "").upper() else "red"
    devedores = resultado.get("devedores", [])

    console.print(Panel("[bold]PGFN — DÍVIDA ATIVA DA UNIÃO[/bold]", style="cyan", expand=False))
    console.print(f"  [{color}]{status}[/{color}]\n")

    if devedores:
        t = Table(box=box.SIMPLE, show_header=False)
        n_cols = max(len(r) for r in devedores)
        for _ in range(n_cols):
            t.add_column()
        for row in devedores:
            t.add_row(*[str(c) for c in row])
        console.print(t)



def show_news(noticias: list, nome: str):
    console.print(Panel(f"[bold]NOTÍCIAS NEGATIVAS — {nome[:50].upper()}[/bold]", style="cyan", expand=False))
    if not noticias:
        console.print("  [green]✓ Nenhuma notícia negativa encontrada[/green]\n")
        return
    t = Table(box=box.SIMPLE, show_header=True)
    t.add_column("Data", width=12, style="dim")
    t.add_column("Fonte", width=22)
    t.add_column("Título")
    for n in noticias:
        t.add_row(n["data"], n["fonte"], n["titulo"])
    console.print(t)
    console.print("  [dim]Verifique os links originais para confirmar o teor das notícias.[/dim]\n")


# ── Main ───────────────────────────────────────────────────────────────────────

async def main():
    if len(sys.argv) < 2:
        console.print("[bold red]Uso:[/bold red] python consulta_cnpj.py [CNPJ]")
        console.print("  Ex: python consulta_cnpj.py 33.000.167/0001-01")
        sys.exit(1)

    cnpj = clean_cnpj(sys.argv[1])
    if len(cnpj) != 14:
        console.print(f"[red]CNPJ inválido:[/red] {sys.argv[1]}")
        sys.exit(1)

    console.rule(f"[bold cyan]ANÁLISE DE CRÉDITO — {fmt_cnpj(cnpj)}[/bold cyan]")

    # 1. Dados cadastrais + sócios
    with console.status("[cyan]Consultando Receita Federal (Brasil API)...[/cyan]"):
        dados = fetch_cnpj(cnpj)
    nome = dados.get("razao_social") or cnpj

    show_cadastral(dados)
    show_cnaes(dados)
    show_socios(dados)

    # 2. PGFN
    console.print("\n[yellow]Abrindo browser para consulta PGFN...[/yellow]")
    try:
        pgfn = await fetch_pgfn(cnpj)
        show_pgfn(pgfn)
    except Exception as exc:
        console.print(Panel(
            f"[red]Erro:[/red] {exc}\n"
            "Consulte manualmente: [link]https://www.listadevedores.pgfn.gov.br/[/link]",
            title="[bold]PGFN[/bold]",
            border_style="red",
            expand=False,
        ))

    # 3. Notícias
    with console.status(f"[cyan]Buscando notícias sobre {nome[:40]}...[/cyan]"):
        noticias = fetch_news(nome)
    show_news(noticias, nome)

    console.rule("[dim]Fim da consulta[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
