import pytest

from tyche_ai.job_search.cli import main


def test_fake_cli_runs_without_keys(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--fake", "Cari lowongan akuntan pajak di Surabaya seminggu terakhir"]) == 0

    output = capsys.readouterr().out
    assert "Tax Accountant" in output
    assert '"firecrawl_calls":1' in output
    assert "finance_accounting" in output


def test_fake_cli_rejects_gibberish(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--fake", "asdf asdf asdf"]) == 1
    assert "FAILED:" in capsys.readouterr().err
