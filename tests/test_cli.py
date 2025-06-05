"""
Test CLI functionality.
"""

from unittest.mock import patch

from click.testing import CliRunner

from rez_proxy.cli import main


def test_cli_basic():
    """Test basic CLI functionality."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Rez Proxy" in result.output


@patch("rez_proxy.cli.detect_rez_installation")
def test_cli_rez_detection_failure(mock_detect):
    """Test CLI behavior when Rez detection fails."""
    mock_detect.side_effect = RuntimeError("Rez not found")

    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 1
    assert "Rez detection failed: Rez not found" in result.output
    assert "Please ensure Rez is properly installed" in result.output


@patch("rez_proxy.cli.uvicorn.run")
@patch("rez_proxy.cli.detect_rez_installation")
def test_cli_successful_start(mock_detect, mock_uvicorn, mock_rez_info):
    """Test CLI successful startup (without actually starting server)."""
    mock_detect.return_value = mock_rez_info
    mock_uvicorn.return_value = None  # Don't actually start server

    runner = CliRunner()
    result = runner.invoke(main, ["--host", "127.0.0.1", "--port", "8080"])

    assert result.exit_code == 0
    assert "Found Rez" in result.output
    assert "Starting Rez Proxy on http://127.0.0.1:8080" in result.output
    mock_uvicorn.assert_called_once()
