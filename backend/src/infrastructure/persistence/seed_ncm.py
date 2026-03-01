"""Seed script — populates the NCM table from the full TIPI catalog.

Primary source: CSV from GitHub (jansenfelipe/ncm), containing ~14 000
real NCM codes with descriptions.  Falls back to a hardcoded subset
if the download fails (timeout, network error, etc.).
"""

from __future__ import annotations

import logging

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.sqlalchemy.models import Base

logger = logging.getLogger(__name__)

_NCM_CSV_URL = (
    "https://raw.githubusercontent.com/jansenfelipe/ncm/master/ncm.csv"
)
_DOWNLOAD_TIMEOUT = 30  # seconds


# ── Fallback hardcoded subset (common retail NCMs) ──────────────────
# Used when the CSV download fails.  ~80 codes covering beverages,
# dairy, meat, bakery, hygiene, cleaning, electronics, clothing, etc.
NCM_FALLBACK_DATA: list[tuple[str, str]] = [
    # Refrigerantes e Águas
    ("22011000", "Águas minerais e águas gaseificadas"),
    ("22019000", "Gelo e neve"),
    ("22021000", "Águas, incluindo águas minerais e gaseificadas, adicionadas de açúcar"),
    ("22029000", "Outras bebidas não alcoólicas, exceto sucos"),
    ("22029010", "Refrigerantes"),
    # Bebidas Alcoólicas
    ("22030000", "Cervejas de malte"),
    ("22041000", "Vinhos espumantes e vinhos espumosos"),
    ("22042100", "Vinhos, em recipientes de capacidade ≤ 2l"),
    ("22060000", "Outras bebidas fermentadas (sidra, perada, hidromel)"),
    ("22071000", "Álcool etílico não desnaturado ≥ 80% vol"),
    ("22082000", "Aguardentes de vinho ou de bagaço de uvas"),
    ("22083000", "Uísques"),
    ("22084000", "Rum e outras aguardentes de cana-de-açúcar"),
    ("22085000", "Gim (gin) e genebra"),
    ("22086000", "Vodca"),
    ("22087000", "Licores"),
    ("22089000", "Outras bebidas espirituosas e destiladas"),
    # Leite e Laticínios
    ("04011000", "Leite não concentrado, teor de gordura ≤ 1%"),
    ("04012000", "Leite não concentrado, teor de gordura > 1% e ≤ 6%"),
    ("04021000", "Leite em pó, com teor de gordura ≤ 1,5%"),
    ("04031000", "Iogurte"),
    ("04051000", "Manteiga"),
    ("04061000", "Queijo fresco (não curado), incluindo requeijão"),
    ("04069000", "Outros queijos"),
    # Carnes
    ("02011000", "Carcaças e meias-carcaças de bovino, frescas ou refrigeradas"),
    ("02013000", "Carne bovina desossada, fresca ou refrigerada"),
    ("02023000", "Carne bovina desossada, congelada"),
    ("02071100", "Carnes de galos e galinhas, não cortadas, frescas"),
    ("02071200", "Carnes de galos e galinhas, não cortadas, congeladas"),
    ("02101100", "Presuntos e pedaços de suíno, salgados ou defumados"),
    ("02101200", "Peito (bacon) de suíno, salgado ou defumado"),
    # Massas e Cereais
    ("19021100", "Massas alimentícias não cozidas, com ovos"),
    ("19021900", "Outras massas alimentícias não cozidas"),
    ("19041000", "Produtos à base de cereais obtidos por expansão ou torrefação"),
    ("19051000", "Pão crocante (knäckebröd)"),
    ("19053100", "Bolachas e biscoitos adicionados de edulcorantes"),
    ("19059000", "Outros produtos de padaria, pastelaria ou indústria de bolachas"),
    # Arroz e Grãos
    ("10063021", "Arroz semibranqueado ou branqueado, polido ou brunido"),
    ("07131090", "Ervilhas secas"),
    ("07132090", "Grão-de-bico"),
    ("07133390", "Feijão comum"),
    # Açúcar e Doces
    ("17019900", "Outros açúcares de cana ou de beterraba"),
    ("17049090", "Outros produtos de confeitaria"),
    ("18063200", "Chocolate em tabletes ou barras, não recheado"),
    # Óleos e Gorduras
    ("15079011", "Óleo de soja refinado, em recipientes"),
    ("15171000", "Margarina"),
    # Café e Chá
    ("09012100", "Café torrado, não descafeinado"),
    ("09012200", "Café torrado, descafeinado"),
    ("09024000", "Chá preto e chá parcialmente fermentado"),
    # Sucos
    ("20091100", "Suco de laranja, congelado, não fermentado"),
    ("20091900", "Outros sucos de laranja"),
    # Higiene Pessoal
    ("33051000", "Xampus"),
    ("33059000", "Outras preparações capilares"),
    ("33061000", "Dentifrícios (creme dental)"),
    ("33072000", "Desodorantes e antiperspirantes corporais"),
    ("33030000", "Perfumes e águas de colônia"),
    ("34011100", "Sabonetes de toucador"),
    # Limpeza
    ("34022000", "Preparações tensoativas para lavagem (detergentes)"),
    ("34025000", "Preparações acondicionadas para venda a retalho (sabão líquido)"),
    ("38081000", "Inseticidas"),
    # Papel e Absorventes
    ("48181000", "Papel higiênico"),
    ("48182000", "Lenços e toalhas de papel"),
    ("96190000", "Absorventes e tampões higiênicos, fraldas"),
    # Eletrônicos
    ("84713000", "Máquinas portáteis para processamento de dados (notebooks)"),
    ("85171100", "Telefones para redes celulares (smartphones)"),
    ("85287200", "Aparelhos receptores de televisão, em cores"),
    # Vestuário
    ("61091000", "T-shirts de algodão, de malha"),
    ("61051000", "Camisas de algodão, de malha, masculinas"),
    ("61046200", "Calças de algodão, de malha, femininas"),
    # Calçados
    ("64041100", "Calçados para esporte, com sola de borracha e parte superior têxtil"),
    ("64039100", "Calçados de couro natural, cobrindo o tornozelo"),
    ("64029900", "Outros calçados com sola e parte superior de borracha/plástico"),
    # Cigarros
    ("24022000", "Cigarros contendo tabaco"),
    # Combustíveis
    ("27101210", "Gasolinas, exceto gasolina de aviação"),
    ("27101259", "Outros óleos diesel"),
    ("27111300", "Gases liquefeitos de petróleo (GLP, gás de cozinha)"),
    # Medicamentos
    ("30049099", "Outros medicamentos para venda a retalho"),
    # Embalagens
    ("39241000", "Serviços de mesa e artigos de cozinha, de plástico"),
    ("76129000", "Recipientes de alumínio (latas)"),
]


