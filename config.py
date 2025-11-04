"""Configuration management for the Travel Agent application.

Provides a typed `AppConfig` with environment-driven settings and basic
dependency checks used by the UI entrypoint.
"""
# import suppress_warnings  # Must be first to suppress warnings
import warnings

warnings.filterwarnings("ignore")
from typing import Literal, Optional

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings

from utils.azure_foundry_search import AzureFoundrySearchClient, SearchProviderError


class AppConfig(BaseSettings):
    """Application configuration with validation."""

    # Provider selection
    llm_provider: Literal["openai", "azure_openai"] = Field(
        default="openai",
        env="LLM_PROVIDER",
        description="Provider for core LLM + Mem0 (openai or azure_openai)",
    )
    search_provider: Literal["tavily", "azure_foundry_agent"] = Field(
        default="tavily",
        env="SEARCH_PROVIDER",
        description="Web search provider used by tools",
    )

    # OpenAI configuration
    openai_api_key: Optional[str] = Field(
        default=None,
        env="OPENAI_API_KEY",
        description="OpenAI API key",
    )

    # Azure OpenAI configuration
    azure_openai_api_key: Optional[str] = Field(
        default=None,
        env="AZURE_OPENAI_API_KEY",
        description="Azure OpenAI key (KEY1/KEY2)",
    )
    azure_openai_endpoint: Optional[str] = Field(
        default=None,
        env="AZURE_OPENAI_ENDPOINT",
        description="Azure OpenAI endpoint (https://<resource>.openai.azure.com)",
    )
    azure_openai_api_version: str = Field(
        default="2024-10-21",
        env="AZURE_OPENAI_API_VERSION",
        description="Azure OpenAI API version",
    )
    azure_openai_responses_deployment: Optional[str] = Field(
        default=None,
        env="AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME",
        validation_alias=AliasChoices(
            "AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME",
            "AZURE_OPENAI_RESPONSES_DEPLOYMENT",
        ),
        description="Azure OpenAI deployment name for Responses API",
    )
    azure_openai_embeddings_deployment: Optional[str] = Field(
        default=None,
        env="AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME",
        validation_alias=AliasChoices(
            "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME",
            "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT",
        ),
        description="Azure OpenAI deployment name for embeddings (Mem0)",
    )
    azure_openai_mem0_llm_deployment: Optional[str] = Field(
        default=None,
        env="AZURE_OPENAI_MEM0_LLM_DEPLOYMENT_NAME",
        validation_alias=AliasChoices(
            "AZURE_OPENAI_MEM0_LLM_DEPLOYMENT_NAME",
            "AZURE_OPENAI_MEM0_LLM_DEPLOYMENT",
        ),
        description="Azure OpenAI deployment name used by Mem0 LLM",
    )

    # Search configuration
    tavily_api_key: Optional[str] = Field(
        default=None,
        env="TAVILY_API_KEY",
        description="Tavily API key",
    )
    azure_foundry_api_key: Optional[str] = Field(
        default=None,
        env="AZURE_FOUNDRY_API_KEY",
        description="Azure AI Foundry API key",
    )
    azure_foundry_endpoint: Optional[str] = Field(
        default=None,
        env="AZURE_FOUNDRY_ENDPOINT",
        description="Azure AI Foundry inference endpoint URL",
    )
    azure_foundry_search_agent_id: Optional[str] = Field(
        default=None,
        env="AZURE_FOUNDRY_SEARCH_AGENT_ID",
        description="Azure AI Foundry search agent deployment ID",
    )

    # Model Configuration
    travel_agent_model: str = Field(
        default="gpt-4o-mini",
        env="TRAVEL_AGENT_MODEL",
        description="Base model ID or deployment for the travel agent",
    )
    mem0_model: str = Field(
        default="gpt-4o-mini",
        env="MEM0_MODEL",
        description="Model/deployment backing Mem0 LLM",
    )
    mem0_embedding_model: str = Field(
        default="text-embedding-3-small",
        env="MEM0_EMBEDDING_MODEL",
        description="Embedding model or deployment backing Mem0",
    )
    mem0_embedding_model_dims: int = Field(
        default=1536,
        env="MEM0_EMBEDDING_MODEL_DIMS",
        validation_alias=AliasChoices("MEM0_EMBEDDING_MODEL_DIMS", "MEM0_EMBDDING_MODEL_DIMS"),
        description="Embedding dimensionality",
    )

    # Other config
    max_tool_iterations: int = Field(default=8, env="MAX_TOOL_ITERATIONS", description="Maximum tool iterations")
    # Keep at least last 20 conversation steps (≈ 40 messages)
    max_chat_history_size: int = Field(default=40, env="MAX_CHAT_HISTORY_SIZE", description="Maximum chat history size (messages)")
    max_search_results: int = Field(default=5, env="MAX_SEARCH_RESULTS", description="Maximum search results from Tavily client")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL", description="Redis connection URL")
    
    # Mem0 mode selection
    mem0_cloud: bool = Field(default=False, env="MEM0_CLOUD", description="Use Mem0 Cloud when true; otherwise use local Mem0 with Redis vector store")

    # Server Configuration
    server_name: str = Field(default="0.0.0.0", env="SERVER_NAME", description="Server host")
    server_port: int = Field(default=7860, env="SERVER_PORT", description="Server port")
    share: bool = Field(default=False, env="SHARE", description="Enable public sharing")

    # Optional unless using Mem0 Cloud
    MEM0_API_KEY: Optional[str] = Field(default=None, env="MEM0_API_KEY", description="Mem0 API key (required if MEM0_CLOUD=true)")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v):
        """Validate OpenAI API key format when provided."""
        if v and not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v
    
    @model_validator(mode="after")
    def validate_mem0_requirements(self):  # type: ignore[override]
        """Ensure MEM0_API_KEY is present when using Mem0 Cloud."""
        if self.mem0_cloud and not (self.MEM0_API_KEY and self.MEM0_API_KEY.strip()):
            raise ValueError("MEM0_API_KEY is required when MEM0_CLOUD is true")
        return self

    @model_validator(mode="after")
    def validate_provider_requirements(self):  # type: ignore[override]
        """Validate provider-specific settings."""
        if self.llm_provider == "openai":
            if not (self.openai_api_key and self.openai_api_key.strip()):
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        else:
            missing = []
            if not (self.azure_openai_api_key and self.azure_openai_api_key.strip()):
                missing.append("AZURE_OPENAI_API_KEY")
            if not (self.azure_openai_endpoint and self.azure_openai_endpoint.strip()):
                missing.append("AZURE_OPENAI_ENDPOINT")
            if not (self.azure_openai_responses_deployment and self.azure_openai_responses_deployment.strip()):
                missing.append("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")
            if missing:
                raise ValueError(
                    "Missing Azure OpenAI settings: " + ", ".join(missing)
                )

        if self.search_provider == "tavily":
            if not (self.tavily_api_key and self.tavily_api_key.strip()):
                raise ValueError("TAVILY_API_KEY is required when SEARCH_PROVIDER=tavily")
        elif self.search_provider == "azure_foundry_agent":
            missing = []
            if not (self.azure_foundry_api_key and self.azure_foundry_api_key.strip()):
                missing.append("AZURE_FOUNDRY_API_KEY")
            if not (self.azure_foundry_endpoint and self.azure_foundry_endpoint.strip()):
                missing.append("AZURE_FOUNDRY_ENDPOINT")
            if not (self.azure_foundry_search_agent_id and self.azure_foundry_search_agent_id.strip()):
                missing.append("AZURE_FOUNDRY_SEARCH_AGENT_ID")
            if missing:
                raise ValueError(
                    "Missing Azure AI Foundry settings: " + ", ".join(missing)
                )
        return self



