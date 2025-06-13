import sys
import asyncio
from gitingest import ingest_async

async def main():
    try:
        if len(sys.argv) != 4:
            raise ValueError("Usage: python script.py <path> <summary_file> <content_file>")

        path, summary_file, content_file = sys.argv[1], sys.argv[2], sys.argv[3]

        # Asynchronous ingest with error handling
        try:
            summary, _, content = await ingest_async(path)
        except Exception as e:
            raise RuntimeError(f"Failed to ingest path '{path}': {str(e)}")

        # Check for empty content
        if not content:
            raise ValueError(f"No content found in path '{path}'")

        # File writing with error handling
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(str(summary))
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(str(content))
        except IOError as e:
            raise IOError(f"Failed to write files: {str(e)}")

        print(f"Success! Summary saved to {summary_file}, content to {content_file}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
