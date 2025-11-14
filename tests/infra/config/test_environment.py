import os
from threading import Thread
from unittest.mock import patch

import pytest

from arcadiumai.infra import EnvironmentConfig


@pytest.mark.unit
class TestEnvironmentConfig:
    def setup_method(self):
        EnvironmentConfig.reset()

    def teardown_method(self):
        EnvironmentConfig.reset()

    def test_singleton_pattern(self):
        instance1 = EnvironmentConfig()
        instance2 = EnvironmentConfig()

        assert instance1 is instance2

    def test_get_api_key_success(self):
        with patch.dict(os.environ, {"TEST_API_KEY": "test_value"}):
            EnvironmentConfig.reset()
            key = EnvironmentConfig.get_api_key("TEST_API_KEY")

            assert key == "test_value"

    def test_get_api_key_missing_raises_error(self):
        EnvironmentConfig.reset()

        with pytest.raises(EnvironmentError, match="was not found"):
            EnvironmentConfig.get_api_key("NONEXISTENT_KEY")

    def test_get_api_key_uses_cache(self):
        with patch.dict(os.environ, {"CACHED_KEY": "cached_value"}):
            EnvironmentConfig.reset()

            key1 = EnvironmentConfig.get_api_key("CACHED_KEY")

            with patch.dict(os.environ, {"CACHED_KEY": "new_value"}, clear=True):
                key2 = EnvironmentConfig.get_api_key("CACHED_KEY")

            assert key1 == key2 == "cached_value"

    def test_clear_cache(self):
        with patch.dict(os.environ, {"CACHE_TEST": "value1"}):
            EnvironmentConfig.reset()
            key1 = EnvironmentConfig.get_api_key("CACHE_TEST")

            EnvironmentConfig.clear_cache()

            with patch.dict(os.environ, {"CACHE_TEST": "value2"}):
                key2 = EnvironmentConfig.get_api_key("CACHE_TEST")

            assert key1 == "value1"
            assert key2 == "value2"

    def test_reset_clears_instance(self):
        instance1 = EnvironmentConfig()
        EnvironmentConfig.reset()
        instance2 = EnvironmentConfig()

        assert instance1 is not instance2

    def test_reset_clears_cache(self):
        with patch.dict(os.environ, {"RESET_TEST": "original"}):
            EnvironmentConfig.reset()
            EnvironmentConfig.get_api_key("RESET_TEST")

            assert "RESET_TEST" in EnvironmentConfig._cache

            EnvironmentConfig.reset()

            assert len(EnvironmentConfig._cache) == 0

    def test_multiple_keys_cached_independently(self):
        with patch.dict(os.environ, {"KEY1": "value1", "KEY2": "value2"}):
            EnvironmentConfig.reset()

            val1 = EnvironmentConfig.get_api_key("KEY1")
            val2 = EnvironmentConfig.get_api_key("KEY2")

            assert val1 == "value1"
            assert val2 == "value2"
            assert len(EnvironmentConfig._cache) == 2

    def test_error_message_includes_key_name(self):
        EnvironmentConfig.reset()

        with pytest.raises(EnvironmentError, match="MISSING_KEY"):
            EnvironmentConfig.get_api_key("MISSING_KEY")

    def test_initialization_only_once(self):
        EnvironmentConfig.reset()

        assert EnvironmentConfig._initialized is False

        EnvironmentConfig()
        assert EnvironmentConfig._initialized is True

        EnvironmentConfig()
        assert EnvironmentConfig._initialized is True

    def test_get_env_with_existing_value(self):
        with patch.dict(os.environ, {"ENV_VAR": "env_value"}):
            EnvironmentConfig.reset()
            value = EnvironmentConfig.get_env("ENV_VAR")

            assert value == "env_value"

    def test_get_env_with_default_when_missing(self):
        EnvironmentConfig.reset()
        value = EnvironmentConfig.get_env("MISSING_VAR", default="default_value")

        assert value == "default_value"

    def test_get_env_returns_none_without_default(self):
        EnvironmentConfig.reset()
        value = EnvironmentConfig.get_env("MISSING_VAR")

        assert value is None

    def test_get_env_uses_cache(self):
        with patch.dict(os.environ, {"CACHED_ENV": "cached_env_value"}):
            EnvironmentConfig.reset()

            value1 = EnvironmentConfig.get_env("CACHED_ENV")

            with patch.dict(os.environ, {}, clear=True):
                value2 = EnvironmentConfig.get_env("CACHED_ENV")

            assert value1 == value2 == "cached_env_value"

    def test_thread_safety_singleton_creation(self):
        EnvironmentConfig.reset()
        instances = []

        def create_instance():
            instance = EnvironmentConfig()
            instances.append(id(instance))

        threads = [Thread(target=create_instance) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(set(instances)) == 1

    def test_thread_safety_get_api_key(self):
        with patch.dict(os.environ, {"THREAD_KEY": "thread_value"}):
            EnvironmentConfig.reset()
            results = []
            errors = []

            def get_key():
                try:
                    value = EnvironmentConfig.get_api_key("THREAD_KEY")
                    results.append(value)
                except Exception as e:
                    errors.append(e)

            threads = [Thread(target=get_key) for _ in range(20)]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            assert len(errors) == 0
            assert len(results) == 20
            assert all(r == "thread_value" for r in results)

    def test_get_api_key_with_empty_string_raises_error(self):
        with patch.dict(os.environ, {"EMPTY_KEY": ""}):
            EnvironmentConfig.reset()

            with pytest.raises(EnvironmentError):
                EnvironmentConfig.get_api_key("EMPTY_KEY")

    def test_cache_consistency_between_get_methods(self):
        with patch.dict(os.environ, {"SHARED_KEY": "shared_value"}):
            EnvironmentConfig.reset()

            value1 = EnvironmentConfig.get_api_key("SHARED_KEY")

            value2 = EnvironmentConfig.get_env("SHARED_KEY")

            assert value1 == value2 == "shared_value"

    def test_dotenv_loaded_only_once(self):
        with patch("arcadiumai.infra.config.environment.load_dotenv") as mock_load:
            EnvironmentConfig.reset()

            EnvironmentConfig()
            EnvironmentConfig()
            EnvironmentConfig()

            assert mock_load.call_count == 1

    def test_get_api_key_strips_whitespace(self):
        with patch.dict(os.environ, {"WHITESPACE_KEY": "  value_with_spaces  "}):
            EnvironmentConfig.reset()
            value = EnvironmentConfig.get_api_key("WHITESPACE_KEY")

            assert value == "value_with_spaces"
            assert value == EnvironmentConfig._cache["WHITESPACE_KEY"]

    def test_get_api_key_with_only_whitespace_raises_error(self):
        with patch.dict(os.environ, {"WHITESPACE_ONLY": "   "}):
            EnvironmentConfig.reset()

            with pytest.raises(EnvironmentError, match="is empty"):
                EnvironmentConfig.get_api_key("WHITESPACE_ONLY")

    def test_get_env_strips_whitespace(self):
        with patch.dict(os.environ, {"WHITESPACE_ENV": "  env_value  "}):
            EnvironmentConfig.reset()
            value = EnvironmentConfig.get_env("WHITESPACE_ENV")

            assert value == "env_value"

    def test_get_env_with_empty_string_returns_default(self):
        with patch.dict(os.environ, {"EMPTY_ENV": ""}):
            EnvironmentConfig.reset()
            value = EnvironmentConfig.get_env("EMPTY_ENV", default="default")

            assert value == "default"

    def test_get_env_with_whitespace_only_returns_default(self):
        with patch.dict(os.environ, {"WHITESPACE_ONLY_ENV": "   "}):
            EnvironmentConfig.reset()
            value = EnvironmentConfig.get_env("WHITESPACE_ONLY_ENV", default="default")

            assert value == "default"

    def test_get_env_does_not_cache_empty_values(self):
        with patch.dict(os.environ, {"EMPTY_CACHE": ""}):
            EnvironmentConfig.reset()
            EnvironmentConfig.get_env("EMPTY_CACHE", default="default")

            assert "EMPTY_CACHE" not in EnvironmentConfig._cache

    def test_reload_reloads_dotenv(self):
        with patch("arcadiumai.infra.config.environment.load_dotenv") as mock_load:
            EnvironmentConfig.reset()
            EnvironmentConfig()

            assert mock_load.call_count == 1

            EnvironmentConfig.reload()

            assert mock_load.call_count == 2
            mock_load.assert_called_with(override=True)

    def test_reload_clears_cache(self):
        with patch.dict(os.environ, {"RELOAD_KEY": "original"}):
            EnvironmentConfig.reset()
            _ = EnvironmentConfig.get_api_key("RELOAD_KEY")

            assert "RELOAD_KEY" in EnvironmentConfig._cache

            EnvironmentConfig.reload()

            assert "RELOAD_KEY" not in EnvironmentConfig._cache

    def test_reload_allows_new_values(self):
        with patch.dict(os.environ, {"RELOAD_TEST": "value1"}):
            EnvironmentConfig.reset()
            val1 = EnvironmentConfig.get_api_key("RELOAD_TEST")

            EnvironmentConfig.reload()

            with patch.dict(os.environ, {"RELOAD_TEST": "value2"}):
                val2 = EnvironmentConfig.get_api_key("RELOAD_TEST")

            assert val1 == "value1"
            assert val2 == "value2"

    def test_reload_is_thread_safe(self):
        with patch.dict(os.environ, {"THREAD_RELOAD": "initial"}):
            EnvironmentConfig.reset()
            EnvironmentConfig.get_api_key("THREAD_RELOAD")

            errors = []

            def reload_env():
                try:
                    EnvironmentConfig.reload()
                except Exception as e:
                    errors.append(e)

            threads = [Thread(target=reload_env) for _ in range(10)]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            assert len(errors) == 0

    def test_multiple_api_keys_with_validation(self):
        with patch.dict(
            os.environ,
            {
                "KEY_VALID": "valid_value",
                "KEY_EMPTY": "",
                "KEY_WHITESPACE": "   ",
                "KEY_NORMAL": "normal",
            },
        ):
            EnvironmentConfig.reset()

            assert EnvironmentConfig.get_api_key("KEY_VALID") == "valid_value"
            assert EnvironmentConfig.get_api_key("KEY_NORMAL") == "normal"

            with pytest.raises(EnvironmentError):
                EnvironmentConfig.get_api_key("KEY_EMPTY")

            with pytest.raises(EnvironmentError):
                EnvironmentConfig.get_api_key("KEY_WHITESPACE")

    def test_cache_survives_multiple_get_env_calls(self):
        with patch.dict(os.environ, {"PERSISTENT": "persist_value"}):
            EnvironmentConfig.reset()

            for i in range(5):
                value = EnvironmentConfig.get_env("PERSISTENT")
                assert value == "persist_value"

            assert "PERSISTENT" in EnvironmentConfig._cache

    def test_get_env_none_value_not_stripped(self):
        EnvironmentConfig.reset()
        value = EnvironmentConfig.get_env("NONEXISTENT_VAR", default=None)

        assert value is None

    def test_get_api_key_concurrent_first_access(self):
        from threading import Barrier, Thread

        with patch.dict(os.environ, {"CONCURRENT_API_KEY": "concurrent_value"}):
            EnvironmentConfig.reset()
            results = []
            errors = []
            barrier = Barrier(5)

            def get_key_synchronized():
                try:
                    barrier.wait()
                    key = EnvironmentConfig.get_api_key("CONCURRENT_API_KEY")
                    results.append(key)
                except Exception as e:
                    errors.append(str(e))

            threads = [Thread(target=get_key_synchronized) for _ in range(5)]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            assert len(errors) == 0
            assert len(results) == 5
            assert all(r == "concurrent_value" for r in results)

    def test_get_env_with_none_strips_whitespace_from_env(self):
        with patch.dict(os.environ, {"STRIP_TEST": "  value_to_strip  "}):
            EnvironmentConfig.reset()
            value = EnvironmentConfig.get_env("STRIP_TEST")

            assert value == "value_to_strip"
            assert value == EnvironmentConfig._cache["STRIP_TEST"]
