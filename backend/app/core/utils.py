import json

import tiktoken


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(model)
    return len(encoding.encode(text))


def count_tokens_in_dict(data: dict, model: str = "cl100k_base") -> int:
    return count_tokens(json.dumps(data), model)
