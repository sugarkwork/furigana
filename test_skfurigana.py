from skfurigana import add_furigana

def main():
    text = "お弁当を食べながら空を見上げているうちに、お弁当箱は空になった。"
    result = add_furigana(text)
    print(''.join(map(str, result)))

if __name__ == "__main__":
    main()