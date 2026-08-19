from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CodePatternDefinition:
    identifier: str
    category: str
    description: str
    pattern: re.Pattern[str]
    extensions: tuple[str, ...]


def _compile(regex: str) -> re.Pattern[str]:
    return re.compile(regex, re.IGNORECASE)


ALL_CODE_EXTENSIONS: tuple[str, ...] = (
    ".py",
    ".java",
    ".kt",
    ".js",
    ".ts",
    ".tsx",
    ".go",
    ".cs",
)


CODE_PATTERN_REGISTRY: tuple[CodePatternDefinition, ...] = (
    # LLM provider usage patterns
    CodePatternDefinition(
        identifier="openai_client_import",
        category="llm",
        description="OpenAI SDK client import detected",
        pattern=_compile(
            r"\bfrom\s+openai\s+import\s+(OpenAI|AsyncOpenAI|AzureOpenAI|AsyncAzureOpenAI)\b"
        ),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="openai_client_construct",
        category="llm",
        description="OpenAI SDK client construction detected",
        pattern=_compile(r"\b(OpenAI|AsyncOpenAI|AzureOpenAI|AsyncAzureOpenAI)\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="langchain_chat_provider_construct",
        category="llm",
        description="LangChain provider chat-model construction detected",
        pattern=_compile(r"\b(ChatOpenAI|AzureChatOpenAI|ChatAnthropic|ChatBedrock|ChatVertexAI)\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="anthropic_client_construct",
        category="llm",
        description="Anthropic SDK client construction detected",
        pattern=_compile(r"\b(Anthropic|AsyncAnthropic)\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="llm_provider_api_call",
        category="llm",
        description="LLM provider API invocation detected",
        pattern=_compile(
            r"\b(chat\.completions\.create|responses\.create|messages\.create|generate_content|invoke_model|embeddings\.create)\s*\("
        ),
        extensions=(".py", ".js", ".ts", ".tsx"),
    ),
    CodePatternDefinition(
        identifier="ai_gateway_usage",
        category="llm_context",
        description="Internal AI gateway/client abstraction usage detected",
        pattern=_compile(r"\b(model_gateway|llm_gateway|ai_client|inference_client|generation_client)\b"),
        extensions=(".py", ".js", ".ts", ".tsx", ".java", ".kt", ".go", ".cs"),
    ),
    CodePatternDefinition(
        identifier="model_config_usage",
        category="llm_context",
        description="Model configuration parameters detected",
        pattern=_compile(r"\b(model\s*=|model_name\s*=|deployment_name\s*=|temperature\s*=|embedding_model\s*=|llm\s*=)"),
        extensions=(".py", ".js", ".ts", ".tsx"),
    ),
    CodePatternDefinition(
        identifier="prompt_template_usage",
        category="llm_context",
        description="Prompt template artifacts detected in code",
        pattern=_compile(r"\b(system_prompt|prompt_template|few_shot)\b"),
        extensions=(".py", ".js", ".ts", ".tsx", ".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="vector_retrieval_usage",
        category="llm_context",
        description="Vector retrieval related construct detected",
        pattern=_compile(r"\b(vectorstore|vector_store|faiss|chroma|pinecone|weaviate|milvus|pgvector|embedding)\b"),
        extensions=(".py", ".js", ".ts", ".tsx", ".java", ".kt", ".go"),
    ),

    # Retry and resilience
    CodePatternDefinition(
        identifier="retry_annotation",
        category="retry",
        description="Retry annotation usage detected",
        pattern=_compile(r"@\s*Retry(?:able)?\b"),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="retry_template",
        category="retry",
        description="Spring RetryTemplate usage detected",
        pattern=_compile(r"\bRetryTemplate\b"),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="resilience4j_retry",
        category="retry",
        description="Resilience4j retry API usage detected",
        pattern=_compile(r"io\.github\.resilience4j\.retry|\bRetry\.decorate\w*\s*\("),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="python_tenacity_retry",
        category="retry",
        description="Python tenacity retry decorator detected",
        pattern=_compile(r"@\s*(?:tenacity\.)?retry\s*\("),
        extensions=(".py",),
    ),
    # Input validation
    CodePatternDefinition(
        identifier="java_validation_annotation",
        category="input_validation",
        description="Java/Kotlin validation annotation detected",
        pattern=_compile(r"@\s*(Valid|Validated|NotNull|NotBlank)\b"),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="pydantic_model_validation",
        category="input_validation",
        description="Pydantic model validation construct detected",
        pattern=_compile(r"\bBaseModel\b|\bField\s*\(|\bfield_validator\s*\(|\bmodel_validator\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="schema_validation_library",
        category="input_validation",
        description="Schema-validation library usage detected",
        pattern=_compile(r"\bz\.object\s*\(|\bJoi\.object\s*\(|\bschema\.validate\s*\("),
        extensions=(".js", ".ts", ".tsx"),
    ),
    # Observability and tracing
    CodePatternDefinition(
        identifier="otel_tracing",
        category="observability",
        description="OpenTelemetry tracing usage detected",
        pattern=_compile(
            r"\bOpenTelemetry\b|\bio\.opentelemetry\b|\bGlobalOpenTelemetry\b|"
            r"\bstart_as_current_span\s*\(|\bstartSpan\s*\(|\bgetTracer\s*\("
        ),
        extensions=ALL_CODE_EXTENSIONS,
    ),
    # Fallback constructs
    CodePatternDefinition(
        identifier="circuit_breaker_fallback",
        category="fallback",
        description="Circuit-breaker fallback construct detected",
        pattern=_compile(r"\bfallbackMethod\s*=|@\s*CircuitBreaker\b"),
        extensions=(".java", ".kt"),
    ),
    # API implementation patterns
    CodePatternDefinition(
        identifier="spring_rest_controller",
        category="api",
        description="Spring REST controller annotation detected",
        pattern=_compile(r"@\s*RestController\b"),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="spring_request_mapping",
        category="api",
        description="Spring request mapping annotation detected",
        pattern=_compile(r"@\s*(RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping)\b"),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="fastapi_app_init",
        category="api",
        description="FastAPI application initialization detected",
        pattern=_compile(r"\bFastAPI\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="fastapi_route_decorator",
        category="api",
        description="FastAPI route decorator detected",
        pattern=_compile(r"@\s*(app|router)\.(get|post|put|delete|patch)\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="flask_route_decorator",
        category="api",
        description="Flask route decorator detected",
        pattern=_compile(r"@\s*app\.route\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="express_app_init",
        category="api",
        description="Express app initialization detected",
        pattern=_compile(r"\bexpress\s*\("),
        extensions=(".js", ".ts", ".tsx"),
    ),
    CodePatternDefinition(
        identifier="express_router_method",
        category="api",
        description="Express router/app HTTP method registration detected",
        pattern=_compile(r"\b(?:app|router)\.(get|post|put|delete|patch)\s*\("),
        extensions=(".js", ".ts", ".tsx"),
    ),
    # Agent orchestration patterns
    CodePatternDefinition(
        identifier="langgraph_state_graph",
        category="agents",
        description="LangGraph state-graph construction detected",
        pattern=_compile(r"\bStateGraph\b|\bcreate_react_agent\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="langchain_agent_executor",
        category="agents",
        description="LangChain AgentExecutor usage detected",
        pattern=_compile(r"\bAgentExecutor\b|\binitialize_agent\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="crewai_agent_construct",
        category="agents",
        description="CrewAI agent construct detected",
        pattern=_compile(r"\bfrom\s+crewai\s+import\s+(Agent|Crew)|\bcrewai\.Agent\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="autogen_agent_construct",
        category="agents",
        description="AutoGen agent API usage detected",
        pattern=_compile(r"\b(AssistantAgent|UserProxyAgent|ConversableAgent)\s*\("),
        extensions=(".py",),
    ),
    # RAG implementation patterns
    CodePatternDefinition(
        identifier="rag_embedding_api_call",
        category="rag",
        description="Embedding generation API call detected",
        pattern=_compile(r"\bembeddings\.(create|embed_query|embed_documents)\s*\("),
        extensions=(".py", ".js", ".ts", ".tsx"),
    ),
    CodePatternDefinition(
        identifier="rag_vector_query_call",
        category="rag",
        description="Vector similarity query call detected",
        pattern=_compile(r"\b(query_points|similarity_search|collection\.query)\s*\("),
        extensions=(".py", ".js", ".ts", ".tsx"),
    ),
    CodePatternDefinition(
        identifier="rag_retriever_chain",
        category="rag",
        description="Retriever-chain orchestration detected",
        pattern=_compile(r"\b(as_retriever|create_retrieval_chain|RetrievalQA\.from_chain_type)\s*\("),
        extensions=(".py",),
    ),
)
