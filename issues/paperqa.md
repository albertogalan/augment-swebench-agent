[ADVICE]
[GOAL]
execute the python script without errrors
[PROBLEM]
python pdf_rag_system.py --pdf_dir "/Users/agalan/Downloads/yanipapers/" --query "what are the main research questions on these pappers" --model "claude-3-opus-20240229"  --embedding_model "all-MiniLM-L6-v2"

2025-05-04 00:07:31,998 - httpx - INFO - HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 429 Too Many Requests"
00:07:32 - LiteLLM Router:INFO: router.py:1095 - litellm.acompletion(model=claude-3-5-sonnet-20240620) Exception litellm.RateLimitError: AnthropicException - {"type":"error","error":{"type":"rate_limit_error","message":"This request would exceed the rate limit for your organization (c73989f9-60bd-43d1-b427-c4f24518c4c4) of 8,000 output tokens per minute. For details, refer to: https://docs.anthropic.com/en/api/rate-limits. You can see the response headers for current usage. Please reduce the prompt length or the maximum tokens requested, or try again later. You may also contact sales at https://www.anthropic.com/contact-sales to discuss your options for a rate limit increase."}}
2025-05-04 00:07:32,016 - LiteLLM Router - INFO - litellm.acompletion(model=claude-3-5-sonnet-20240620) Exception litellm.RateLimitError: AnthropicException - {"type":"error","error":{"type":"rate_limit_error","message":"This request would exceed the rate limit for your organization (c73989f9-60bd-43d1-b427-c4f24518c4c4) of 8,000 output tokens per minute. For details, refer to: https://docs.anthropic.com/en/api/rate-limits. You can see the response headers for current usage. Please reduce the prompt length or the maximum tokens requested, or try again later. You may also contact sales at https://www.anthropic.com/contact-sales to discuss your options for a rate limit increase."}}
00:07:32 - LiteLLM Router:INFO: router.py:3557 - Retrying request with num_retries: 3
2025-05-04 00:07:32,016 - LiteLLM Router - INFO - Retrying request with num_retries: 3
^CTraceback (most recent call last):
  File "/Users/agalan/data/src/wk/papers/venv/lib/python3.12/site-packages/litellm/llms/anthropic/chat/handler.py", line 234, in acompletion_function
    response = await async_handler.post(
               ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/agalan/data/src/wk/papers/venv/lib/python3.12/site-packages/litellm/litellm_core_utils/logging_utils.py", line 135, in async_wrapper
    result = await func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/agalan/data/src/wk/papers/venv/lib/python3.12/site-packages/litellm/llms/custom_httpx/http_handler.py", line 256, in post
    raise e
  File "/Users/agalan/data/src/wk/papers/venv/lib/python3.12/site-packages/litellm/llms/custom_httpx/http_handler.py", line 212, in post
    response.raise_for_status()
  File "/Users/agalan/data/src/wk/papers/venv/lib/python3.12/site-packages/httpx/_models.py", line 829, in raise_for_status
    raise HTTPStatusError(message, request=request, response=self)
httpx.HTTPStatusError: Client error '429 Too Many Requests' for url 'https://api.anthropic.com/v1/messages'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429

During handling of the above exception, another exception occurred:

[CONTEXT]
[DOCUMENTATION ABOUT SWE-REX]
