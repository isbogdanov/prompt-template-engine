# Copyright 2024 Igor Bogdanov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
