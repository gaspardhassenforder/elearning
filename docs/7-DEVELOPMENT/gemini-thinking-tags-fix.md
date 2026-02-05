# Gemini Extended Thinking / Content Block Parsing Fix

## Problem Description

When using Google Gemini models (especially Flash 2.0 and Pro models) with the `podcast-creator` library, podcast generation fails with JSON parsing errors like:

```
langchain_core.exceptions.OutputParserException: Invalid json output: <think>
The user wants a podcast transcript...
```

or

```
Invalid json output: [{'type': 'text', 'text': '...'}]
```

## Root Cause

There are **two related issues** with how Gemini models return responses:

### Issue 1: Content Block Format

Gemini returns content as a **list of content blocks** instead of a plain string:

```python
# What Gemini returns:
[{'type': 'text', 'text': 'Here is the JSON: {"key": "value"}'}]

# What the parser expects:
'Here is the JSON: {"key": "value"}'
```

The `podcast-creator` library's `clean_thinking_content()` function expects a string input. When it receives a list, the Python type check at the beginning converts it using `str()`, creating an invalid string like `"[{'type': 'text', 'text': '...'}]"`.

### Issue 2: Extended Thinking Tags

Gemini models with "extended thinking" capabilities wrap their reasoning in `<think>` tags:

```
<think>
Let me analyze this request...
Here's my reasoning...
</think>
{"key": "value"}
```

The `clean_thinking_content()` function is designed to remove these tags. However, in some cases, **the model puts the entire response INCLUDING the JSON inside the `<think>` tags**:

```
<think>
Let me think about this...
Here's the JSON you requested:
{"key": "value"}
</think>
```

After removing the `<think>` tags, the cleaned content is **empty**, causing the JSON parser to fail with "Expecting value: line 1 column 1".

## Solution

The fix is implemented in `commands/podcast_commands.py` using a multi-layered monkey-patch approach:

### Layer 1: Disable Thinking at Model Creation (Primary Fix)

We patch `AIFactory.create_language()` to automatically disable extended thinking for Gemini models:

```python
def _patched_create_language(provider, model_name, config, **kwargs):
    """Disable thinking for Gemini models at model creation."""
    is_gemini = (
        (provider and provider.lower() in ['google', 'gemini']) or
        (model_name and 'gemini' in model_name.lower())
    )
    
    if is_gemini and config:
        config = config.copy()
        # Try multiple config keys (different SDK versions may use different keys)
        config['thinking_mode'] = 'disabled'
        config['extended_thinking'] = False
        config['disable_thinking'] = True
        config['thinking'] = False
        
        # Also disable in structured output config
        if 'structured' in config:
            structured = config['structured'].copy()
            structured['thinking'] = False
            structured['extended_thinking'] = False
            structured['thinking_mode'] = 'disabled'
            config['structured'] = structured
    
    return _original_create_language(provider, model_name, config, **kwargs)
```

This is the **primary fix** - preventing the model from using thinking tokens in the first place.

### Layer 2: Robust Content Extraction (Fallback)

If thinking still appears (due to SDK limitations or model behavior), we have robust parsing:

### 2. Content Block Extraction

```python
def _extract_text_from_content(content: Any) -> str:
    """Extract text from Gemini's content block format."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
            elif isinstance(block, str):
                text_parts.append(block)
        return '\n'.join(text_parts)
    else:
        return str(content)
```

### 3. Robust JSON Extraction

```python
def _strip_thinking_tags_and_extract_json(content: str) -> str:
    """
    Strip <think> tags and extract JSON, handling edge cases:
    1. Standard case: <think>...</think> followed by JSON
    2. Edge case: JSON is INSIDE the <think> tags
    3. Fallback: Find JSON pattern anywhere in content
    """
    # First, try standard cleaning
    cleaned_content = THINK_PATTERN.sub("", content).strip()
    
    if cleaned_content:
        # Try to find JSON in cleaned content
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', cleaned_content)
        if json_match:
            return json_match.group(1)
        return cleaned_content
    
    # If empty after cleaning, JSON might be inside <think> tags
    thinking_matches = THINK_PATTERN.findall(content)
    for thinking_content in thinking_matches:
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', thinking_content)
        if json_match:
            return json_match.group(1)
    
    # Last resort: find JSON anywhere
    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', content)
    if json_match:
        return json_match.group(1)
    
    return content
```

### 4. Monkey-Patch Application

The patched function is applied to **BOTH** the `podcast_core` and `podcast_nodes` modules:

```python
podcast_core.clean_thinking_content = _patched_clean_thinking_content
podcast_nodes.clean_thinking_content = _patched_clean_thinking_content
```

This is necessary because `nodes.py` imports the function directly with `from .core import clean_thinking_content`, so patching only `core` wouldn't affect the already-imported reference in `nodes`.

## Why Not Patch the Library Directly?

1. **External dependency**: `podcast-creator` is an external library installed via pip
2. **Updates would overwrite**: Any direct patches would be lost on library updates
3. **Monkey-patching is appropriate**: This is a runtime fix for provider-specific behavior

## Testing the Fix

After applying the fix, restart the worker process:

```bash
make stop-all && make start-all
```

Then try generating a podcast. The logs should show:

```
Applied podcast-creator content block handling patch to core and nodes modules
```

## Related Files

- `commands/podcast_commands.py` - Contains the monkey-patch implementation
- `podcast-creator` library (`nodes.py`, `core.py`) - External library being patched

## Alternative Solutions

If you continue to experience issues:

1. **Use a different model**: Try `gpt-4o-mini` or `gpt-4o` in your episode profile instead of Gemini
2. **Disable extended thinking**: If using Gemini models, check if there's an option to disable extended thinking mode
3. **Check model configuration**: Ensure `structured: {"type": "json"}` is being passed to the model configuration

## Error Messages Reference

| Error Message | Cause | Solution |
|--------------|-------|----------|
| `Invalid json output: <think>` | Thinking tags not stripped | Apply monkey-patch |
| `Invalid json output: [{'type': 'text'...` | Content blocks not extracted | Apply monkey-patch |
| `Expecting value: line 1 column 1` | Empty content after stripping tags (JSON was inside tags) | Use robust JSON extraction |

## Changelog

- **2026-01-22**: Initial fix for content block extraction
- **2026-01-22**: Enhanced fix to handle JSON inside `<think>` tags
