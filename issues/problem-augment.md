[GOAL]
need to integrate deepseek llm model on cli.py


[PROBLEM]

when I run python cli.py --llm deepseek --problem-statement "xxx"


DeepSeek API error: HTTP Error 400: {"error":{"message":"Model Not Exist","type":"invalid_request_error","param":null,"code":"invalid_request_error"}}
Using mock response for testing
Calling tool bash with input:
 - command: echo Hello, world!
Tool output:
Hello, world!


[CONTEXT]
you need to know that the script is a loop, the agent is trying to fix an issue , so after 5 seconds or less you need to Cancel with Control-C and check the output


[DOCUMENTATION ABOUT AUGMENT SWE SERVER]
