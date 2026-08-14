from scripts.secret_scan import DEFAULT_PATHS, Finding, format_finding, scan_text


def test_secret_scan_allows_benign_key_documentation():
    findings = scan_text("README.md", "API key is stored in the credential manager.")

    assert findings == []


def test_secret_scan_flags_private_key_material():
    findings = scan_text("secret.txt", "-----BEGIN PRIVATE KEY-----")

    assert findings
    assert findings[0].kind == "private_key"


def test_secret_scan_flags_todo_markers():
    findings = scan_text("src/example.py", "# TODO: finish this")

    assert findings
    assert findings[0].kind == "todo_marker"

def test_format_finding_is_ascii_safe_for_windows_console():
    finding = Finding(path="README.md", kind="todo_marker", line_number=1, line="含中文的占位标记")

    rendered = format_finding(finding)

    assert rendered.isascii()
    assert "README.md:1:todo_marker:" in rendered

def test_default_scan_covers_release_configuration_and_submission_metadata():
    required = {"Dockerfile", "config", ".github", ".gitlab-ci.yml", "submission.jsonc", "SPEC.md"}

    assert required.issubset(DEFAULT_PATHS)
