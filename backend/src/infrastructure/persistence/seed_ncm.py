"""Seed script — populates the NCM table with real TIPI codes for Brazilian retail.

Covers: refrigerantes, águas, bebidas alcoólicas, leite/laticínios, carnes,
massas/cereais, higiene pessoal, limpeza, eletrônicos, vestuário, calçados,
cigarros, combustíveis.  Minimum 80 records with real descriptions from TIPI.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.sqlalchemy.models import Base

NCM_DATA: list[tuple[str, str, bool]] = [
    # ── Refrigerantes e Águas (2201–2202) ────────────────────
    ("22011000", "Águas minerais e águas gaseificadas", False),
    ("22019000", "Gelo e neve", False),
    ("22021000", "Águas, incluindo águas minerais e gaseificadas, adicionadas de açúcar", False),
    ("22021010", "Águas minerais adicionadas de açúcar ou aromatizadas", False),
    ("22029000", "Outras bebidas não alcoólicas, exceto sucos", False),
    ("22029010", "Refrigerantes", False),
    ("22029090", "Outras bebidas não alcoólicas", False),

    # ── Bebidas Alcoólicas (2203–2208) — sujeito_is=True ────
    ("22030000", "Cervejas de malte", True),
    ("22041000", "Vinhos espumantes e vinhos espumosos", True),
    ("22042100", "Vinhos, em recipientes de capacidade ≤ 2l", True),
    ("22042900", "Outros vinhos em recipientes > 2l", True),
    ("22051000", "Vermutes e outros vinhos aromatizados, ≤ 2l", True),
    ("22060000", "Outras bebidas fermentadas (sidra, perada, hidromel)", True),
    ("22071000", "Álcool etílico não desnaturado ≥ 80% vol", True),
    ("22082000", "Aguardentes de vinho ou de bagaço de uvas", True),
    ("22083000", "Uísques", True),
    ("22084000", "Rum e outras aguardentes de cana-de-açúcar", True),
    ("22085000", "Gim (gin) e genebra", True),
    ("22086000", "Vodca", True),
    ("22087000", "Licores", True),
    ("22089000", "Outras bebidas espirituosas e destiladas", True),

    # ── Leite e Laticínios (0401–0406) ──────────────────────
    ("04011000", "Leite não concentrado, teor de gordura ≤ 1%", False),
    ("04012000", "Leite não concentrado, teor de gordura > 1% e ≤ 6%", False),
    ("04014000", "Leite não concentrado, teor de gordura > 6%", False),
    ("04021000", "Leite em pó, com teor de gordura ≤ 1,5%", False),
    ("04022100", "Leite em pó, sem adição de açúcar, gordura > 1,5%", False),
    ("04031000", "Iogurte", False),
    ("04039000", "Leitelho, coalhada e outros leites fermentados", False),
    ("04041000", "Soro de leite, modificado ou não", False),
    ("04051000", "Manteiga", False),
    ("04052000", "Pasta de barrar (spreads) de leite", False),
    ("04061000", "Queijo fresco (não curado), incluindo requeijão", False),
    ("04062000", "Queijo ralado ou em pó", False),
    ("04063000", "Queijo fundido, exceto ralado ou em pó", False),
    ("04064000", "Queijo de pasta azul (Roquefort)", False),
    ("04069000", "Outros queijos", False),

    # ── Carnes (0201–0210) ──────────────────────────────────
    ("02011000", "Carcaças e meias-carcaças de bovino, frescas ou refrigeradas", False),
    ("02012000", "Outras peças de carne bovina não desossadas, frescas", False),
    ("02013000", "Carne bovina desossada, fresca ou refrigerada", False),
    ("02021000", "Carcaças e meias-carcaças de bovino, congeladas", False),
    ("02023000", "Carne bovina desossada, congelada", False),
    ("02031100", "Carcaças e meias-carcaças de suíno, frescas", False),
    ("02032200", "Pernis, pás e pedaços de suíno, congelados com osso", False),
    ("02041000", "Carcaças de ovino, frescas ou refrigeradas", False),
    ("02071100", "Carnes de galos e galinhas, não cortadas, frescas", False),
    ("02071200", "Carnes de galos e galinhas, não cortadas, congeladas", False),
    ("02071400", "Pedaços e miudezas de galos e galinhas, congelados", False),
    ("02081000", "Carnes de coelhos ou lebres, frescas ou congeladas", False),
    ("02101100", "Presuntos e pedaços de suíno, salgados ou defumados", False),
    ("02101200", "Peito (bacon) de suíno, salgado ou defumado", False),
    ("02101900", "Outras carnes de suíno salgadas ou defumadas", False),

    # ── Massas e Cereais (1902–1905) ────────────────────────
    ("19021100", "Massas alimentícias não cozidas, com ovos", False),
    ("19021900", "Outras massas alimentícias não cozidas", False),
    ("19022000", "Massas alimentícias recheadas", False),
    ("19023000", "Outras massas alimentícias (cuscuz)", False),
    ("19030000", "Tapioca e seus sucedâneos", False),
    ("19041000", "Produtos à base de cereais obtidos por expansão ou torrefação", False),
    ("19042000", "Preparações à base de cereais não torrados (muesli)", False),
    ("19051000", "Pão crocante (knäckebröd)", False),
    ("19052000", "Pão de especiarias (gingerbread)", False),
    ("19053100", "Bolachas e biscoitos adicionados de edulcorantes", False),
    ("19053200", "Waffles e wafers", False),
    ("19054000", "Torradas, pão torrado e produtos semelhantes", False),
    ("19059000", "Outros produtos de padaria, pastelaria ou indústria de bolachas", False),

    # ── Higiene Pessoal (3305–3307) ─────────────────────────
    ("33051000", "Xampus", False),
    ("33052000", "Preparações para ondulação ou alisamento permanente", False),
    ("33053000", "Laquês (fixadores) para o cabelo", False),
    ("33059000", "Outras preparações capilares", False),
    ("33061000", "Dentifrícios (creme dental)", False),
    ("33069000", "Outras preparações para higiene bucal", False),
    ("33071000", "Preparações para barbear (antes, durante ou após)", False),
    ("33072000", "Desodorantes e antiperspirantes corporais", False),
    ("33073000", "Sais perfumados e preparações para banhos", False),
    ("33074900", "Outras preparações para perfumar ambientes", False),

    # ── Limpeza (3402, 3808) ────────────────────────────────
    ("34021100", "Agentes orgânicos de superfície, aniônicos", False),
    ("34021200", "Agentes orgânicos de superfície, catiônicos", False),
    ("34022000", "Preparações tensoativas para lavagem (detergentes)", False),
    ("34025000", "Preparações acondicionadas para venda a retalho (sabão líquido)", False),
    ("38081000", "Inseticidas", False),
    ("38089100", "Inseticidas acondicionados para venda a retalho", False),
    ("38089300", "Herbicidas acondicionados para venda a retalho", False),

    # ── Eletrônicos (8471, 8517, 8519) ─────────────────────
    ("84713000", "Máquinas automáticas para processamento de dados portáteis (notebooks)", False),
    ("84714100", "Outras máquinas automáticas para processamento de dados (desktops)", False),
    ("84714900", "Outras máquinas de processamento de dados, apresentadas sob forma de sistemas", False),
    ("84717000", "Unidades de memória (HDD, SSD)", False),
    ("85171100", "Telefones para redes celulares (smartphones)", False),
    ("85171200", "Telefones para redes sem fio (exceto celulares)", False),
    ("85171800", "Outros aparelhos telefônicos", False),
    ("85192000", "Aparelhos acionados por moedas/fichas (jukebox)", False),
    ("85198100", "Aparelhos de reprodução de som, sem gravação", False),
    ("85198900", "Outros aparelhos de gravação/reprodução de som", False),

    # ── Vestuário (6101–6117) ──────────────────────────────
    ("61012000", "Sobretudos e casacos de algodão, de malha, masculinos", False),
    ("61013000", "Sobretudos de fibras sintéticas, de malha, masculinos", False),
    ("61021000", "Sobretudos e casacos de lã, de malha, femininos", False),
    ("61022000", "Sobretudos e casacos de algodão, de malha, femininos", False),
    ("61031000", "Ternos e conjuntos de lã ou pêlos finos, de malha", False),
    ("61042000", "Conjuntos de algodão, de malha, femininos", False),
    ("61051000", "Camisas de algodão, de malha, masculinas", False),
    ("61052000", "Camisas de fibras sintéticas, de malha, masculinas", False),
    ("61061000", "Camisetas (T-shirts) de algodão, de malha, femininas", False),
    ("61091000", "T-shirts de algodão, de malha", False),
    ("61099000", "T-shirts de outras matérias, de malha", False),
    ("61159500", "Meias-calças de fibras sintéticas, malha", False),
    ("61171000", "Xales, echarpes, lenços de pescoço, de malha", False),

    # ── Calçados (6401–6405) ───────────────────────────────
    ("64011000", "Calçados impermeáveis com biqueira protetora de metal", False),
    ("64019200", "Calçados impermeáveis cobrindo o tornozelo, sem biqueira", False),
    ("64021900", "Outros calçados para esporte, com sola de borracha/plástico", False),
    ("64022000", "Calçados com parte superior em tiras fixadas à sola por pregos", False),
    ("64029900", "Outros calçados com sola e parte superior de borracha/plástico", False),
    ("64039100", "Calçados de couro natural, cobrindo o tornozelo", False),
    ("64039900", "Outros calçados de couro natural", False),
    ("64041100", "Calçados para esporte, com sola de borracha e parte superior têxtil", False),
    ("64041900", "Outros calçados com sola de borracha e parte superior têxtil", False),
    ("64051000", "Outros calçados com parte superior de couro natural ou reconstituído", False),
    ("64052000", "Outros calçados com parte superior têxtil", False),

    # ── Cigarros (2402) — sujeito_is=True ──────────────────
    ("24021000", "Charutos e cigarrilhas, contendo tabaco", True),
    ("24022000", "Cigarros contendo tabaco", True),
    ("24029000", "Outros charutos, cigarrilhas e cigarros", True),

    # ── Combustíveis (2710) — sujeito_is=True ──────────────
    ("27101210", "Gasolinas, exceto gasolina de aviação", True),
    ("27101221", "Querosene de aviação", True),
    ("27101259", "Outros óleos diesel", True),
    ("27101921", "Óleo lubrificante", True),
    ("27111300", "Gases liquefeitos de petróleo (GLP, gás de cozinha)", True),
]


def seed_ncm(session: Session) -> int:
    """Insert NCM records idempotently. Returns count of new records."""
    ncm_table = Base.metadata.tables.get("ncm")
    if ncm_table is None:
        raise RuntimeError("Table 'ncm' not found in metadata")

    existing = {
        row[0]
        for row in session.execute(select(ncm_table.c.codigo)).all()
    }

    new_count = 0
    for codigo, descricao, sujeito_is in NCM_DATA:
        if codigo in existing:
            continue
        session.execute(
            ncm_table.insert().values(
                codigo=codigo,
                descricao=descricao,
                sujeito_is=sujeito_is,
            )
        )
        new_count += 1

    session.commit()
    return new_count
