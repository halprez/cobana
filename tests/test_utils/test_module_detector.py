"""Unit tests for module_detector module."""

import pytest
from pathlib import Path

from cobana.utils.module_detector import Module, ModuleDetector


@pytest.mark.unit
class TestModule:
    """Unit tests for Module class."""

    def test_module_creation(self):
        """Test creating a Module instance."""
        module = Module(name="test_module", path="test/path")
        assert module.name == "test_module"
        assert module.path == "test/path"
        assert "test_module" in module.description

    def test_module_equality(self):
        """Test Module equality comparison."""
        module1 = Module(name="test", path="path")
        module2 = Module(name="test", path="path")
        module3 = Module(name="other", path="path")

        assert module1 == module2
        assert module1 != module3

    def test_module_to_dict(self):
        """Test converting Module to dictionary."""
        module = Module(name="test", path="test/path", description="Test module")
        result = module.to_dict()

        assert result == {
            'name': 'test',
            'path': 'test/path',
            'description': 'Test module',
        }


@pytest.mark.unit
class TestModuleDetector:
    """Unit tests for ModuleDetector class."""

    def test_detector_initialization(self, temp_dir, basic_config):
        """Test ModuleDetector initialization."""
        detector = ModuleDetector(temp_dir, basic_config)
        assert detector.root_path == temp_dir.resolve()
        assert detector.config == basic_config
        assert len(detector.modules) == 0

    def test_auto_detect_depth_1(self, sample_codebase, basic_config):
        """Test auto-detection at depth 1."""
        detector = ModuleDetector(sample_codebase, basic_config)
        modules = detector.detect_modules()

        assert len(modules) == 2
        module_names = {m.name for m in modules}
        assert 'module_a' in module_names
        assert 'module_b' in module_names

    def test_auto_detect_depth_2(self, sample_codebase, basic_config):
        """Test auto-detection at depth 2."""
        config = basic_config.copy()
        config['module_detection']['depth'] = 2

        detector = ModuleDetector(sample_codebase, config)
        modules = detector.detect_modules()

        assert len(modules) == 1  # Only module_a/submodule at depth 2
        assert modules[0].name == 'submodule'

    def test_manual_module_detection(self, temp_dir, basic_config):
        """Test manual module detection."""
        config = basic_config.copy()
        config['module_detection'] = {
            'method': 'manual',
            'manual_modules': [
                {
                    'name': 'Custom Module',
                    'path': 'custom/path',
                    'description': 'A custom module',
                },
            ],
        }

        detector = ModuleDetector(temp_dir, config)
        modules = detector.detect_modules()

        assert len(modules) == 1
        assert modules[0].name == 'Custom Module'
        assert modules[0].path == 'custom/path'

    def test_exclude_hidden_directories(self, temp_dir, basic_config):
        """Test that hidden directories (starting with .) are excluded."""
        # Create directories
        (temp_dir / "visible").mkdir()
        (temp_dir / ".hidden").mkdir()

        detector = ModuleDetector(temp_dir, basic_config)
        modules = detector.detect_modules()

        module_names = {m.name for m in modules}
        assert 'visible' in module_names
        assert '.hidden' not in module_names

    def test_get_module_for_file(self, sample_codebase, basic_config):
        """Test mapping files to modules."""
        detector = ModuleDetector(sample_codebase, basic_config)
        detector.detect_modules()

        # File in module_a
        file_a = sample_codebase / "module_a" / "file1.py"
        assert detector.get_module_for_file(file_a) == "module_a"

        # File in module_b
        file_b = sample_codebase / "module_b" / "file3.py"
        assert detector.get_module_for_file(file_b) == "module_b"

        # File in submodule (should still map to module_a)
        file_sub = sample_codebase / "module_a" / "submodule" / "file2.py"
        assert detector.get_module_for_file(file_sub) == "module_a"

    def test_get_module_for_root_file(self, sample_codebase, basic_config):
        """Test that files in root map to 'root' module."""
        # Create a file in root
        root_file = sample_codebase / "root_file.py"
        root_file.write_text("# root")

        detector = ModuleDetector(sample_codebase, basic_config)
        detector.detect_modules()

        assert detector.get_module_for_file(root_file) == "root"

    def test_get_module_files(self, sample_codebase, basic_config):
        """Test getting all files for a specific module."""
        detector = ModuleDetector(sample_codebase, basic_config)
        detector.detect_modules()

        # Get all files in codebase
        all_files = list(sample_codebase.rglob("*.py"))

        # Get files for module_a
        module_a_files = detector.get_module_files("module_a", all_files)

        # Should include files in module_a and its subdirectories
        assert len(module_a_files) >= 3
        assert all("module_a" in str(f) for f in module_a_files)

    def test_invalid_detection_method(self, temp_dir, basic_config):
        """Test that invalid detection method raises error."""
        config = basic_config.copy()
        config['module_detection']['method'] = 'invalid'

        detector = ModuleDetector(temp_dir, config)
        with pytest.raises(ValueError, match="Invalid module detection method"):
            detector.detect_modules()
