import json

from langchain_core.messages import AIMessage

from app import llm as llm_mod
from tests.conftest import FakeLLM, login


def hcp_id(client, h, name):
    r = client.get("/api/v1/hcps", params={"q": name}, headers=h).json()
    return r["items"][0]["id"]


def test_auth_required_and_refresh(client):
    assert client.get("/api/v1/hcps").status_code == 401
    tok = client.post("/api/v1/auth/login", data={"username": "rep1@crm.dev", "password": "rep12345"}).json()
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]}).status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tok["access_token"]}).status_code == 401
    assert client.post("/api/v1/auth/login", data={"username": "rep1@crm.dev", "password": "wrong"}).status_code == 401


def test_reps_only_see_their_own_interactions_managers_see_all(client, rep1, rep2, manager):
    mine = client.get("/api/v1/interactions", params={"size": 100}, headers=rep1).json()
    theirs = client.get("/api/v1/interactions", params={"size": 100}, headers=rep2).json()
    everyone = client.get("/api/v1/interactions", params={"size": 100}, headers=manager).json()
    assert mine["total"] > 0 and theirs["total"] > 0
    assert mine["total"] + theirs["total"] == everyone["total"]
    foreign = theirs["items"][0]
    assert client.get(f"/api/v1/interactions/{foreign['id']}", headers=rep1).status_code == 404
    assert client.patch(f"/api/v1/interactions/{foreign['id']}", json={"notes": "x"}, headers=rep1).status_code == 404
    # a manager can read it but not rewrite a rep's record
    assert client.get(f"/api/v1/interactions/{foreign['id']}", headers=manager).status_code == 200
    assert client.patch(f"/api/v1/interactions/{foreign['id']}", json={"notes": "x"}, headers=manager).status_code == 403


def test_create_interaction_with_followup_and_summary(client, rep1):
    hid = hcp_id(client, rep1, "Verma")
    prod = client.get("/api/v1/products", headers=rep1).json()[0]["id"]
    r = client.post("/api/v1/interactions", headers=rep1, json={
        "hcp_id": hid, "type": "visit", "notes": "Great meeting", "sentiment": "positive", "product_ids": [prod],
        "next_steps": "Send trial data", "follow_up_days": 14})
    assert r.status_code == 201
    body = r.json()
    assert body["summary"].startswith("Visit with Dr. Anita Verma") and body["products"][0]["id"] == prod
    fus = client.get("/api/v1/followups", headers=rep1).json()
    assert any(f["title"] == "Send trial data" for f in fus)


def test_quick_log_parse_fallback_matches_doctor_product_and_followup(client, rep1):
    text = "Visited Dr. Verma at Lakeview today, she was very positive about CardioMax. Follow up in 2 weeks."
    d = client.post("/api/v1/interactions/parse", json={"text": text}, headers=rep1).json()
    assert d["used_llm"] is False
    assert d["doctor_name"] == "Verma" and d["hcp_id"] and d["product_names"] == ["CardioMax"]
    assert d["sentiment"] == "positive" and d["follow_up_days"] == 14


def test_hcp_filters_and_stats(client, rep1):
    r = client.get("/api/v1/hcps", params={"tier": "A", "specialty": "Cardiology"}, headers=rep1).json()
    assert r["total"] >= 2 and all(h["tier"] == "A" and h["specialty"] == "Cardiology" for h in r["items"])
    detail = client.get(f"/api/v1/hcps/{r['items'][0]['id']}", headers=rep1).json()
    assert {"timeline", "sentiment", "products", "followups"} <= set(detail)


def test_analytics_and_manager_only_team_view(client, rep1, manager):
    ov = client.get("/api/v1/analytics/overview", params={"days": 30}, headers=rep1).json()
    assert ov["interactions"] > 0 and len(ov["series"]) == 31
    risk = client.get("/api/v1/analytics/at-risk", headers=manager).json()
    assert risk and all(x["tier"] in "AB" for x in risk) and "suggestion" in risk[0]
    assert client.get("/api/v1/analytics/team", headers=rep1).status_code == 403
    team = client.get("/api/v1/analytics/team", headers=manager).json()
    assert {t["name"] for t in team} == {"Aarav Mehta", "Sneha Rao"}


