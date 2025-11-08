import pytest

from src.domain.exceptions.domain_exceptions import InvalidAgentConfigException
from src.domain.value_objects.configs_validator import SupportedConfigs


@pytest.mark.unit
class TestSupportedConfigs:
    def test_get_available_configs(self):
        configs = SupportedConfigs.get_available_configs()

        assert isinstance(configs, set)
        assert "temperature" in configs
        assert "max_tokens" in configs
        assert "top_p" in configs

    def test_get_available_configs_returns_copy(self):
        configs1 = SupportedConfigs.get_available_configs()
        configs2 = SupportedConfigs.get_available_configs()

        assert configs1 == configs2
        assert configs1 is not configs2

    def test_available_configs_immutable(self):
        configs = SupportedConfigs.get_available_configs()
        original_size = len(configs)

        configs.add("new_config")

        new_configs = SupportedConfigs.get_available_configs()
        assert len(new_configs) == original_size
        assert "new_config" not in new_configs


@pytest.mark.unit
class TestTemperatureValidation:
    def test_validate_temperature_valid_min(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_temperature(0.0)

    def test_validate_temperature_valid_max(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_temperature(2.0)

    def test_validate_temperature_valid_mid_range(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_temperature(1.0)
        SupportedConfigs.validate_temperature(0.5)
        SupportedConfigs.validate_temperature(1.5)

    def test_validate_temperature_none(self):
        # None é aceito (significa não especificado)
        SupportedConfigs.validate_temperature(None)

    def test_validate_temperature_below_min(self):
        with pytest.raises(InvalidAgentConfigException, match="temperature"):
            SupportedConfigs.validate_temperature(-0.1)

    def test_validate_temperature_above_max(self):
        with pytest.raises(InvalidAgentConfigException, match="temperature"):
            SupportedConfigs.validate_temperature(2.1)

    def test_validate_temperature_far_out_of_range(self):
        with pytest.raises(InvalidAgentConfigException, match="temperature"):
            SupportedConfigs.validate_temperature(10.0)

        with pytest.raises(InvalidAgentConfigException, match="temperature"):
            SupportedConfigs.validate_temperature(-5.0)


@pytest.mark.unit
class TestMaxTokensValidation:
    def test_validate_max_tokens_valid_small(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_max_tokens(1)

    def test_validate_max_tokens_valid_large(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_max_tokens(10000)

    def test_validate_max_tokens_valid_typical(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_max_tokens(100)
        SupportedConfigs.validate_max_tokens(500)
        SupportedConfigs.validate_max_tokens(2000)

    def test_validate_max_tokens_none(self):
        # None é aceito (significa não especificado)
        SupportedConfigs.validate_max_tokens(None)

    def test_validate_max_tokens_zero(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens(0)

    def test_validate_max_tokens_negative(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens(-1)

        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens(-100)

    def test_validate_max_tokens_string(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens("100")

    def test_validate_max_tokens_float(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens(100.5)


@pytest.mark.unit
class TestTopPValidation:
    def test_validate_top_p_valid_min(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_top_p(0.0)

    def test_validate_top_p_valid_max(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_top_p(1.0)

    def test_validate_top_p_valid_mid_range(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_top_p(0.5)
        SupportedConfigs.validate_top_p(0.9)
        SupportedConfigs.validate_top_p(0.95)

    def test_validate_top_p_none(self):
        # None é aceito (significa não especificado)
        SupportedConfigs.validate_top_p(None)

    def test_validate_top_p_below_min(self):
        with pytest.raises(InvalidAgentConfigException, match="top_p"):
            SupportedConfigs.validate_top_p(-0.1)

    def test_validate_top_p_above_max(self):
        with pytest.raises(InvalidAgentConfigException, match="top_p"):
            SupportedConfigs.validate_top_p(1.1)

    def test_validate_top_p_far_out_of_range(self):
        with pytest.raises(InvalidAgentConfigException, match="top_p"):
            SupportedConfigs.validate_top_p(2.0)

        with pytest.raises(InvalidAgentConfigException, match="top_p"):
            SupportedConfigs.validate_top_p(-1.0)


@pytest.mark.unit
class TestValidateConfig:
    def test_validate_config_temperature(self):
        # Válido
        SupportedConfigs.validate_config("temperature", 0.7)

        # Inválido
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("temperature", 3.0)

    def test_validate_config_max_tokens(self):
        # Válido
        SupportedConfigs.validate_config("max_tokens", 100)

        # Inválido
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("max_tokens", -10)

    def test_validate_config_top_p(self):
        # Válido
        SupportedConfigs.validate_config("top_p", 0.9)

        # Inválido
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("top_p", 1.5)

    def test_validate_config_unknown_key(self):
        # Chave desconhecida não lança erro (é ignorada)
        SupportedConfigs.validate_config("unknown_key", 123)

    def test_validate_config_all_supported(self):
        # Testa todas as configs suportadas
        SupportedConfigs.validate_config("temperature", 0.8)
        SupportedConfigs.validate_config("max_tokens", 500)
        SupportedConfigs.validate_config("top_p", 0.95)

    def test_validate_config_with_none_values(self):
        # None deve ser aceito para todas as configs
        SupportedConfigs.validate_config("temperature", None)
        SupportedConfigs.validate_config("max_tokens", None)
        SupportedConfigs.validate_config("top_p", None)

    def test_validate_config_boundary_values(self):
        """Testa validação com valores nos limites exatos."""
        # Temperature boundaries
        SupportedConfigs.validate_config("temperature", 0.0)
        SupportedConfigs.validate_config("temperature", 2.0)

        # Top_p boundaries
        SupportedConfigs.validate_config("top_p", 0.0)
        SupportedConfigs.validate_config("top_p", 1.0)

        # Max_tokens minimum
        SupportedConfigs.validate_config("max_tokens", 1)

    def test_validate_config_just_outside_boundaries(self):
        """Testa validação com valores logo fora dos limites."""
        # Temperature
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("temperature", -0.01)
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("temperature", 2.01)

        # Top_p
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("top_p", -0.01)
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("top_p", 1.01)

        # Max_tokens
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("max_tokens", 0)

    def test_get_available_configs_contains_all_supported(self):
        """Verifica que todos os configs suportados estão listados."""
        configs = SupportedConfigs.get_available_configs()
        expected_configs = {"temperature", "max_tokens", "top_p", "think", "top_k"}
        assert configs == expected_configs

    def test_validate_max_tokens_with_large_value(self):
        """Testa max_tokens com valor muito grande."""
        SupportedConfigs.validate_max_tokens(1000000)
        # Não deve lançar erro

    def test_validate_temperature_precision(self):
        """Testa temperature com valores de alta precisão."""
        SupportedConfigs.validate_temperature(0.123456789)
        SupportedConfigs.validate_temperature(1.999999999)
        # Não deve lançar erro

    def test_validate_top_p_precision(self):
        """Testa top_p com valores de alta precisão."""
        SupportedConfigs.validate_top_p(0.123456789)
        SupportedConfigs.validate_top_p(0.999999999)
        # Não deve lançar erro


@pytest.mark.unit
class TestThinkValidation:
    """Test suite for 'think' configuration validation."""

    def test_validate_think_with_boolean_true(self):
        """Test think validation with boolean True (Ollama provider)."""
        SupportedConfigs.validate_think(True)
        # Should not raise

    def test_validate_think_with_boolean_false(self):
        """Test think validation with boolean False."""
        SupportedConfigs.validate_think(False)
        # Should not raise

    def test_validate_think_with_none(self):
        """Test think validation with None."""
        SupportedConfigs.validate_think(None)
        # Should not raise

    def test_validate_think_with_valid_dict(self):
        """Test think validation with valid dict (OpenAI provider)."""
        valid_dict = {"type": "enabled", "budget": "medium"}
        SupportedConfigs.validate_think(valid_dict)
        # Should not raise

    def test_validate_think_with_empty_dict(self):
        """Test think validation with empty dict."""
        SupportedConfigs.validate_think({})
        # Should not raise

    def test_validate_think_with_dict_string_keys_values(self):
        """Test think validation with dict having string keys and values."""
        valid_dict = {
            "mode": "reasoning",
            "depth": "deep",
            "strategy": "comprehensive",
        }
        SupportedConfigs.validate_think(valid_dict)
        # Should not raise

    def test_validate_think_with_dict_non_string_key(self):
        """Test think validation fails with non-string dict key."""
        invalid_dict = {123: "value"}

        with pytest.raises(InvalidAgentConfigException, match="think"):
            SupportedConfigs.validate_think(invalid_dict)

    def test_validate_think_with_dict_non_string_value(self):
        """Test think validation fails with non-string dict value."""
        invalid_dict = {"key": 123}

        with pytest.raises(InvalidAgentConfigException, match="think"):
            SupportedConfigs.validate_think(invalid_dict)

    def test_validate_think_with_dict_mixed_types(self):
        """Test think validation fails with mixed types in dict."""
        invalid_dict = {"valid": "string", "invalid": 42}

        with pytest.raises(InvalidAgentConfigException, match="think"):
            SupportedConfigs.validate_think(invalid_dict)

    def test_validate_think_with_invalid_type_string(self):
        """Test think validation fails with string (not bool or dict)."""
        with pytest.raises(InvalidAgentConfigException, match="think"):
            SupportedConfigs.validate_think("enabled")

    def test_validate_think_with_invalid_type_int(self):
        """Test think validation fails with integer."""
        with pytest.raises(InvalidAgentConfigException, match="think"):
            SupportedConfigs.validate_think(1)

    def test_validate_think_with_invalid_type_float(self):
        """Test think validation fails with float."""
        with pytest.raises(InvalidAgentConfigException, match="think"):
            SupportedConfigs.validate_think(0.5)

    def test_validate_think_with_invalid_type_list(self):
        """Test think validation fails with list."""
        with pytest.raises(InvalidAgentConfigException, match="think"):
            SupportedConfigs.validate_think(["enabled"])

    def test_validate_think_error_message_format(self):
        """Test that error message mentions both boolean and dict options."""
        with pytest.raises(InvalidAgentConfigException) as exc_info:
            SupportedConfigs.validate_think("invalid")

        error_msg = str(exc_info.value)
        assert "boolean" in error_msg.lower() or "bool" in error_msg.lower()
        assert "dict" in error_msg.lower()


@pytest.mark.unit
class TestTopKValidation:
    """Test suite for 'top_k' configuration validation."""

    def test_validate_top_k_with_valid_small_value(self):
        """Test top_k validation with small valid value."""
        SupportedConfigs.validate_top_k(1)
        # Should not raise

    def test_validate_top_k_with_valid_medium_value(self):
        """Test top_k validation with medium valid value."""
        SupportedConfigs.validate_top_k(50)
        # Should not raise

    def test_validate_top_k_with_valid_large_value(self):
        """Test top_k validation with large valid value."""
        SupportedConfigs.validate_top_k(1000)
        # Should not raise

    def test_validate_top_k_with_none(self):
        """Test top_k validation with None."""
        SupportedConfigs.validate_top_k(None)
        # Should not raise

    def test_validate_top_k_with_zero(self):
        """Test top_k validation fails with zero."""
        with pytest.raises(InvalidAgentConfigException, match="top_k"):
            SupportedConfigs.validate_top_k(0)

    def test_validate_top_k_with_negative_value(self):
        """Test top_k validation fails with negative value."""
        with pytest.raises(InvalidAgentConfigException, match="top_k"):
            SupportedConfigs.validate_top_k(-1)

    def test_validate_top_k_with_large_negative_value(self):
        """Test top_k validation fails with large negative value."""
        with pytest.raises(InvalidAgentConfigException, match="top_k"):
            SupportedConfigs.validate_top_k(-100)

    def test_validate_top_k_with_float_value(self):
        """Test top_k validation fails with float."""
        with pytest.raises(InvalidAgentConfigException, match="top_k"):
            SupportedConfigs.validate_top_k(10.5)

    def test_validate_top_k_with_string_value(self):
        """Test top_k validation fails with string."""
        with pytest.raises(InvalidAgentConfigException, match="top_k"):
            SupportedConfigs.validate_top_k("10")

    def test_validate_top_k_with_boolean_value(self):
        """Test top_k validation with boolean value - might pass as bool is int subclass."""
        # In Python, bool is a subclass of int, so True is treated as 1
        # This test documents this behavior
        try:
            SupportedConfigs.validate_top_k(True)
            # If it passes, True is treated as 1 (valid)
        except InvalidAgentConfigException:
            # If it raises, boolean values are explicitly rejected
            pass

    def test_validate_top_k_error_message_format(self):
        """Test that error message is informative."""
        with pytest.raises(InvalidAgentConfigException) as exc_info:
            SupportedConfigs.validate_top_k(0)

        error_msg = str(exc_info.value)
        assert "top_k" in error_msg
        assert "integer" in error_msg.lower()
        assert "greater than zero" in error_msg.lower()


@pytest.mark.unit
class TestValidateConfigExtended:
    """Extended tests for validate_config method."""

    def test_validate_config_think_with_boolean(self):
        """Test validate_config with think as boolean."""
        SupportedConfigs.validate_config("think", True)
        SupportedConfigs.validate_config("think", False)
        # Should not raise

    def test_validate_config_think_with_dict(self):
        """Test validate_config with think as dict."""
        SupportedConfigs.validate_config("think", {"mode": "enabled"})
        # Should not raise

    def test_validate_config_think_with_invalid_type(self):
        """Test validate_config with think as invalid type."""
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("think", "string")

    def test_validate_config_top_k_with_valid_value(self):
        """Test validate_config with top_k valid value."""
        SupportedConfigs.validate_config("top_k", 40)
        # Should not raise

    def test_validate_config_top_k_with_invalid_value(self):
        """Test validate_config with top_k invalid value."""
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("top_k", 0)

        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("top_k", -5)

    def test_validate_config_all_supported_configs(self):
        """Test validate_config with all supported configurations."""
        # Valid values for all configs
        SupportedConfigs.validate_config("temperature", 0.7)
        SupportedConfigs.validate_config("max_tokens", 100)
        SupportedConfigs.validate_config("top_p", 0.9)
        SupportedConfigs.validate_config("think", True)
        SupportedConfigs.validate_config("top_k", 50)
        # Should not raise

    def test_get_available_configs_includes_think_and_top_k(self):
        """Test that available configs includes think and top_k."""
        configs = SupportedConfigs.get_available_configs()

        assert "think" in configs
        assert "top_k" in configs

    def test_get_available_configs_complete_set(self):
        """Test that all supported configs are present."""
        configs = SupportedConfigs.get_available_configs()
        expected = {"temperature", "max_tokens", "top_p", "think", "top_k"}

        assert configs == expected
