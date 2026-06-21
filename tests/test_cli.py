from typer.testing import CliRunner

from qdlake.cli import app


runner = CliRunner()


def test_cli_help_runs():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "ingest-prices" in result.output
    assert "query-prices" in result.output