"""
Prompt templates for Genshin Impact Chatbot
Custom prompts optimized for character information retrieval
"""

from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
from typing import List, Dict


class GenshinPrompts:
    """Collection of prompt templates for Genshin chatbot"""

    # System message - defines chatbot personality and behavior
    SYSTEM_MESSAGE = """You are a knowledgeable and friendly Genshin Impact assistant.

Your role:
- Help players with information about Genshin Impact characters
- Provide accurate, detailed information based on the context provided
- Be enthusiastic and friendly, but concise
- If you don't know something or it's not in the context, admit it honestly

Guidelines:
- Always base your answers on the provided CONTEXT
- Cite character names and specific details when relevant
- Keep responses clear and well-structured
- Use markdown formatting when helpful (lists, bold, etc.)
- If asked about game mechanics not in context, politely say you specialize in character information

Context Language: The context may contain information in English or mixed languages. Answer in the user's question language when possible."""

    # Basic RAG template - simple Q&A
    BASIC_QA_TEMPLATE = """Use the following context about Genshin Impact characters to answer the question.

CONTEXT:
{context}

QUESTION: {question}

ANSWER (be helpful and specific):"""

    # Detailed character info template
    CHARACTER_INFO_TEMPLATE = """You are a Genshin Impact expert. Use the provided context to give detailed character information.

CONTEXT:
{context}

USER QUESTION: {question}

Please provide a comprehensive answer covering:
- Character name and basic info (element, weapon, region if mentioned)
- Relevant details from the context
- Any specific information requested

ANSWER:"""

    # Comparison template - for comparing characters
    COMPARISON_TEMPLATE = """You are comparing Genshin Impact characters based on the provided context.

CONTEXT:
{context}

COMPARISON QUESTION: {question}

Analyze the context and provide:
1. Key similarities between the characters
2. Main differences
3. Specific stats or abilities if mentioned

COMPARISON:"""

    # Recommendation template
    RECOMMENDATION_TEMPLATE = """You are helping a Genshin Impact player choose characters based on their needs.

CONTEXT (Available character information):
{context}

PLAYER'S REQUEST: {question}

Based on the context, provide:
1. Recommended character(s) that fit the request
2. Why they are suitable
3. Key strengths for the player's needs

RECOMMENDATION:"""

    # Chat template with history
    CHAT_TEMPLATE = """You are a friendly Genshin Impact assistant having a conversation.

CONTEXT (Character information):
{context}

CONVERSATION HISTORY:
{chat_history}

CURRENT QUESTION: {question}

Respond naturally, referring to previous messages if relevant.

RESPONSE:"""

    @staticmethod
    def get_basic_qa_prompt() -> PromptTemplate:
        """Get basic Q&A prompt template"""
        return PromptTemplate(
            template=GenshinPrompts.BASIC_QA_TEMPLATE,
            input_variables=["context", "question"]
        )

    @staticmethod
    def get_character_info_prompt() -> PromptTemplate:
        """Get detailed character info prompt"""
        return PromptTemplate(
            template=GenshinPrompts.CHARACTER_INFO_TEMPLATE,
            input_variables=["context", "question"]
        )

    @staticmethod
    def get_comparison_prompt() -> PromptTemplate:
        """Get character comparison prompt"""
        return PromptTemplate(
            template=GenshinPrompts.COMPARISON_TEMPLATE,
            input_variables=["context", "question"]
        )

    @staticmethod
    def get_recommendation_prompt() -> PromptTemplate:
        """Get character recommendation prompt"""
        return PromptTemplate(
            template=GenshinPrompts.RECOMMENDATION_TEMPLATE,
            input_variables=["context", "question"]
        )

    @staticmethod
    def get_chat_prompt() -> PromptTemplate:
        """Get conversational prompt with history"""
        return PromptTemplate(
            template=GenshinPrompts.CHAT_TEMPLATE,
            input_variables=["context", "question", "chat_history"]
        )

    @staticmethod
    def get_chat_prompt_template() -> ChatPromptTemplate:
        """
        Get ChatPromptTemplate for modern LangChain chains
        This uses ChatGoogleGenerativeAI format
        """
        system_template = GenshinPrompts.SYSTEM_MESSAGE

        human_template = """Context from knowledge base:
{context}

Question: {question}"""

        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ]

        return ChatPromptTemplate.from_messages(messages)

    @staticmethod
    def format_context(documents: List[Dict]) -> str:
        """
        Format retrieved documents into context string

        Args:
            documents: List of retrieved documents with 'content' and 'metadata'

        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant information found."

        context_parts = []

        for i, doc in enumerate(documents, 1):
            # Extract content
            content = doc.get('page_content', doc.get('content', str(doc)))

            # Extract metadata if available
            metadata = doc.get('metadata', {})
            character = metadata.get('character', 'Unknown')

            # Format each document
            context_parts.append(f"--- Source {i}: {character} ---\n{content}\n")

        return "\n".join(context_parts)

    @staticmethod
    def format_chat_history(history: List[tuple]) -> str:
        """
        Format chat history for context

        Args:
            history: List of (user_message, bot_response) tuples

        Returns:
            Formatted chat history string
        """
        if not history:
            return "No previous conversation."

        formatted = []
        for user_msg, bot_msg in history[-3:]:  # Last 3 exchanges
            formatted.append(f"User: {user_msg}")
            formatted.append(f"Assistant: {bot_msg}")

        return "\n".join(formatted)


# Test and demonstration
if __name__ == "__main__":
    print("=" * 60)
    print("🎯 Genshin Prompts - Template Showcase")
    print("=" * 60)

    # Test 1: Basic QA Prompt
    print("\n[1] Basic Q&A Prompt:")
    print("-" * 60)
    basic_prompt = GenshinPrompts.get_basic_qa_prompt()

    sample_context = """Character: Diluc
