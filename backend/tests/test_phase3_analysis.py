import os
import tempfile
import textwrap
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_code_analysis_returns_entities_imports_and_calls() -> None:
    payload = {
        "language": "python",
        "source": textwrap.dedent('''
            import os
            from pkg import util


            def foo(x):
                return bar(x)


            class Service:
                def run(self):
                    return foo(1)


            def bar(x):
                return x + 1
        '''),
        "file_path": "example.py",
    }

    response = client.post("/api/analysis/run", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["language"] == "python"
    assert body["file_path"] == "example.py"
    assert len(body["entities"]) >= 4
    assert any(entity["name"] == "foo" for entity in body["entities"])
    assert any(entity["name"] == "Service" for entity in body["entities"])
    assert any(item["module"] == "pkg" for item in body["imports"])
    assert any(call["callee"] == "foo" for call in body["calls"])
    assert any(edge["source"] == "foo" and edge["target"] == "bar" for edge in body["dependency_graph"])


def test_full_repository_analysis_flow() -> None:
    # 1. Create a repository
    repo_resp = client.post(
        "/api/repositories",
        json={
            "name": "sample-python-repo",
            "url": "https://github.com/acme/sample-python-repo",
            "provider": "github",
            "default_branch": "main",
        },
    )
    assert repo_resp.status_code == 200
    repo_id = repo_resp.json()["id"]

    # 2. Create temporary directory with source files
    with tempfile.TemporaryDirectory() as tmpdir:
        auth_py = os.path.join(tmpdir, "auth.py")
        with open(auth_py, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent('''
                def validate_token(token):
                    return True
            ''').strip())

        payment_py = os.path.join(tmpdir, "payment.py")
        with open(payment_py, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent('''
                from auth import validate_token

                class PaymentService:
                    def charge(self, amount):
                        validate_token("abc")
                        return amount
            ''').strip())

        # 3. Trigger analysis
        analyze_resp = client.post(
            f"/api/code-analysis/repositories/{repo_id}/analyze",
            json={"path": tmpdir},
        )
        assert analyze_resp.status_code == 200, analyze_resp.text
        run_data = analyze_resp.json()
        assert run_data["repository_id"] == repo_id
        assert run_data["status"] in ("completed", "partial")
        assert run_data["files_discovered"] == 2
        assert run_data["entities_found"] >= 4
        assert run_data["relationships_found"] >= 4

        # 4. Fetch analyzed files
        files_resp = client.get(f"/api/code-analysis/repositories/{repo_id}/files")
        assert files_resp.status_code == 200
        files = files_resp.json()
        assert len(files) == 2

        # 5. Fetch code entities with filtering
        entities_resp = client.get(f"/api/code-analysis/repositories/{repo_id}/entities?entity_type=CLASS")
        assert entities_resp.status_code == 200
        classes = entities_resp.json()
        assert any(c["name"] == "PaymentService" for c in classes)

        # 6. Fetch relationships
        rels_resp = client.get(f"/api/code-analysis/repositories/{repo_id}/relationships")
        assert rels_resp.status_code == 200
        rels = rels_resp.json()
        assert any(r["relationship_type"] == "IMPORTS" for r in rels)

        # 7. Fetch dependency graph
        graph_resp = client.get(f"/api/code-analysis/repositories/{repo_id}/graph")
        assert graph_resp.status_code == 200
        graph = graph_resp.json()
        assert "nodes" in graph and "edges" in graph
        assert len(graph["nodes"]) >= 4

        # 8. Check run details
        run_id = run_data["id"]
        run_detail = client.get(f"/api/code-analysis/runs/{run_id}")
        assert run_detail.status_code == 200
        assert run_detail.json()["id"] == run_id


def test_reanalysis_replaces_old_records() -> None:
    repo_resp = client.post(
        "/api/repositories",
        json={"name": "reanalysis-repo", "provider": "github"},
    )
    repo_id = repo_resp.json()["id"]

    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "v1.py")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("def initial(): pass\n")

        # Run 1
        r1 = client.post(f"/api/code-analysis/repositories/{repo_id}/analyze", json={"path": tmpdir})
        assert r1.status_code == 200

        # Update file
        with open(f1, "w", encoding="utf-8") as f:
            f.write("def updated(): pass\ndef new_fn(): pass\n")

        # Run 2 (Re-analysis)
        r2 = client.post(f"/api/code-analysis/repositories/{repo_id}/analyze", json={"path": tmpdir})
        assert r2.status_code == 200

        entities_resp = client.get(f"/api/code-analysis/repositories/{repo_id}/entities?entity_type=FUNCTION")
        entities = entities_resp.json()
        names = [e["name"] for e in entities]
        assert "updated" in names
        assert "new_fn" in names
        assert "initial" not in names
