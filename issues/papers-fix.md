

[PROBLEM]

check the plan-execution-road.md and to the following


you need to rewrite code for human in loop process:

Add the following options to setup configuration

when model setup:
- ask which provider do you want to use (deepseek, antrohophic, google)
- ask type of embedding models ( explaining each one)
- ask summary_llm
- ask llm
- ask how many papers do you have ( put range option )
- ask folder of the paper ( default ~/Desktop/papers )
- ask name of settings to save

when agent setup:
- ask select tools
- ask select agent type (toolselector, simpleagent, memoryagent )
- index settings name and concurrency
- ask agent system prompot (select file from prompts folder )
- ask name of setting to save


once you create above make test for each



[RULES]
You have this rules to make the code

Focus on simplicity and clarity, avoid to develop complex structures
Use python if necessary , not java

You are an expert software architect specializing in object-oriented design with deep knowledge of SOLID principles and design patterns.
# abstraction level

Create this design at a [high/medium/low] level of abstraction:
- High-level: Focus on major components and interfaces
- Medium-level: Show primary classes with key attributes/methods
- Low-level: Include all classes with implementation details

# Multi-level abstraction request
Provide a multi-level view of this system:
1. First, a high-level architectural diagram showing major components
2. Then, a detailed class diagram for the [specific component]
3. Finally, an implementation view of [specific class] with all methods
