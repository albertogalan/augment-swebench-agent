[PROBLEM]


fix the issue when run this command:

python -m src.main ask


I you need context as a reference, please check the following:


[CONTEXT]

# How to Check if a Question is Well-Formulated in PaperQA2

When using PaperQA2, ensuring your question is well-formulated is crucial for getting accurate and relevant answers. There are several approaches you can take to verify and improve your question quality.

## 1. Start with a Simple Quality Check

PaperQA2 doesn't have a built-in "question quality checker," but you can use several techniques to assess and improve your questions:

```python
from paperqa import Settings, ask

# First, test your question's clarity
test_question = "What are the key factors in bispecific antibodies?"
preliminary_response = ask(
    test_question,
    settings=Settings(
        # Use a faster/cheaper model for this test
        llm="gpt-4o-mini",
        summary_llm="gpt-4o-mini",
        paper_directory="my_papers"
    )
)

# Check if the answer contains phrases indicating query issues
answer_text = preliminary_response.session.answer
if "I cannot answer" in answer_text or "insufficient information" in answer_text:
    print("Question may need refinement - insufficient relevant information found")
```

## 2. Check the Evidence Quality

Examining the quality and relevance of retrieved evidence can indicate if your question is well-formulated:

```python
from paperqa import Docs, Settings

async def check_question_quality(question):
    docs = Docs()
    # Add your documents
    await docs.aadd("your_document.pdf")

    # Get evidence without generating an answer
    evidence_response = await docs.aget_evidence(question)

    # Check the relevance scores of retrieved contexts
    relevant_count = sum(1 for ctx in evidence_response.contexts if ctx.score > 5)
    total_count = len(evidence_response.contexts)

    if relevant_count / total_count < 0.5:
        print(f"Warning: Only {relevant_count}/{total_count} pieces of evidence seem relevant")
        print("Consider reformulating your question to be more specific or aligned with your documents")

    return evidence_response.contexts
```

## 3. Use Pre-Query Validation

You can implement a pre-query validation step using an LLM to assess question quality:

```python
from paperqa import Settings
from lmi import LiteLLMModel, Message

async def validate_question(question, domain="scientific research"):
    """Validate a question before sending it to the full PaperQA pipeline"""
    llm = Settings().get_llm()

    validation_prompt = f"""
    Analyze the following question for clarity, specificity, and relevance to {domain}:

    Question: "{question}"

    Please evaluate:
    1. Clarity: Is the question clear and unambiguous?
    2. Specificity: Is it specific enough to yield meaningful answers?
    3. Relevance: Is it relevant to {domain}?
    4. Assumptions: Does it contain problematic assumptions?

    Then provide:
    - An assessment (Good/Needs improvement)
    - Specific suggestions for improvement if needed
    - A reframed version of the question if helpful
    """

    result = await llm.call_single(messages=[Message(content=validation_prompt)])
    return result.text

# Example usage
question = "What does AI do for chemistry?"
validation_result = await validate_question(question, domain="chemistry and AI applications")
print(validation_result)

# Only proceed with the actual query if the question seems well-formed
if "Good" in validation_result:
    # Run the actual query...
    pass
```

## 4. Check For Adequate Document Coverage

Make sure your corpus contains relevant documents for your question:

```python
from paperqa import Settings
from paperqa.agents.search import get_directory_index

async def check_document_coverage(question, paper_directory="my_papers"):
    settings = Settings(paper_directory=paper_directory)
    index = await get_directory_index(settings=settings)

    # Search for relevant documents
    results = await index.query(query=question, top_n=5)

    if not results:
        print("Warning: No relevant documents found for this question.")
        print("Consider adding more specific documents to your paper directory.")
        return False

    # Check relevance scores
    if results[0].score < 10:  # Threshold may need adjustment
        print(f"Warning: Best document match has low relevance score ({results[0].score}).")
        print("Question might not align well with your document collection.")

    return True
```

## 5. Iterative Question Refinement

Sometimes it's helpful to iterate and refine your question based on initial results:

```python
from paperqa import Settings, ask

initial_question = "AI in science?"
refined_question = "What specific applications of artificial intelligence have improved prediction accuracy in computational chemistry since 2020?"

# Compare responses from both questions
initial_response = ask(initial_question, settings=Settings(paper_directory="my_papers"))
refined_response = ask(refined_question, settings=Settings(paper_directory="my_papers"))

# Check which gets more specific, higher-quality evidence
print(f"Initial question retrieved {len(initial_response.session.contexts)} contexts")
print(f"Refined question retrieved {len(refined_response.session.contexts)} contexts")

# Examine quality of citations used
initial_citations = len(initial_response.session.used_contexts)
refined_citations = len(refined_response.session.used_contexts)

print(f"Initial question used {initial_citations} citations in its answer")
print(f"Refined question used {refined_citations} citations in its answer")
```

By implementing these approaches, you can ensure your questions are well-formulated and likely to receive high-quality answers from PaperQA2, maximizing the value you get from your document collection.



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
