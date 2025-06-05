"""
Test shells router functionality.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


class TestShellsRouter:
    """Test shells router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @patch("rez.shells.get_shell_types")
    @patch("rez.shells.get_shell_class")
    def test_list_shells_success(self, mock_get_class, mock_get_types, client):
        """Test successful shells listing."""
        # Mock shell types
        mock_get_types.return_value = ["bash", "tcsh", "cmd", "powershell"]

        # Mock shell classes
        def mock_shell_class_factory(shell_name):
            mock_class = Mock()
            mock_class.name.return_value = shell_name
            mock_class.executable = shell_name
            mock_class.file_extension.return_value = (
                ".sh" if shell_name != "cmd" else ".bat"
            )
            mock_class.is_available.return_value = True
            mock_class.executable_filepath.return_value = f"/bin/{shell_name}"
            return mock_class

        mock_get_class.side_effect = mock_shell_class_factory

        response = client.get("/api/v1/shells")
        assert response.status_code == 200

        data = response.json()
        assert "shells" in data
        assert len(data["shells"]) == 4

        # Check first shell
        bash_shell = next(s for s in data["shells"] if s["name"] == "bash")
        assert bash_shell["executable"] == "bash"
        assert bash_shell["available"] is True

    @patch("rez.shells.get_shell_types")
    @patch("rez.shells.get_shell_class")
    def test_list_shells_with_unavailable(self, mock_get_class, mock_get_types, client):
        """Test shells listing with some unavailable shells."""
        # Mock shell types
        mock_get_types.return_value = ["bash", "tcsh", "cmd"]

        # Mock shell classes with mixed availability
        def mock_shell_class_factory(shell_name):
            mock_class = Mock()
            mock_class.name.return_value = shell_name
            mock_class.executable = shell_name
            mock_class.file_extension.return_value = ".sh"
            mock_class.is_available.return_value = (
                shell_name != "tcsh"
            )  # tcsh unavailable
            mock_class.executable_filepath.return_value = (
                f"/bin/{shell_name}" if shell_name != "tcsh" else None
            )
            return mock_class

        mock_get_class.side_effect = mock_shell_class_factory

        response = client.get("/api/v1/shells")
        assert response.status_code == 200

        data = response.json()
        assert "shells" in data

        # Check availability
        bash_shell = next(s for s in data["shells"] if s["name"] == "bash")
        assert bash_shell["available"] is True

        tcsh_shell = next(s for s in data["shells"] if s["name"] == "tcsh")
        assert tcsh_shell["available"] is False

    @patch("rez.shells.get_shell_types")
    def test_list_shells_exception_handling(self, mock_get_types, client):
        """Test shells listing exception handling."""
        mock_get_types.side_effect = Exception("Rez error")

        response = client.get("/api/v1/shells")
        assert response.status_code == 500

    @patch("rez.shells.get_shell_class")
    def test_get_shell_info_success(self, mock_get_class, client):
        """Test successful shell info retrieval."""
        # Mock shell class
        mock_class = Mock()
        mock_class.name.return_value = "bash"
        mock_class.executable = "bash"
        mock_class.file_extension.return_value = ".sh"
        mock_class.is_available.return_value = True
        mock_class.executable_filepath.return_value = "/bin/bash"
        mock_class.__doc__ = "Bash shell implementation"

        mock_get_class.return_value = mock_class

        response = client.get("/api/v1/shells/bash")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "bash"
        assert data["executable"] == "bash"
        assert data["file_extension"] == ".sh"
        assert data["available"] is True
        assert data["executable_path"] == "/bin/bash"

    @patch("rez.shells.get_shell_class")
    def test_get_shell_info_not_found(self, mock_get_class, client):
        """Test shell info retrieval for non-existent shell."""
        mock_get_class.side_effect = Exception("Shell not found")

        response = client.get("/api/v1/shells/nonexistent")
        assert response.status_code == 404

    @patch("rez.shells.get_shell_class")
    def test_get_shell_info_unavailable(self, mock_get_class, client):
        """Test shell info retrieval for unavailable shell."""
        # Mock unavailable shell class
        mock_class = Mock()
        mock_class.name.return_value = "tcsh"
        mock_class.executable = "tcsh"
        mock_class.file_extension.return_value = ".csh"
        mock_class.is_available.return_value = False
        mock_class.executable_filepath.return_value = None
        mock_class.__doc__ = "Tcsh shell implementation"

        mock_get_class.return_value = mock_class

        response = client.get("/api/v1/shells/tcsh")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "tcsh"
        assert data["available"] is False
        assert data["executable_path"] is None

    @patch("rez.shells.get_shell_class")
    def test_get_shell_info_exception_handling(self, mock_get_class, client):
        """Test shell info retrieval exception handling."""
        mock_get_class.side_effect = Exception("Rez error")

        response = client.get("/api/v1/shells/bash")
        assert response.status_code == 404  # Treated as not found

    @patch("rez.shells.get_shell_types")
    @patch("rez.shells.get_shell_class")
    def test_list_shells_empty_result(self, mock_get_class, mock_get_types, client):
        """Test shells listing with empty result."""
        mock_get_types.return_value = []

        response = client.get("/api/v1/shells")
        assert response.status_code == 200

        data = response.json()
        assert data["shells"] == []

    @patch("rez.shells.get_shell_types")
    @patch("rez.shells.get_shell_class")
    def test_list_shells_filter_available_only(
        self, mock_get_class, mock_get_types, client
    ):
        """Test shells listing with available_only filter."""
        # Mock shell types
        mock_get_types.return_value = ["bash", "tcsh", "cmd"]

        # Mock shell classes with mixed availability
        def mock_shell_class_factory(shell_name):
            mock_class = Mock()
            mock_class.name.return_value = shell_name
            mock_class.executable = shell_name
            mock_class.file_extension.return_value = ".sh"
            mock_class.is_available.return_value = shell_name in ["bash", "cmd"]
            mock_class.executable_filepath.return_value = (
                f"/bin/{shell_name}" if shell_name in ["bash", "cmd"] else None
            )
            return mock_class

        mock_get_class.side_effect = mock_shell_class_factory

        response = client.get("/api/v1/shells?available_only=true")
        assert response.status_code == 200

        data = response.json()
        assert "shells" in data

        # Should only include available shells
        available_shells = [s for s in data["shells"] if s["available"]]
        assert len(available_shells) == len(
            data["shells"]
        )  # All returned shells should be available

        shell_names = [s["name"] for s in data["shells"]]
        assert "bash" in shell_names
        assert "cmd" in shell_names
        # tcsh might or might not be included depending on implementation


