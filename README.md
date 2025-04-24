# skfurigana

日本語テキストにふりがな（ルビ）を付与し、さらに英数字をカタカナに自動変換するPythonパッケージです。  
形態素解析（fugashi + unidic）によるふりがな付与に加え、DeepSeek APIを利用して英数字をカタカナに変換します。

## 特徴

- 日本語テキストに自動でふりがなを付与
- 英数字や記号をカタカナに変換（DeepSeek API利用）
- シンプルなAPIで非同期処理にも対応

## インストール

```bash
pip install skfurigana
```

または、リポジトリをクローンして直接インストールも可能です。

```bash
git clone https://github.com/sugarkwork/furigana.git
cd furigana
pip install .
```

### 依存パッケージ

- fugashi[unidic]
- unidic
- skpmem
- json_repair
- chat_assistant

## DeepSeek APIキーの設定

本パッケージの一部機能（英数字のカタカナ変換）には DeepSeek API キーが必要です。  
プロジェクトのルートディレクトリに `.env` ファイルを作成し、以下のようにAPIキーを記載してください。

```
DEEPSEEK_API_KEY=あなたのAPIキー
```

## 使い方

### ふりがな付与（同期処理）

```python
from skfurigana import add_furigana

text = "お弁当を食べながら空を見上げているうちに、お弁当箱は空になった。"
result = add_furigana(text)
print(''.join(map(str, result)))
# 出力例: [お(お)][弁(べん)][当(とう)] を [食(た)]べながら[空(そら)]を...
```

### ふりがな＋英数字カタカナ変換（非同期処理）

```python
import asyncio
from skfurigana import convert_furigana

async def main():
    text = "LibreChatのdatabase全体をtext形式でdumpする方法について。"
    result = await convert_furigana(text)
    print(''.join(map(str, result)))

asyncio.run(main())
# 出力例: [LibreChat(リブレチャット)]の[database(データベース)]全体を[text(テキスト)]形式で...
```

### 英数字のみカタカナ変換（非同期処理）

```python
import asyncio
from skfurigana import KatakanaTranslator

async def main():
    translator = KatakanaTranslator()
    words = ["LibreChat", "database", "text"]
    result = await translator.translate_to_katakana(words)
    print(result)  # {'LibreChat': 'リブレチャット', 'database': 'データベース', ...}

asyncio.run(main())
```

## ライセンス

MIT License

## リンク

- [GitHubリポジトリ](https://github.com/sugarkwork/furigana)