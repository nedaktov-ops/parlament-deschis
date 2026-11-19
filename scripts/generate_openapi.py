#!/usr/bin/env python3
"""Generate OpenAPI schema from FastAPI app.

This script extracts the OpenAPI schema and saves it to the repository
for documentation and TypeScript client generation.
"""

import json
from pathlib import Path

# Import the app from the project
from backend.main import app


def generate_openapi_schema() -> dict:
    """Generate OpenAPI schema from the FastAPI app."""
    return app.openapi()


def main():
    """Generate and save OpenAPI schema."""
    schema = generate_openapi_schema()
    
    # Pretty print the schema
    schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
    
    # Save to pipeline directory (generated asset)
    output_path = Path(__file__).parent.parent / "pipeline" / "openapi.json"
    output_path.write_text(schema_json)
    
    print(f"✅ Generated OpenAPI schema: {output_path}")
    print(f"   Title: {schema['info']['title']}")
    print(f"   Version: {schema['info']['version']}")
    print(f"   Paths: {len(schema['paths'])} endpoints")
    
    return 0


if __name__ == "__main__":
    exit(main())