class TestShellUtilities:
    """Test shell utility functions."""

    def test_shell_info_conversion(self):
        """Test shell class to info conversion."""
        from rez_proxy.routers.shells import _shell_to_info

        # Mock shell class
        mock_class = Mock()
        mock_class.name.return_value = "bash"
        mock_class.executable = "bash"
        mock_class.file_extension.return_value = ".sh"
        mock_class.is_available.return_value = True
        mock_class.executable_filepath.return_value = "/bin/bash"
        mock_class.__doc__ = "Bash shell implementation"

        info = _shell_to_info(mock_class)

        assert info["name"] == "bash"
        assert info["executable"] == "bash"
        assert info["file_extension"] == ".sh"
        assert info["available"] is True
        assert info["executable_path"] == "/bin/bash"
        assert info["description"] == "Bash shell implementation"

    def test_shell_info_conversion_minimal(self):
        """Test shell class to info conversion with minimal data."""
        from rez_proxy.routers.shells import _shell_to_info

        # Mock minimal shell class
        mock_class = Mock()
        mock_class.name.return_value = "test"
        mock_class.executable = "test"
        mock_class.file_extension.return_value = ".test"
        mock_class.is_available.return_value = False
        mock_class.executable_filepath.return_value = None
        mock_class.__doc__ = None

        info = _shell_to_info(mock_class)

        assert info["name"] == "test"
        assert info["executable"] == "test"
        assert info["file_extension"] == ".test"
        assert info["available"] is False
        assert info["executable_path"] is None
        assert info["description"] is None

    def test_shell_info_conversion_with_exception(self):
        """Test shell class to info conversion with exceptions."""
        from rez_proxy.routers.shells import _shell_to_info

        # Mock shell class that raises exceptions
        mock_class = Mock()
        mock_class.name.side_effect = Exception("Name error")
        mock_class.executable = "test"
        mock_class.file_extension.return_value = ".test"
        mock_class.is_available.return_value = False
        mock_class.executable_filepath.return_value = None
        mock_class.__doc__ = None

        # Should handle exceptions gracefully
        info = _shell_to_info(mock_class)

        # Should have some default values or handle the exception
        assert "name" in info
        assert "executable" in info
