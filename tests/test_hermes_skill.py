from hermes_skill.pothi_skill import PothiParivaarSkill


def test_hermes_skill_initialization():
    skill = PothiParivaarSkill(base_url="http://localhost:8000")
    assert skill.base_url == "http://localhost:8000"


def test_hermes_skill_handles_unreachable_server():
    # Calling an unreachable port should return a graceful error dict without crashing
    skill = PothiParivaarSkill(base_url="http://127.0.0.1:59999")
    res = skill.get_status()
    assert "error" in res
    assert "Failed to connect" in res["error"]
