"""Query templates for common patterns across languages."""

from typing import Dict, List, Optional

# Query templates for different languages and patterns
QUERY_TEMPLATES = {
    "python": {
        "functions": "(function_definition name: (identifier) @function.name) @function.def",
        "classes": "(class_definition name: (identifier) @class.name) @class.def",
        "imports": [
            "(import_statement) @import",
            "(import_from_statement) @import"
        ],
        "methods": "(class_definition body: (block (function_definition name: (identifier) @method.name) @method.def))",
        "variables": "(assignment left: (identifier) @variable.name) @variable.def",
        "decorators": "(decorator) @decorator",
        "docstrings": "(function_definition body: (block (expression_statement (string) @docstring)))",
        "comments": "(comment) @comment",
    },
    "javascript": {
        "functions": [
            "(function_declaration name: (identifier) @function.name) @function.def",
            "(function name: (identifier) @function.name) @function.def",
            "(arrow_function) @function.def",
            "(method_definition key: (property_identifier) @function.name) @function.def"
        ],
        "classes": "(class_declaration name: (identifier) @class.name) @class.def",
        "imports": [
            "(import_statement) @import",
            "(import_clause) @import"
        ],
        "variables": [
            "(variable_declarator name: (identifier) @variable.name) @variable.def",
            "(lexical_declaration) @variable.def"
        ],
        "exports": "(export_statement) @export",
        "comments": [
            "(comment) @comment",
            "(jsx_comment) @comment"
        ],
    },
    "typescript": {
        "functions": [
            "(function_declaration name: (identifier) @function.name) @function.def",
            "(function_signature name: (identifier) @function.name) @function.sig",
            "(arrow_function) @function.def",
            "(method_definition key: (property_identifier) @function.name) @function.def",
            "(method_signature key: (property_identifier) @function.name) @function.sig"
        ],
        "classes": "(class_declaration name: (type_identifier) @class.name) @class.def",
        "interfaces": "(interface_declaration name: (type_identifier) @interface.name) @interface.def",
        "types": "(type_alias_declaration name: (type_identifier) @type.name) @type.def",
        "imports": [
            "(import_statement) @import",
            "(import_clause) @import"
        ],
        "enums": "(enum_declaration name: (identifier) @enum.name) @enum.def",
    },
    "go": {
        "functions": "(function_declaration name: (identifier) @function.name) @function.def",
        "methods": "(method_declaration name: (field_identifier) @method.name) @method.def",
        "structs": "(type_declaration (type_spec name: (type_identifier) @struct.name type: (struct_type))) @struct.def",
        "interfaces": "(type_declaration (type_spec name: (type_identifier) @interface.name type: (interface_type))) @interface.def",
        "imports": "(import_declaration) @import",
        "variables": [
            "(var_declaration) @variable.def",
            "(short_var_declaration) @variable.def"
        ],
    },
    "rust": {
        "functions": "(function_item name: (identifier) @function.name) @function.def",
        "structs": "(struct_item name: (type_identifier) @struct.name) @struct.def",
        "enums": "(enum_item name: (type_identifier) @enum.name) @enum.def",
        "traits": "(trait_item name: (type_identifier) @trait.name) @trait.def",
        "impl_blocks": "(impl_item) @impl",
        "imports": "(use_declaration) @import",
        "macros": "(macro_definition name: (identifier) @macro.name) @macro.def",
    },
    "c": {
        "functions": "(function_definition declarator: (function_declarator declarator: (identifier) @function.name)) @function.def",
        "structs": "(struct_specifier name: (type_identifier) @struct.name) @struct.def",
        "typedefs": "(type_definition declarator: (type_identifier) @typedef.name) @typedef.def",
        "includes": "(preproc_include) @include",
        "macros": "(preproc_function_def name: (identifier) @macro.name) @macro.def",
        "variables": "(declaration declarator: (identifier) @variable.name) @variable.def",
    },
    "cpp": {
        "functions": "(function_definition declarator: (function_declarator declarator: (identifier) @function.name)) @function.def",
        "classes": "(class_specifier name: (type_identifier) @class.name) @class.def",
        "structs": "(struct_specifier name: (type_identifier) @struct.name) @struct.def",
        "methods": "(function_definition declarator: (function_declarator declarator: (field_identifier) @method.name)) @method.def",
        "namespaces": "(namespace_definition name: (identifier) @namespace.name) @namespace.def",
        "templates": "(template_declaration) @template",
        "includes": "(preproc_include) @include",
    },
    "java": {
        "classes": "(class_declaration name: (identifier) @class.name) @class.def",
        "interfaces": "(interface_declaration name: (identifier) @interface.name) @interface.def",
        "methods": "(method_declaration name: (identifier) @method.name) @method.def",
        "fields": "(field_declaration declarator: (variable_declarator name: (identifier) @field.name)) @field.def",
        "imports": "(import_declaration) @import",
        "packages": "(package_declaration) @package",
        "annotations": "(annotation) @annotation",
    },
}


def get_query_template(language: str, pattern_type: str) -> Optional[str]:
    """Get a query template for a specific language and pattern type."""
    if language not in QUERY_TEMPLATES:
        return None
    
    templates = QUERY_TEMPLATES[language]
    if pattern_type not in templates:
        return None
    
    template = templates[pattern_type]
    
    # If it's a list, join them with alternation
    if isinstance(template, list):
        return " ".join(template)
    
    return template


def list_available_templates(language: Optional[str] = None) -> Dict[str, List[str]]:
    """List available query templates."""
    if language:
        if language in QUERY_TEMPLATES:
            return {language: list(QUERY_TEMPLATES[language].keys())}
        return {}
    
    return {lang: list(patterns.keys()) for lang, patterns in QUERY_TEMPLATES.items()}


def build_combined_query(language: str, pattern_types: List[str]) -> Optional[str]:
    """Build a combined query from multiple pattern types."""
    queries = []
    for pattern_type in pattern_types:
        template = get_query_template(language, pattern_type)
        if template:
            queries.append(template)
    
    if not queries:
        return None
    
    return " ".join(queries)