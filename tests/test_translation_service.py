from services.translation_service import TranslationConfig, TranslationService

def test_empty_input():
    """
    空文字列を翻訳すると空文字列を返す
    """
    cfg = TranslationConfig()
    svc = TranslationService(cfg)
    inputs = [""]
    assert svc.translate_en_to_jp(inputs) == [""]

def test_en_to_jp():
    """
    英文を日本語に翻訳する
    """
    cfg = TranslationConfig()
    svc = TranslationService(cfg)
    inputs = ["This is a test.", "Time is money."]
    translated = svc.translate_en_to_jp(inputs)

    # 空文字列でないことを確認
    assert translated[0] != ""

    # 2つ分の翻訳結果を確認
    assert len(translated) == 2