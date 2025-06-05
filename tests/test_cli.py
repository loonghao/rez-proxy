"""
Test CLI functionality.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from rez_proxy.cli import main


@patch("rez_proxy.cli.detect_rez_installation")
@patch("rez_proxy.cli.uvicorn.run")
def test_cli_basic(mock_uvicorn, mock_detect, mock_rez_info):
    """Test basic CLI functionality."""
    mock_detect.return_value = mock_rez_info
    
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
    assert "Rez detection failed" in result.output
