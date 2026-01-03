# main.py
import sys
from core.cli import FSBuilderCLI

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        FSBuilderCLI.main()
    else:
        # Show help if no arguments
        FSBuilderCLI.main()

if __name__ == "__main__":
    main()