import sys
from skfurigana.furigana import add_furigana, convert_furigana, get_chat_assistant

async def main():
    if len(sys.argv) < 2:
        print("使い方: python run_furigana.py [add|convert] テキスト")
        sys.exit(1)
    
    from skpmem.async_pmem import PersistentMemory
    async with PersistentMemory("cache.db") as memory:
        command = sys.argv[1]
        if command == "convert":
            if len(sys.argv) < 3:
                print("convert_furigana: テキストを指定してください")
                sys.exit(1)
            text = sys.argv[2]
            result = await convert_furigana(text, tag=True, separator=False, memory=memory)
            print(''.join(map(str, result)))
        else:
            print(f"未知のコマンド: {command}")
            print("使い方: python run_furigana.py [add|convert] テキスト")
            sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())