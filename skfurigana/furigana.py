import os
from typing import List
import fugashi
import unidic
import re
import json
import asyncio
import logging
from typing import List, Dict
from skpmem.async_pmem import PersistentMemory
import asyncio
from json_repair import repair_json


def unidic_download():
    import unidic
    import subprocess
    import sys
    # python -m unidic download
    subprocess.run([sys.executable, '-m', 'unidic', 'download'])


class KatakanaTranslator:
    def __init__(self, model: str = "deepseek/deepseek-chat", cache_file: str = "cache.db"):
        """
        テキスト翻訳クラスの初期化
        
        Args:
            model (str, optional): 使用するAIモデル. デフォルトは"deepseek/deepseek-chat".
        """
        self.chache = {}
        self.model = model
        self.logger = logging.getLogger(__name__)
        if isinstance(cache_file, str):
            self.memory = PersistentMemory(cache_file)
        elif isinstance(cache_file, PersistentMemory):
            self.memory = cache_file
        self.assistant = None
    
    def get_assistant(self):
        if self.assistant:
            return self.assistant

        from chat_assistant import ChatAssistant
        self.assistant = ChatAssistant(memory=self.memory)
        self.assistant.model_manager.change_model(self.model)
        return self.assistant

    def extract_alphanumeric(self, text: str) -> List[str]:
        """
        テキストから英数字の文字列を抽出する
        
        Args:
            text (str): 入力テキスト
        
        Returns:
            List[str]: 抽出された英数字の文字列リスト
        """
        # alphabet plus number
        pattern1 = r'[a-zA-Z]+(?:\d+(?:\.\d+)*)?(?:\d+)?'
        # alphabet only
        pattern2 = r'[a-zA-Z]+'
        return list(set(re.findall(pattern1, text) + re.findall(pattern2, text)))

    async def translate_to_katakana(self, words: List[str]) -> Dict[str, str]:
        """
        単語リストを日本語カタカナ風に翻訳する
        
        Args:
            words (List[str]): 翻訳する単語リスト
        
        Returns:
            Dict[str, str]: 単語とその翻訳の辞書
        """
        prompt_text = ("次の英単語および数字を英語風のカタカナ読みにするとどうなりますか？\n"
                       "Python の dict 型で出力してください。コメントや補足は不要です。\n")

        self.get_assistant()
        response = await self.assistant.chat("", f"{prompt_text}\n\n{words}")
        self.logger.debug(response)
        return json.loads(repair_json(response))    
    

    async def get_cached_translation(self, text: str) -> str:
        """
        キャッシュされた翻訳を取得する
        """
        key = f"translation_cache_{text}"
        result = await self.memory.load(key)
        return result

    async def save_translation(self, text: str, translated_text: str) -> None:
        """
        翻訳をキャッシュする
        """
        key = f"translation_cache_{text}"
        await self.memory.save(key, translated_text)
    
    async def translate_dict(self, text:str=None, alphanumeric_words:List[str] = None) -> Dict[str, str]:
        if not alphanumeric_words and text:
            alphanumeric_words = list(set(self.extract_alphanumeric(text)))

        # キャッシュされた翻訳を取得
        cached_words = {}
        for word in alphanumeric_words:
            if translated_text := await self.get_cached_translation(word):
                if translated_text := translated_text.strip():
                    if word != translated_text:
                        cached_words[word] = translated_text

        # キャッシュされた翻訳をテキストから削除
        for key in cached_words.keys():
            alphanumeric_words.remove(key)

        # カタカナ翻訳を取得
        if alphanumeric_words:
            self.logger.debug("Translating to Katakana...")
            self.logger.debug(alphanumeric_words)
            translates = await self.translate_to_katakana(alphanumeric_words)
        else:
            self.logger.debug("No words to translate.")
            translates = {}
        
        translates.update(cached_words)

        for key in translates.keys():
            if key not in cached_words:
                await self.save_translation(key, translates[key])

        return translates

    async def translate_text(self, text: str) -> str:
        # 英数字の単語を抽出
        alphanumeric_words = list(set(self.extract_alphanumeric(text)))

        # 英数字の文字列の長い順にソートする
        sorted_words = alphanumeric_words.copy()
        sorted_words.sort(key=lambda x: len(x), reverse=True)

        translates = await self.translate_dict(alphanumeric_words=alphanumeric_words)

        self.logger.debug("Translation completed.")
        self.logger.debug(translates)

        # テキストを置き換え
        for key in sorted_words:
            text = text.replace(key, translates[key])
    
        return text
    
    async def close(self):
        if self.memory:
            await asyncio.sleep(0.1)
            await self.memory.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

