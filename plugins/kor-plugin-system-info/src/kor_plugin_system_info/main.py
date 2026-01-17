import platform
import sys

def main():
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")

if __name__ == "__main__":
    main()
