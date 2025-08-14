class PromptEngineError(Exception):
    # Base exception for all errors raised by the prompt engine.
    pass


class TemplateNotFoundError(PromptEngineError):
    # Raised when a specified template file cannot be found.
    pass


class TemplateParsingError(PromptEngineError):
    # Raised when a template file has invalid syntax.
    pass


class MissingPlaceholderError(PromptEngineError):
    # Raised when the build method is called without providing a value for a required placeholder.
    pass