class Moji:
    def __init__(self, surface: str = None, kana: str = None, sepalator: bool = False):
        self.surface = surface
        self.kana = kana
        self.sepalator = sepalator

    def __str__(self):
        if self.kana:
            return f'[{self.surface}({self.kana})]'
        elif self.sepalator:
            return ' '
        else:
            return self.surface

    def __repr__(self):
        return str(self)


def is_kana(char: str) -> bool:
    return ('\u3040' <= char <= '\u309F') or ('\u30A0' <= char <= '\u30FF')

def is_kanji(char: str) -> bool:
    return ('\u4E00' <= char <= '\u9FFF') or ('\u3400' <= char <= '\u4DBF') or ('\uF900' <= char <= '\uFAFF')

def get_kana_for_kanji(kana) -> str:
    return ''.join(
        chr(ord(char) + 0x3041 - 0x30A1) if 0x30A1 <= ord(char) <= 0x30F6 else char for char in kana)

def extract_okurigana_and_surface(word_surface: str) -> tuple[str, str]:
    okurigana = ''
    for i in range(len(word_surface) - 1, -1, -1):
        if is_kana(word_surface[i]):
            okurigana = word_surface[i] + okurigana
        else:
            break
    kanji_length = len(word_surface) - len(okurigana)
    surface_cut = word_surface[:kanji_length]
    return surface_cut, okurigana

def split_by_kana(surface_cut: str, kana: str, okurigana: str) -> list:
    result = []
    if bool(re.search(r'[\u3041-\u309F]', surface_cut)):
        middle_okurigana = re.findall(r'[\u3041-\u309F\u30A0-\u30FF]+', surface_cut)
        split_word = surface_cut.split(middle_okurigana[0])
        split_kana = kana.split(middle_okurigana[0])
        if len(split_word) != len(split_kana):
            result.append(Moji(surface_cut, kana))
            if okurigana:
                result.append(Moji(okurigana))
        else:
            if len(split_word) == 2:
                result.append(Moji(split_word[0], split_kana[0]))
                result.append(Moji(middle_okurigana[0]))
                result.append(Moji(split_word[1], split_kana[1]))
                if okurigana:
                    result.append(Moji(okurigana))
    else:
        result.append(Moji(surface_cut, kana))
        if okurigana:
            result.append(Moji(okurigana))
    return result

def process_word(word) -> list[Moji]:
    result = []
    word_surface = word.surface
    if is_kanji(word_surface):
        surface_cut, okurigana = extract_okurigana_and_surface(word_surface)
        
        if word.feature.kana:
            kana = get_kana_for_kanji(word.feature.kana)
            kana = kana[0:len(kana) - len(okurigana)] if okurigana else kana
            result.extend(split_by_kana(surface_cut, kana, okurigana))
        else:
            if word_surface:
                result.append(Moji(word_surface))
    else:
        if word_surface:
            result.append(Moji(word_surface))
    return result

def add_furigana(text: str) -> list[Moji]:
    # Unidic 辞書がなければ自動ダウンロード
    if not os.path.exists(unidic.DICDIR):
        unidic_download()

    tagger = fugashi.Tagger(f'-d "{unidic.DICDIR}"')
    
    result = []
    for line in text.split('\n'):
        if len(result) != 0:
            result.append(Moji("\n"))
        for word in tagger(line.strip()):
            result.extend(process_word(word))
            result.append(Moji(sepalator=True))
       
    return result

async def convert_furigana(text: str) -> list[Moji]:
    furigana = add_furigana(text)
    async with KatakanaTranslator() as translator:
        translated_dict = await translator.translate_dict(text)
        result = []
        for moji in furigana:
            if moji.surface in translated_dict:
                moji.kana = translated_dict[moji.surface]
            result.append(moji)

    return result


async def main():
    logging.basicConfig(level=logging.INFO)
    text = """
    LibreChatのdatabase全体をtext形式でdumpする方法について。
    お弁当を食べながら空を見上げているうちに、お弁当箱は空になった。
    a123, http://example.com, superuser, 123456
    Ubuntuは、Desktop版とServer版の2つのEditionがあります。
    Mongoの意味は何ですか？知らんけど。GEMINI_API_KEY
    """
    result = await convert_furigana(text)
    print(''.join(map(str, result)))


if __name__ == '__main__':
    asyncio.run(main())
