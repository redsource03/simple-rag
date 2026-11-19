#!/usr/bin/env python3
"""
RAG Agent Save Script

This script initializes the RAG agent and calls the add_document function
to save documents to the GraphRAG knowledge base.

Usage:
    python save_rag.py --title="My Title" --content="Document content here"
    python save_rag.py --title="Server Specs" --content-file=server-specs.txt
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rag_agent.main import add_document


async def main(
    content: str,
    title: str,
    source: Optional[str] = None,
    tags: Optional[list] = None,
    category: Optional[str] = None
):
    """
    Save a document to the RAG knowledge base.
    
    Args:
        content: The document content to save
        title: A descriptive title for the document
        source: Optional source (URL, file path, author)
        tags: Optional list of tags for categorization
        category: Optional category name
    """
    print("=" * 60)
    print("RAG Agent - Save Document")
    print("=" * 60)
    print(f"\n📝 Saving document: '{title}'")
    
    if source:
        print(f"📌 Source: {source}")
    
    if tags:
        print(f"🏷️  Tags: {', '.join(tags)}")
    
    if category:
        print(f"📁 Category: {category}")
    
    print(f"\n📄 Content preview ({len(content)} characters):")
    print("-" * 60)
    preview = content[:200] + "..." if len(content) > 200 else content
    print(preview)
    print("-" * 60)
    
    # Call the add_document function
    result = await add_document(
        content=content,
        title=title,
        source=source,
        tags=tags,
        category=category
    )
    
    # Display results
    print("\n" + "=" * 60)
    
    if result["status"] == "success":
        print("✅ Document saved successfully!\n")
        print(f"📊 Extraction Results:")
        print(f"   Title: {result['title']}")
        print(f"   Entities Extracted: {result['entities_extracted']}")
        print(f"   Relationships Extracted: {result['relationships_extracted']}")
        print(f"   Communities Found: {result['communities_found']}")
        print(f"   Source: {result['source']}")
        print(f"   Tags: {', '.join(result['tags']) if result['tags'] else 'None'}")
        print(f"   Category: {result['category']}")
        print(f"   Message: {result['message']}")
        
    else:
        print("❌ Failed to save document\n")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print("=" * 60)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Save a document to the RAG knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --title="Server Specs" --content="GPU: 9070XT, CPU: AMD Ryzen 7 7700"
  %(prog)s --title="RAG Introduction" --content-file=docs/intro.md --tags="rag,neo4j" --category="technical"
  %(prog)s --title="Project Notes" --content-file=notes.txt --source="https://example.com"
        """
    )
    
    parser.add_argument(
        "--title", "-t",
        required=True,
        help="A descriptive title for the document"
    )
    
    parser.add_argument(
        "--content", "-c",
        help="The document content to save (use with --title)"
    )
    
    parser.add_argument(
        "--content-file", "-f",
        help="Path to a file containing the document content"
    )
    
    parser.add_argument(
        "--source", "-s",
        help="Optional source (URL, file path, author)"
    )
    
    parser.add_argument(
        "--tags", "-g",
        nargs="+",
        help="Optional tags for categorizing the document (space-separated)"
    )
    
    parser.add_argument(
        "--category", "-a",
        help="Optional category for the document"
    )
    
    return parser.parse_args()


def load_content_from_file(file_path: str) -> str:
    """Load content from a file."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    
    if not path.is_file():
        print(f"❌ Error: Not a file: {file_path}")
        sys.exit(1)
    
    try:
        content = path.read_text(encoding="utf-8")
        print(f"📖 Loaded content from: {file_path}")
        print(f"📊 Content size: {len(content)} characters")
        return content
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    
    # Get content from either --content or --content-file
    content = args.content
    if not content and args.content_file:
        content = load_content_from_file(args.content_file)
    
    if not content:
        print("❌ Error: Must provide content via --content or --content-file")
        sys.exit(1)
    
    # Run the save operation
    import asyncio
    asyncio.run(
        main(
            content=content,
            title=args.title,
            source=args.source,
            tags=args.tags,
            category=args.category
        )
    )
