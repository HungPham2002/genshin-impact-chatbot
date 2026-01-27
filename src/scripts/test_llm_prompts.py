"""
Test prompt templates with actual Gemini LLM
Verify that prompts work correctly with the LLM
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm.llm_provider import LLMProvider
from src.rag.prompts import GenshinPrompts
from langchain_core.output_parsers import StrOutputParser


def test_basic_qa():
    """Test basic Q&A with Gemini"""
    print("\n" + "=" * 60)
    print("Test 1: Basic Q&A")
    print("=" * 60)

    # Create LLM
    llm_provider = LLMProvider.create_llm(provider="gemini")
    llm = llm_provider.get_llm()

    # Get prompt
    prompt = GenshinPrompts.get_basic_qa_prompt()

    # Create chain
    chain = prompt | llm | StrOutputParser()

    # Test data
    context = """Character: Diluc
Element: Pyro
Weapon: Claymore
Region: Mondstadt
Description: The uncrowned king of Mondstadt, Diluc is the owner of the Dawn Winery and a formidable warrior who wields a Claymore with devastating Pyro attacks."""

    question = "What element and weapon does Diluc use?"

    # Invoke
    print(f"\nQuestion: {question}")
    print(f"\nContext: {context[:100]}...")
    print(f"\nGenerating answer...")

    response = chain.invoke({
        "context": context,
        "question": question
    })

    print(f"\nAnswer:\n{response}")

    return response


def test_character_info():
    """Test detailed character info prompt"""
    print("\n" + "=" * 60)
    print("Test 2: Character Info (Detailed)")
    print("=" * 60)

    # Create LLM
    llm_provider = LLMProvider.create_llm(provider="gemini")
    llm = llm_provider.get_llm()

    # Get prompt
    prompt = GenshinPrompts.get_character_info_prompt()

    # Create chain
    chain = prompt | llm | StrOutputParser()

    # Test data
    context = """Character: Hu Tao
Element: Pyro
Weapon: Polearm
Region: Liyue
Rarity: 5-star
Role: DPS
Description: The 77th Director of the Wangsheng Funeral Parlor. She is a quirky and cheerful girl who introduces herself as the director. She wields a Polearm and uses Pyro abilities. Her Elemental Skill sacrifices HP to increase her attack damage."""

    question = "Tell me everything about Hu Tao"

    # Invoke
    print(f"\nQuestion: {question}")
    print(f"\nGenerating detailed answer...")

    response = chain.invoke({
        "context": context,
        "question": question
    })

    print(f"\nAnswer:\n{response}")

    return response


def test_chat_template():
    """Test modern chat template with ChatGoogleGenerativeAI"""
    print("\n" + "=" * 60)
    print("Test 3: Chat Template (Modern Format)")
    print("=" * 60)

    # Create LLM
    llm_provider = LLMProvider.create_llm(provider="gemini")
    llm = llm_provider.get_llm()

    # Get chat prompt template
    prompt = GenshinPrompts.get_chat_prompt_template()

    # Create chain
    chain = prompt | llm | StrOutputParser()

    # Test data
    context = """Character: Zhongli
Element: Geo
Weapon: Polearm
Region: Liyue
Description: A consultant for the Wangsheng Funeral Parlor. He is knowledgeable about Liyue's history and culture. His Elemental Skill creates a stone pillar that shields allies."""

    question = "What makes Zhongli special?"

    # Invoke
    print(f"\nQuestion: {question}")
    print(f"\nGenerating answer with chat template...")

    response = chain.invoke({
        "context": context,
        "question": question
    })

    print(f"\nAnswer:\n{response}")

    return response


def test_multiple_characters():
    """Test with multiple characters in context"""
    print("\n" + "=" * 60)
    print("Test 4: Multiple Characters Comparison")
    print("=" * 60)

    # Create LLM
    llm_provider = LLMProvider.create_llm(provider="gemini")
    llm = llm_provider.get_llm()

    # Get comparison prompt
    prompt = GenshinPrompts.get_comparison_prompt()

    # Create chain
    chain = prompt | llm | StrOutputParser()

    # Test data - format using the helper
    docs = [
        {
            'content': 'Diluc is a Pyro DPS character who uses Claymore. He has high attack damage and is great for dealing sustained Pyro damage.',
            'metadata': {'character': 'Diluc', 'element': 'Pyro'}
        },
        {
            'content': 'Hu Tao is a Pyro DPS character who uses Polearm. She sacrifices HP for increased attack and excels at single-target damage.',
            'metadata': {'character': 'Hu Tao', 'element': 'Pyro'}
        }
    ]

    context = GenshinPrompts.format_context(docs)
    question = "Compare Diluc and Hu Tao as Pyro DPS characters"

    # Invoke
    print(f"\nQuestion: {question}")
    print(f"\nGenerating comparison...")

    response = chain.invoke({
        "context": context,
        "question": question
    })

    print(f"\nAnswer:\n{response}")

    return response


def main():
    """Run all prompt tests"""
    print("=" * 60)
    print("Testing Prompts with Gemini LLM")
    print("=" * 60)

    try:
        # Run tests
        test_basic_qa()
        test_character_info()
        test_chat_template()
        test_multiple_characters()


    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()