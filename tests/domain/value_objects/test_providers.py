import pytest

from createagents.domain import SupportedProviders


@pytest.mark.unit
class TestSupportedProviders:
    def test_get_available_providers(self):
        providers = SupportedProviders.get_available_providers()

        assert isinstance(providers, set)
        assert 'openai' in providers
        assert 'ollama' in providers

    def test_get_available_providers_returns_copy(self):
        providers1 = SupportedProviders.get_available_providers()
        providers2 = SupportedProviders.get_available_providers()

        assert providers1 == providers2
        assert providers1 is not providers2

    def test_available_providers_immutable(self):
        providers = SupportedProviders.get_available_providers()
        original_size = len(providers)

        providers.add('new_provider')

        new_providers = SupportedProviders.get_available_providers()
        assert len(new_providers) == original_size
        assert 'new_provider' not in new_providers

    def test_providers_count(self):
        providers = SupportedProviders.get_available_providers()

        assert len(providers) == 2

    def test_providers_are_lowercase(self):
        providers = SupportedProviders.get_available_providers()

        for provider in providers:
            assert provider == provider.lower()

    def test_no_empty_provider_names(self):
        providers = SupportedProviders.get_available_providers()

        for provider in providers:
            assert provider.strip() != ''
            assert len(provider) > 0

    def test_providers_are_strings(self):
        providers = SupportedProviders.get_available_providers()

        for provider in providers:
            assert isinstance(provider, str)

    def test_specific_providers_exist(self):
        providers = SupportedProviders.get_available_providers()

        assert 'openai' in providers
        assert 'ollama' in providers

    def test_providers_no_duplicates(self):
        providers = SupportedProviders.get_available_providers()

        providers_list = list(providers)
        assert len(providers_list) == len(set(providers_list))
