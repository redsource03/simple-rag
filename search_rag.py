#!/usr/bin/env python3
"""
RAG Agent Search Script

This script initializes the RAG agent and calls the search_documents function
to query the GraphRAG knowledge base.

Usage:
    python search_rag.py "your search query here"
    python search_rag.py "What is the GPU in my local server?"
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rag_agent.main import search_documents, _get_driver, _get_kg_pipeline


async def main(query: str, max_results: int = 5, min_relevance: float = 0.7):
    """
    Search the RAG knowledge base for relevant information.
    
    Args:
        query: The search query to look for
        max_results: Maximum number of results to return
        min_relevance: Minimum relevance score (0.0-1.0)
    """
    print("=" * 60)
    print("RAG Agent - Document Search")
    print("=" * 60)
    print(f"\nSearching for: '{query}'")
    print(f"Max results: {max_results}")
    print(f"Min relevance: {min_relevance}")
    print("-" * 60)
    
    # Call the search_documents function
    result = await search_documents(
        query=query,
        max_results=max_results,
        min_relevance=min_relevance
    )
    
    # Display results
    if result["status"] == "success":
        print("\n✅ Search completed successfully!\n")
        
        # Display entities
        if result["entities"]:
            print(f"📄 Found {result['total_results']} matching entity/entities:\n")
            for i, entity in enumerate(result["entities"], 1):
                print(f"  {i}. {entity['name']}")
                print(f"     Description: {entity['description']}")
                print(f"     Relevance: {entity['relevance_score']:.2f}")
                print()
        else:
            print("  No entities found matching your query.")
            print()
        
        # Display communities
        if result["communities"]:
            print(f"📁 Found {len(result['communities'])} related community/ies:\n")
            for i, community in enumerate(result["communities"], 1):
                print(f"  {i}. {community['title']}")
                print(f"     Level: {community['level']}")
                print(f"     Summary: {community['summary']}")
                print(f"     Entities: {community['entity_count']}")
                print()
        
        # Display search metadata
        print("📊 Search Metadata:")
        print(f"   Query: {result['query']}")
        print(f"   Total Results: {result['total_results']}")
        print(f"   Search Time: ~{result['search_time_ms']}ms")
        
    else:
        print(f"\n❌ Search failed with error:")
        print(f"   {result.get('error', 'Unknown error')}")
    
    print("=" * 60)


if __name__ == "__main__":
    # Get query from command line arguments or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What are my local LLM server specifications?"
    
    # Parse optional arguments
    max_results = 5
    min_relevance = 0.7
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith("--max=") or arg.startswith("-m="):
            max_results = int(arg.split("=")[1])
        elif arg.startswith("--min=") or arg.startswith("-r="):
            min_relevance = float(arg.split("=")[1])
    
    # Run the search
    import asyncio
    asyncio.run(main(query, max_results, min_relevance))
