# skfurigana

日本語テキストにふりがな（ルビ）を付与し、英数字をカタカナに自動変換できる Python パッケージです。形態素解析（fugashi + UniDic）でのふりがな付与に加え、LLM（既定は DeepSeek）を用いた英数字→カタカナ変換と、必要に応じたルビの自動補正にも対応します。

## 特徴

- ふりがなの自動付与（同期 API）
- 英数字のカタカナ化とルビの自動補正（非同期 API）
- シンプルな API 設計（`Moji` オブジェクトのリストを返却）
- 出力形式は角括弧表記と `ruby` タグ表記を切替可
- 単語翻訳結果をローカルキャッシュ（`cache.db`）して再利用

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

### 依存パッケージ（抜粋）

- `fugashi[unidic]`, `unidic`: 形態素解析と辞書
- `skpmem`: 永続メモリ（翻訳キャッシュ等）
- `chat_assistant`: LLM 呼び出しラッパー
- `json_repair`: LLM 出力の JSON 補正

UniDic 辞書が未導入の場合、初回実行時に自動ダウンロードを試みます（`python -m unidic download` 相当）。ネットワーク制限がある環境では事前に辞書を導入してください。

```bash
pip install unidic fugashi[unidic]
python -m unidic download
```

## 環境変数（LLM 用）

- `DEEPSEEK_API_KEY`: 既定のモデル（`deepseek/deepseek-chat`）を使う場合に必要です。
- `.env` に記述する場合は以下のように設定します。

```
DEEPSEEK_API_KEY=あなたのAPIキー
```

chat_assistant が対応する他プロバイダを用いる場合は、各プロバイダの API キーを環境変数で設定してください（例: Gemini など）。

## クイックスタート

### ふりがな付与のみ（同期）

```python
from skfurigana import add_furigana

text = "お弁当を食べながら空を見上げているうちに、お弁当箱は空になった。"
result = add_furigana(text)
print(''.join(map(str, result)))
# 例: [お(お)][弁(べん)][当(とう)] を [食(た)]べながら[空(そら)]を...
```

### ふりがな＋英数字カタカナ化（非同期）

```python
import asyncio
from skfurigana import convert_furigana

async def main():
    text = "LibreChatのdatabase全体をtext形式でdumpする方法について。"
    result = await convert_furigana(text)
    print(''.join(map(str, result)))

asyncio.run(main())
# 例: [LibreChat(リブレチャット)]の[database(データベース)]全体を[text(テキスト)]形式で...
```

### `ruby` タグでの出力（非同期）

```python
import asyncio
from skfurigana import convert_furigana

async def main():
    text = "お弁当を食べながら空を見上げる。LibreChatについて。"
    result = await convert_furigana(text, tag=True, separator=False)
    print(''.join(map(str, result)))
    # 例: <ruby>弁当<rt>べんとう</rt></ruby> ... <ruby>LibreChat<rt>リブレチャット</rt></ruby> ...

asyncio.run(main())
```

### 英数字のみカタカナ変換（非同期）

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

## 関数とパラメータ

- `add_furigana(text: str) -> list[Moji]`
  - 日本語テキストにふりがなを付与します（LLM 不要）。
  - 返り値は `Moji` のリストです。`str(moji)` で角括弧表記、`moji.set_mode(tag=True)` で `ruby` 表記が可能です。

- `convert_furigana(text: str, tag=False, separator=True, adjust_ai=True, memory=None, model=None, temperature=None, models=None) -> list[Moji]`
  - ふりがな付与に加え、英数字をカタカナへ翻訳し、必要なら LLM でルビを自動調整します（非同期）。
  - 主な引数:
    - `tag`: `True` で `ruby` タグ出力、`False` で角括弧表記。
    - `separator`: `True` でトークン間のスペースを出力、`False` で削除。
    - `adjust_ai`: `True` で LLM による読みの自動補正を実施。コストと遅延が発生します。
    - `memory`: `skpmem` のメモリを渡すと会話・翻訳のキャッシュを共有できます（既定は `cache.db`）。
    - `model`: ルビ補正や翻訳に用いるモデル名（既定 `deepseek/deepseek-chat`）。
    - `temperature`: LLM の温度。省略時は 0.0。
    - `models`: `chat_assistant.ModelManager` を外部から渡す高度な利用向け。

- `KatakanaTranslator`
  - `translate_to_katakana(words: list[str]) -> dict[str,str]`: 単語配列を一括で英語風カタカナに変換。
  - `translate_text(text: str) -> str`: テキスト内の英数字をカタカナに一括置換（内部的に辞書化）。

## CLI（サンプル）

簡易スクリプト `run_furigana.py` を用意しています。

```bash
python run_furigana.py convert "LibreChatのdatabase全体をtext形式でdumpする方法について。"
```

既定で `tag=True, separator=False` で出力します。LLM を利用するため、API キーとネットワーク接続が必要です。

## キャッシュと生成物

- 翻訳・会話キャッシュは既定でリポジトリ直下の `cache.db`（SQLite）に保存されます。
- キャッシュをクリアしたい場合は `cache.db` を削除してください。
- UniDic の辞書は別途ダウンロード・管理されます（`unidic.DICDIR`）。

## 注意点・ベストプラクティス

- ネットワーク要件:
  - 初回の UniDic ダウンロードにネットワークが必要です。制限環境では事前導入してください。
  - 英数字のカタカナ化やルビ補正には LLM API へのアクセスが必要です（DeepSeek など）。
- コストとレイテンシ:
  - `adjust_ai=True` は品質向上の代わりにトークン課金と遅延が発生します。必要に応じて `False` にしてください。
- 出力形式:
  - 表示用途（HTML）では `tag=True` で `ruby` 出力、テキスト用途では既定の角括弧表記が扱いやすいです。
- 形態素解析の精度:
  - UniDic のバージョンや品詞分解の結果に依存します。用途に応じて後処理を検討してください。

## トラブルシューティング

- UniDic の自動ダウンロードに失敗する:
  - 手動で `pip install unidic fugashi[unidic]`、続けて `python -m unidic download` を実行してください。
- LLM 呼び出しでエラーになる:
  - `DEEPSEEK_API_KEY` など必要な環境変数が設定されているか確認し、ネットワーク接続を見直してください。
  - 料金・レート制限に注意してください。失敗時は `adjust_ai=False` で回避可能です。
- ふりがなのみで十分:
  - `add_furigana` を使用してください（LLM 不要、オフライン可）。

## ライセンス

MIT License

## リンク

- GitHub: https://github.com/sugarkwork/furigana