def test_assistant_requires_llm(client, rep1):
    assert client.post("/api/v1/chat", json={"message": "hi"}, headers=rep1).status_code == 503


def _chat(client, headers, msg):
    with client.stream("POST", "/api/v1/chat", json={"message": msg}, headers=headers) as s:
        return [json.loads(line[6:]) for line in s.iter_lines() if line.startswith("data: ")]


def test_assistant_proposes_writes_and_nothing_is_saved_until_confirmed(client, rep1, rep2):
    call = AIMessage(content="", tool_calls=[{"name": "propose_log_interaction", "id": "t1", "args": {
        "hcp_name": "Dr. Verma", "type": "visit", "notes": "Discussed dosing", "products": ["CardioMax"], "sentiment": "positive",
        "next_steps": "Send brochure", "follow_up_days": 7}}])
    llm_mod.set_llm(FakeLLM([call, AIMessage(content="I've drafted that visit. Please confirm it.")]))
    before = client.get("/api/v1/interactions", headers=rep1).json()["total"]

    events = _chat(client, rep1, "Met Dr Verma today, positive about CardioMax")
    types = [e["type"] for e in events]
    assert "tool_call" in types and "tool_result" in types and "actions" in types and types[-1] == "done"
    assert any(e["type"] == "token" and "confirm" in e["text"] for e in events)
    action = next(e for e in events if e["type"] == "actions")["actions"][0]
    assert action["status"] == "pending" and action["payload"]["product_names"] == ["CardioMax"]
    assert client.get("/api/v1/interactions", headers=rep1).json()["total"] == before        # nothing saved yet

    assert client.post(f"/api/v1/chat/actions/{action['id']}/confirm", headers=rep2).status_code == 404  # not their action
    ok = client.post(f"/api/v1/chat/actions/{action['id']}/confirm", headers=rep1)
    assert ok.status_code == 200 and ok.json()["status"] == "confirmed"
    after = client.get("/api/v1/interactions", headers=rep1).json()
    assert after["total"] == before + 1 and after["items"][0]["source"] == "assistant"
    assert client.post(f"/api/v1/chat/actions/{action['id']}/confirm", headers=rep1).status_code == 409  # no double-apply
    assert [m["role"] for m in client.get("/api/v1/chat/history", headers=rep1).json()] == ["user", "assistant"]


def test_assistant_can_cancel_and_unknown_doctor_is_not_proposed(client, rep1):
    bad = AIMessage(content="", tool_calls=[{"name": "propose_followup", "id": "t1", "args": {"hcp_name": "Zzyzx Nobody", "title": "x"}}])
    llm_mod.set_llm(FakeLLM([bad, AIMessage(content="I couldn't find that doctor.")]))
    events = _chat(client, rep1, "remind me about Zzyzx")
    assert not any(e["type"] == "actions" for e in events)
    assert "No doctor matching" in next(e for e in events if e["type"] == "tool_result")["content"]

    ok = AIMessage(content="", tool_calls=[{"name": "propose_followup", "id": "t2", "args": {"hcp_name": "Verma", "title": "Call back", "due_in_days": 3}}])
    llm_mod.set_llm(FakeLLM([ok, AIMessage(content="Drafted.")]))
    aid = next(e for e in _chat(client, rep1, "remind me about Verma") if e["type"] == "actions")["actions"][0]["id"]
    assert client.post(f"/api/v1/chat/actions/{aid}/cancel", headers=rep1).json()["status"] == "cancelled"
    assert client.post(f"/api/v1/chat/actions/{aid}/confirm", headers=rep1).status_code == 409


def test_csv_export_is_scoped(client, rep1, manager):
    mine = client.get("/api/v1/interactions/export.csv", headers=rep1).text.strip().splitlines()
    allr = client.get("/api/v1/interactions/export.csv", headers=manager).text.strip().splitlines()
    assert mine[0].startswith("date,rep") and len(allr) > len(mine) > 1
