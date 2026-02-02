#!/usr/bin/env python3
"""
Seed Tenant Script

Creates a test tenant for development.

Usage:
    python scripts/seed_tenant.py
    python scripts/seed_tenant.py --tenant-id mantra --name "MANTRA System"
"""

import os
import sys
import asyncio
import argparse
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg


async def get_connection() -> asyncpg.Connection:
    """Get database connection."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://chat:chatpassword@localhost:5433/atlas_chat"
    )
    return await asyncpg.connect(database_url)


async def seed_tenant(
    tenant_id: str,
    name: str,
    persona_name: str,
    system_prompt: str
):
    """Seed a tenant."""
    conn = await get_connection()

    try:
        # Check if tenant exists
        existing = await conn.fetchval(
            "SELECT id FROM tenants WHERE id = $1",
            tenant_id
        )

        if existing:
            print(f"Tenant '{tenant_id}' already exists")
            return

        # Default configurations
        llm_config = json.dumps({
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 1000,
        })

        embedding_config = json.dumps({
            "provider": "openai",
            "model": "text-embedding-3-small",
            "dimensions": 1536,
        })

        rag_config = json.dumps({
            "strategy": "hybrid",
            "reranker_enabled": False,
            "top_k": 5,
            "score_threshold": 0.3,
        })

        features = json.dumps({
            "memory_extraction": True,
            "temporal_memory": True,
            "streaming": True,
            "session_summarization": True,
        })

        # Insert tenant
        await conn.execute("""
            INSERT INTO tenants (
                id, name, system_prompt, persona_name,
                llm_config, embedding_config, rag_config, features
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, tenant_id, name, system_prompt, persona_name,
            llm_config, embedding_config, rag_config, features)

        print(f"✓ Created tenant: {tenant_id}")
        print(f"  Name: {name}")
        print(f"  Persona: {persona_name}")

    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description="Seed a test tenant")
    parser.add_argument(
        "--tenant-id",
        default="test",
        help="Tenant ID"
    )
    parser.add_argument(
        "--name",
        default="Test Tenant",
        help="Tenant name"
    )
    parser.add_argument(
        "--persona",
        default="Assistant",
        help="AI persona name"
    )
    parser.add_argument(
        "--system-prompt",
        default="You are a helpful AI assistant.",
        help="System prompt"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ARSAKA_TUTUR Tenant Seeder")
    print("=" * 60)
    print()

    asyncio.run(seed_tenant(
        tenant_id=args.tenant_id,
        name=args.name,
        persona_name=args.persona,
        system_prompt=args.system_prompt,
    ))


if __name__ == "__main__":
    main()
