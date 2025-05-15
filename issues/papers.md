[PROBLEM]
please continue with the code generation acording to :

please create the python code according to the following requirements:
- see all requirements on CONTEXT section


[CONTEXT]

# Initial Question Submission Phase - Classes and Files

Based on your requirements, I'll design a system that involves human-in-the-loop interaction where the LLM (Claude) helps refine research questions using the metaprompt frameworks you provided (PICO/PICOT, PEO, and PCC). Here are the relevant classes and files for the initial question submission phase:

## Main Classes Involved

1. **ResearchAgent**
   - Main controller that orchestrates the question refinement process
   - Manages communication between the user and LLM
   - Tracks the state of the question refinement process

2. **QuestionProcessor**
   - Analyzes initial questions
   - Determines which framework (PICO/PICOT, PEO, or PCC) is most appropriate
   - Identifies ambiguities or areas needing clarification

3. **FrameworkSelector**
   - Evaluates the research question type
   - Recommends the most suitable framework based on question characteristics
   - Loads appropriate metaprompt content

4. **ClarificationManager**
   - Generates clarification questions based on the selected framework
   - Tracks user responses to clarifications
   - Manages the multi-turn conversation for question refinement

5. **MetapromptLoader**
   - Loads and processes the metaprompt frameworks
   - Extracts relevant sections for the current refinement step
   - Provides template structures for different question types

6. **LLMInterface**
   - Manages communication with Claude
   - Formats prompts according to Claude's requirements
   - Processes responses from the LLM

7. **UserInteractionManager**
   - Handles user input and output
   - Presents clarification questions to the user
   - Displays intermediate and final refined questions

## File Structure

1. `main.py`
   - Entry point for the application
   - Initializes the system components
   - Creates the ResearchAgent instance

2. `research_agent.py`
   - Contains the ResearchAgent class
   - Orchestrates the overall question refinement process

3. `question_processor.py`
   - Contains the QuestionProcessor class
   - Implements question analysis functionality

4. `framework_selector.py`
   - Contains the FrameworkSelector class
   - Logic for choosing between PICO/PICOT, PEO, and PCC frameworks

5. `clarification_manager.py`
   - Contains the ClarificationManager class
   - Manages the iterative question refinement process

6. `metaprompt_loader.py`
   - Contains the MetapromptLoader class
   - Handles loading and processing of metaprompt files

7. `llm_interface.py`
   - Contains the LLMInterface class
   - Integrates with LangChain and Claude API

8. `user_interaction.py`
   - Contains the UserInteractionManager class
   - Manages user interface elements and interactions

9. `config.py`
   - Contains configuration parameters
   - API keys, model settings, and system parameters

10. `data/metaprompts/`
    - Directory containing the metaprompt files
    - Includes PICO_PICOT.md, PEO.md, and PCC.md

## Process Flow for Initial Question Submission

1. **User Submits Initial Question**
   - User enters an initial research question via UserInteractionManager
   - ResearchAgent receives this question

2. **Question Analysis**
   - ResearchAgent passes the question to QuestionProcessor
   - QuestionProcessor analyzes the question structure and content
   - FrameworkSelector recommends the most appropriate framework

3. **Metaprompt Loading**
   - MetapromptLoader retrieves the selected framework
   - Prepares relevant sections for the current refinement stage

4. **Clarification Generation**
   - ClarificationManager identifies areas needing clarification
   - Uses the selected framework to create structured clarification questions
   - LLMInterface communicates with Claude to generate appropriate questions

5. **Human Interaction**
   - UserInteractionManager presents clarification questions to the user
   - User provides responses to clarifications
   - ClarificationManager collects and processes these responses

6. **Iterative Refinement**
   - The process repeats for the specified number of iterations
   - Each iteration refines the question further using framework guidance
   - LLM progressively incorporates user feedback to improve the question

7. **Final Question Generation**
   - After the final iteration, ResearchAgent generates the refined question
   - The final question is structured according to the selected framework
   - UserInteractionManager presents this to the user for approval

This structure provides a clean, modular approach to implementing the initial question submission phase, with clear separation of responsibilities between classes and files. It's designed to integrate with LangChain for LLM interactions while maintaining a human-in-the-loop workflow.
