import threading

_lock1 = threading.Lock()
_lock2 = threading.Lock()
_instance = None

class ChatAssistantProvider:
    """
    ChatAssistant のインスタンスを共通の設定で管理・取得するためのプロバイダ
    """
    def __init__(self, model="deepseek/deepseek-chat", memory=None, **kwargs):
        self._assistant = None
        self._model = model
        if self._model is None:
            self._model = "deepseek/deepseek-chat"
        if memory is None:
            from skpmem.async_pmem import PersistentMemory
            memory = PersistentMemory("cache.db")
        self._memory = memory
        self._kwargs = kwargs

    def get_assistant(self):
        with _lock1:
            if self._assistant is not None:
                return self._assistant
            from chat_assistant import ChatAssistant
            self._assistant = ChatAssistant(memory=self._memory, **self._kwargs)
            self._assistant.model_manager.change_model(self._model)
            return self._assistant

# シングルトン的に使う場合のグローバル関数
def get_chat_assistant(model="deepseek/deepseek-chat", memory=None, **kwargs):
    if model is None:
        model="deepseek/deepseek-chat"
    global _instance
    with _lock2:
        if _instance is None:
            _instance = ChatAssistantProvider(model=model, memory=memory, **kwargs)
        return _instance.get_assistant()
