import asyncio
from skfurigana import convert_furigana

async def main():
    text = "LibreChatのdatabase全体をtext形式でdumpする方法について。"
    try:
        result = await convert_furigana(text)
        print(''.join(map(str, result)))
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("注意: この機能にはDeepSeek APIキーが必要です。")

if __name__ == "__main__":
    asyncio.run(main())