def _download_ncm_csv() -> list[tuple[str, str]]:
    """Download the full NCM CSV and return as (codigo, descricao) pairs."""
    try:
        resp = httpx.get(_NCM_CSV_URL, timeout=_DOWNLOAD_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.warning("Failed to download NCM CSV: %s", exc)
        return []

    records: list[tuple[str, str]] = []
    for line in resp.text.splitlines():
        line = line.strip()
        if not line or ";" not in line:
            continue
        parts = line.split(";", 1)
        if len(parts) != 2:
            continue
        codigo_raw = parts[0].strip().strip('"')
        descricao = parts[1].strip().strip('"')

        # CSV has 7-digit codes; pad to 8 digits (standard NCM format)
        if len(codigo_raw) == 7:
            codigo_raw += "0"
        # Skip non-numeric or wrong-length codes
        if not codigo_raw.isdigit() or len(codigo_raw) != 8:
            continue

        records.append((codigo_raw, descricao))

    return records


def seed_ncm(session: Session) -> int:
    """Insert NCM records idempotently. Returns count of new records.

    Tries to download the full TIPI catalog (~14 000 codes) from GitHub.
    Falls back to a hardcoded subset if the download fails.
    """
    ncm_table = Base.metadata.tables.get("ncm")
    if ncm_table is None:
        raise RuntimeError("Table 'ncm' not found in metadata")

    # Check how many records already exist
    existing_count = session.execute(
        select(ncm_table.c.codigo)
    ).all()
    existing_codes = {row[0] for row in existing_count}

    # If we already have a large dataset (>1000), skip re-seeding
    if len(existing_codes) > 1000:
        logger.info(
            "NCM table already has %d records, skipping seed.",
            len(existing_codes),
        )
        return 0

    # Try downloading the full CSV
    records = _download_ncm_csv()
    source = "GitHub CSV"

    if not records:
        logger.info("Using fallback NCM data (%d records)", len(NCM_FALLBACK_DATA))
        records = NCM_FALLBACK_DATA
        source = "fallback"

    new_count = 0
    for codigo, descricao in records:
        if codigo in existing_codes:
            continue
        session.execute(
            ncm_table.insert().values(
                codigo=codigo,
                descricao=descricao,
                sujeito_is=False,
            )
        )
        existing_codes.add(codigo)
        new_count += 1

    if new_count:
        session.commit()
        logger.info(
            "Seeded %d NCM records from %s (total: %d)",
            new_count, source, len(existing_codes),
        )

    return new_count