def get_config() -> AppConfig:
    """Get application configuration with proper error handling."""
    try:
        return AppConfig()
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        print("\n📝 Please check your environment variables or create a .env file with:")
        print("LLM_PROVIDER=openai  # or azure_openai")
        print("SEARCH_PROVIDER=tavily  # or azure_foundry_agent")
        print("# When using OpenAI")
        print("OPENAI_API_KEY=sk-your-key-here")
        print("# When using Azure OpenAI")
        print("# AZURE_OPENAI_API_KEY=your-key-here")
        print("# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com")
        print("# AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=your-deployment")
        print("# Provide search keys based on SEARCH_PROVIDER (Tavily or Azure AI Foundry)")
        raise SystemExit(1)


def validate_dependencies() -> bool:
    """Validate that required services are available."""
    config = get_config()
    
    try:
        if config.llm_provider == "openai":
            from openai import OpenAI

            OpenAI(api_key=config.openai_api_key)
            print("✅ OpenAI API key configured")
        else:
            from openai import AzureOpenAI

            AzureOpenAI(
                api_key=config.azure_openai_api_key,
                azure_endpoint=config.azure_openai_endpoint,
                api_version=config.azure_openai_api_version,
                azure_deployment=config.azure_openai_responses_deployment,
            )
            print("✅ Azure OpenAI credentials configured")
    except Exception as e:
        provider = "OpenAI" if config.llm_provider == "openai" else "Azure OpenAI"
        print(f"❌ {provider} configuration error: {e}")
        return False

    if config.search_provider == "tavily":
        print("✅ Tavily search configured")
    elif config.search_provider == "azure_foundry_agent":
        try:
            client = AzureFoundrySearchClient(
                endpoint=config.azure_foundry_endpoint or "",
                api_key=config.azure_foundry_api_key or "",
                agent_id=config.azure_foundry_search_agent_id or "",
            )
            response = client.search(query="travel concierge health check", count=1)
            result_count = len(response.get("results", [])) if isinstance(response, dict) else 0
            print(f"✅ Azure AI Foundry Search Agent reachable ({result_count} sample result{'s' if result_count != 1 else ''})")
        except SearchProviderError as spe:
            print(f"❌ Azure AI Foundry search validation failed: {spe}")
            return False
        except Exception as e:
            print(f"❌ Azure AI Foundry search validation encountered an unexpected error: {e}")
            return False
    else:
        print(f"✅ Search provider '{config.search_provider}' configured")

    print("✅ All dependencies validated")
    return True
