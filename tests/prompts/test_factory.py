"""Tests for the PromptBuilder factory and registry."""
import pytest

from src.interfaces.prompts import PromptBuilder
from src.interfaces.models import FewShotExample
from src.interfaces.exceptions import PromptBuilderNotFoundError
from src.prompts import (
    get_prompt_builder,
    register_prompt_builder,
    list_available_domains,
    MSAPromptBuilder,
    HARPromptBuilder,
)


class TestGetPromptBuilder:
    """Tests for get_prompt_builder factory function."""
    
    def test_get_msa_builder(self):
        """Can retrieve MSA builder."""
        builder = get_prompt_builder("msa")
        assert isinstance(builder, MSAPromptBuilder)
    
    def test_get_har_builder(self):
        """Can retrieve HAR builder."""
        builder = get_prompt_builder("har")
        assert isinstance(builder, HARPromptBuilder)
    
    def test_case_insensitive(self):
        """Domain names are case-insensitive."""
        builder_lower = get_prompt_builder("msa")
        builder_upper = get_prompt_builder("MSA")
        builder_mixed = get_prompt_builder("MsA")
        
        assert type(builder_lower) == type(builder_upper) == type(builder_mixed)
    
    def test_unknown_domain_raises_error(self):
        """Unknown domain raises PromptBuilderNotFoundError."""
        with pytest.raises(PromptBuilderNotFoundError) as exc_info:
            get_prompt_builder("unknown_domain")
        
        assert "unknown_domain" in str(exc_info.value)
    
    def test_error_message_lists_available_domains(self):
        """Error message includes available domains."""
        with pytest.raises(PromptBuilderNotFoundError) as exc_info:
            get_prompt_builder("nonexistent")
        
        error_msg = str(exc_info.value)
        assert "msa" in error_msg or "har" in error_msg
    
    def test_returns_new_instance_each_time(self):
        """Each call returns a new instance (not singleton)."""
        builder1 = get_prompt_builder("msa")
        builder2 = get_prompt_builder("msa")
        
        assert builder1 is not builder2


class TestListAvailableDomains:
    """Tests for list_available_domains function."""
    
    def test_returns_list(self):
        """Returns a list."""
        domains = list_available_domains()
        assert isinstance(domains, list)
    
    def test_includes_msa_and_har(self):
        """Includes built-in domains."""
        domains = list_available_domains()
        assert "msa" in domains
        assert "har" in domains


class TestRegisterPromptBuilder:
    """Tests for dynamic registration of new builders."""
    
    def test_register_custom_builder(self):
        """Can register a custom builder."""
        
        # Create a custom builder
        class CustomBuilder(PromptBuilder):
            @property
            def domain_name(self) -> str:
                return "custom"
            
            def get_system_prompt(self) -> str:
                return "Custom system prompt"
            
            def get_fewshot_examples(self):
                return [FewShotExample(user="Custom input", assistant="Custom output")]
        
        # Register it
        register_prompt_builder("custom_test", CustomBuilder)
        
        # Retrieve it
        builder = get_prompt_builder("custom_test")
        assert isinstance(builder, CustomBuilder)
        assert builder.domain_name == "custom"
    
    def test_register_overwrites_existing(self):
        """Registering with same name overwrites previous."""
        
        class Builder1(PromptBuilder):
            @property
            def domain_name(self) -> str:
                return "v1"
            def get_system_prompt(self) -> str:
                return "v1 prompt"
            def get_fewshot_examples(self):
                return []
        
        class Builder2(PromptBuilder):
            @property
            def domain_name(self) -> str:
                return "v2"
            def get_system_prompt(self) -> str:
                return "v2 prompt"
            def get_fewshot_examples(self):
                return []
        
        register_prompt_builder("overwrite_test", Builder1)
        register_prompt_builder("overwrite_test", Builder2)
        
        builder = get_prompt_builder("overwrite_test")
        assert builder.domain_name == "v2"


class TestBuilderPolymorphism:
    """Tests that all registered builders work polymorphically."""
    
    @pytest.mark.parametrize("domain", ["msa", "har"])
    def test_all_builders_return_valid_llm_request(self, domain, sample_activity_description):
        """All registered builders produce valid LLMRequest."""
        builder = get_prompt_builder(domain)
        result = builder.build_prompt(sample_activity_description)
        
        assert result.prompt == sample_activity_description
        assert result.system_prompt is not None
        assert isinstance(result.fewshots, list)
    
    @pytest.mark.parametrize("domain", ["msa", "har"])
    def test_all_builders_handle_prerequisites(
        self, domain, sample_activity_description, sample_prerequisites
    ):
        """All registered builders handle prerequisites correctly."""
        builder = get_prompt_builder(domain)
        result = builder.build_prompt(
            sample_activity_description, 
            prerequisites=sample_prerequisites
        )
        
        # Prerequisites should be included in fewshots
        assert len(result.fewshots) >= len(sample_prerequisites)

