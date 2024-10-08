import pathlib
from abc import abstractmethod
from enum import StrEnum
from typing import Annotated, Any, Literal

import openai
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant import config
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema

# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Helpers
#


# helper for loading an include from a text file
def load_text_include(filename) -> str:
    # get directory relative to this module
    directory = pathlib.Path(__file__).parent

    # get the file path for the prompt file
    file_path = directory / "text_includes" / filename

    # read the prompt from the file
    return file_path.read_text()


# mapping service types to an enum to use as keys in the configuration model
# to prevent errors if the service type is changed where string values were used
class ServiceType(StrEnum):
    AzureOpenAI = "azure_openai"
    OpenAI = "openai"


class ServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Service Configuration",
        json_schema_extra={
            "required": ["service_type"],
        },
    )

    service_type: Annotated[str, UISchema(widget="hidden")] = ""

    @property
    def service_type_display_name(self) -> str:
        # get from the class title
        return self.model_config.get("title") or self.service_type

    @abstractmethod
    def new_client(self, **kwargs) -> Any:
        pass


# endregion


#
# region Service Configuration
#


class AzureAuthConfigType(StrEnum):
    Identity = "azure-identity"
    ServiceKey = "api-key"


class AzureOpenAIAzureIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Annotated[Literal[AzureAuthConfigType.Identity], UISchema(widget="hidden")] = (
        AzureAuthConfigType.Identity
    )


class AzureOpenAIApiKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="API key based authentication",
        json_schema_extra={
            "required": ["azure_openai_api_key"],
        },
    )

    auth_method: Annotated[Literal[AzureAuthConfigType.ServiceKey], UISchema(widget="hidden")] = (
        AzureAuthConfigType.ServiceKey
    )

    azure_openai_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="Azure OpenAI API Key",
            description=(
                "The Azure OpenAI API key for your resource instance.  If not provided, the service default will be"
                " used."
            ),
        ),
    ] = ""


class AzureOpenAIServiceConfig(ServiceConfig):
    model_config = ConfigDict(
        title="Azure OpenAI",
        json_schema_extra={
            "required": ["azure_openai_deployment", "azure_openai_endpoint"],
        },
    )

    service_type: Annotated[Literal[ServiceType.AzureOpenAI], UISchema(widget="hidden")] = ServiceType.AzureOpenAI

    auth_config: Annotated[
        AzureOpenAIAzureIdentityAuthConfig | AzureOpenAIApiKeyAuthConfig,
        Field(
            title="Authentication Configuration",
            discriminator="auth_method",
        ),
        UISchema(hide_title=True, widget="radio"),
    ] = AzureOpenAIAzureIdentityAuthConfig()

    azure_openai_endpoint: Annotated[
        str,
        Field(
            title="Azure OpenAI Endpoint",
            description=(
                "The Azure OpenAI endpoint for your resource instance. If not provided, the service default will"
                " be used."
            ),
        ),
    ] = config.first_env_var("azure_openai_endpoint", "assistant__azure_openai_endpoint") or ""

    azure_openai_deployment: Annotated[
        str,
        Field(
            title="Azure OpenAI Deployment",
            description="The Azure OpenAI deployment to use.",
        ),
    ] = "gpt-4o"

    # set on the class to avoid re-creating the token provider for each client, which allows
    # the token provider to cache and re-use tokens
    _azure_bearer_token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )

    def new_client(self, **kwargs) -> openai.AsyncAzureOpenAI:
        api_version = kwargs.get("api_version", "2024-02-15-preview")

        match self.auth_config:
            case AzureOpenAIApiKeyAuthConfig():
                return openai.AsyncAzureOpenAI(
                    api_key=self.auth_config.azure_openai_api_key,
                    azure_deployment=self.azure_openai_deployment,
                    azure_endpoint=self.azure_openai_endpoint,
                    api_version=api_version,
                )

            case AzureOpenAIAzureIdentityAuthConfig():
                return openai.AsyncAzureOpenAI(
                    azure_ad_token_provider=AzureOpenAIServiceConfig._azure_bearer_token_provider,
                    azure_deployment=self.azure_openai_deployment,
                    azure_endpoint=self.azure_openai_endpoint,
                    api_version=api_version,
                )


class OpenAIServiceConfig(ServiceConfig):
    model_config = ConfigDict(
        title="OpenAI",
        json_schema_extra={
            "required": ["openai_api_key"],
        },
    )

    service_type: Annotated[Literal[ServiceType.OpenAI], UISchema(widget="hidden")] = ServiceType.OpenAI

    openai_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="OpenAI API Key",
            description="The API key to use for the OpenAI API.",
        ),
    ] = ""

    openai_organization_id: Annotated[
        str,
        Field(
            title="Organization ID [Optional]",
            description=(
                "The ID of the organization to use for the OpenAI API.  NOTE, this is not the same as the organization"
                " name. If you do not specify an organization ID, the default organization will be used."
            ),
        ),
        UISchema(placeholder="[optional]"),
    ] = ""


# endregion


#
# region Assistant Configuration
#


class ChatDriverConfig(BaseModel):
    instructions: Annotated[
        str,
        Field(
            title="Instructions",
            description="The prompt used to instruct the behavior of the AI assistant.",
        ),
        UISchema(widget="textarea"),
    ] = "You are a helpful assistant."

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for chat driver."),
    ] = "gpt-4o"


# the workbench app builds dynamic forms based on the configuration model and UI schema
class AssistantConfigModel(BaseModel):
    guardrails_prompt: Annotated[
        str,
        Field(
            title="Guardrails Prompt",
            description=(
                "The prompt used to inform the AI assistant about the guardrails to follow. Default value based upon"
                " recommendations from: [Microsoft OpenAI Service: System message templates]"
                "(https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/system-message"
                "#define-additional-safety-and-behavioral-guardrails)"
            ),
        ),
        UISchema(widget="textarea", enable_markdown_in_description=True),
    ] = load_text_include("guardrails_prompt.txt")

    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="The message to display when the conversation starts.",
        ),
        UISchema(widget="textarea"),
    ] = "Hello! How can I help you today?"

    chat_driver_config: Annotated[
        ChatDriverConfig,
        Field(
            title="Chat Driver Configuration",
            description="The configuration for the chat driver.",
        ),
    ] = ChatDriverConfig()

    service_config: Annotated[
        AzureOpenAIServiceConfig | OpenAIServiceConfig,
        Field(
            title="Service Configuration",
            discriminator="service_type",
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureOpenAIServiceConfig()

    content_safety_config: Annotated[
        CombinedContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety Configuration",
        ),
        UISchema(widget="radio"),
    ] = CombinedContentSafetyEvaluatorConfig()

    # add any additional configuration fields


# endregion
