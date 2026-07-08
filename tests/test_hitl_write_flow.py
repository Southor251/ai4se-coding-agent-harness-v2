from agent_harness.demos.hitl_write import DEMO_CONTENT, run_demo


def test_hitl_write_demo_requires_approval_before_writing(tmp_path):
    result = run_demo(workspace_root=tmp_path)

    assert result["status"] == "approved_and_written"
    assert result["request_status"] == "approved"
    assert result["file_existed_before_approval"] is False
    assert result["file_written"] is True
    assert result["halt_reason"] == "done"
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == DEMO_CONTENT


def test_hitl_write_demo_can_reload_persisted_request(tmp_path):
    store_path = tmp_path / "hitl" / "requests.json"
    workspace = tmp_path / "workspace"

    result = run_demo(workspace_root=workspace, hitl_store_path=store_path)

    assert result["status"] == "approved_and_written"
    assert result["request_status"] == "approved"
    assert store_path.exists()
    assert (workspace / "hello.txt").exists()
