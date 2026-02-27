"""Tests for declarative queries: filters, sort, and whitelist validation."""

from __future__ import annotations


class TestFilters:
    """Filter by allowed fields."""

    def _seed(self, client, headers, uf, cfop="5102"):
        resp = client.post(
            "/entities/fiscal_rules",
            json={
                "id_grupo_tributario": "grp-q",
                "id_natureza_operacao": "nat-q",
                "cfop": cfop,
                "uf_origem": uf,
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["id"]

    def test_filter_eq(self, client, auth_headers):
        id_sp = self._seed(client, auth_headers, "SP")
        id_rj = self._seed(client, auth_headers, "RJ")

        resp = client.get(
            "/entities/fiscal_rules?filter[uf_origem]=SP",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["uf_origem"] == "SP" for i in items)
        assert any(i["id"] == id_sp for i in items)

        # Cleanup
        client.delete(f"/entities/fiscal_rules/{id_sp}", headers=auth_headers)
        client.delete(f"/entities/fiscal_rules/{id_rj}", headers=auth_headers)

    def test_multiple_filters(self, client, auth_headers):
        id1 = self._seed(client, auth_headers, "SP", "5102")
        id2 = self._seed(client, auth_headers, "SP", "6102")

        resp = client.get(
            "/entities/fiscal_rules?filter[uf_origem]=SP&filter[cfop]=5102",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert item["uf_origem"] == "SP"
            assert item["cfop"] == "5102"

        # Cleanup
        client.delete(f"/entities/fiscal_rules/{id1}", headers=auth_headers)
        client.delete(f"/entities/fiscal_rules/{id2}", headers=auth_headers)

    def test_filter_returns_correct_total(self, client, auth_headers):
        id_sp = self._seed(client, auth_headers, "SP")
        id_mg = self._seed(client, auth_headers, "MG")

        resp = client.get(
            "/entities/fiscal_rules?filter[uf_origem]=MG",
            headers=auth_headers,
        )
        body = resp.json()
        assert body["total"] >= 1
        assert all(i["uf_origem"] == "MG" for i in body["items"])

        # Cleanup
        client.delete(f"/entities/fiscal_rules/{id_sp}", headers=auth_headers)
        client.delete(f"/entities/fiscal_rules/{id_mg}", headers=auth_headers)


class TestFilterWhitelist:
    """Non-filterable fields return 400."""

    def test_disallowed_field_returns_400(self, client, auth_headers):
        resp = client.get(
            "/entities/fiscal_rules?filter[icms_cst]=00",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        body = resp.json()
        assert "not filterable" in body["error"]["message"]

    def test_allowed_field_passes(self, client, auth_headers):
        resp = client.get(
            "/entities/fiscal_rules?filter[uf_origem]=SP",
            headers=auth_headers,
        )
        assert resp.status_code == 200


class TestSort:
    """Sort by field ascending and descending."""

    def test_sort_ascending(self, client, auth_headers):
        resp = client.get(
            "/entities/fiscal_rules?sort=cfop",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_sort_descending(self, client, auth_headers):
        resp = client.get(
            "/entities/fiscal_rules?sort=-cfop",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_no_filter_no_sort_works(self, client, auth_headers):
        resp = client.get(
            "/entities/fiscal_rules",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "items" in resp.json()
        assert "total" in resp.json()