Element: Pyro
Weapon: Claymore
Region: Mondstadt
Description: The uncrowned king of Mondstadt, Diluc is a wealthy winery owner and a powerful warrior."""

    formatted = basic_prompt.format(
        context=sample_context,
        question="Who is Diluc?"
    )
    print(formatted)

    # Test 2: Character Info Prompt
    print("\n[2] Character Info Prompt:")
    print("-" * 60)
    char_prompt = GenshinPrompts.get_character_info_prompt()

    formatted = char_prompt.format(
        context=sample_context,
        question="Tell me about Diluc's element and weapon"
    )
    print(formatted[:300] + "...")

    # Test 3: Chat Prompt Template (ChatGoogleGenerativeAI compatible)
    print("\n[3] Chat Prompt Template (for ChatGoogleGenerativeAI):")
    print("-" * 60)
    chat_prompt = GenshinPrompts.get_chat_prompt_template()

    messages = chat_prompt.format_messages(
        context=sample_context,
        question="What element does Diluc use?"
    )

    print(f"Number of messages: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"\nMessage {i + 1} ({type(msg).__name__}):")
        print(msg.content[:200] + "..." if len(msg.content) > 200 else msg.content)

    # Test 4: Context Formatting
    print("\n[4] Context Formatting:")
    print("-" * 60)

    sample_docs = [
        {
            'content': 'Diluc is a Pyro character who uses Claymore.',
            'metadata': {'character': 'Diluc', 'element': 'Pyro'}
        },
        {
            'content': 'Hu Tao is a Pyro character who uses Polearm.',
            'metadata': {'character': 'Hu Tao', 'element': 'Pyro'}
        }
    ]

    formatted_context = GenshinPrompts.format_context(sample_docs)
    print(formatted_context)

    # Test 5: Available prompt types
    print("\n[5] Available Prompt Templates:")
    print("-" * 60)
    prompts = [
        "Basic Q&A",
        "Character Info",
        "Comparison",
        "Recommendation",
        "Chat with History",
        "Chat Template (Modern)"
    ]

    for i, prompt_name in enumerate(prompts, 1):
        print(f"  {i}. {prompt_name}")