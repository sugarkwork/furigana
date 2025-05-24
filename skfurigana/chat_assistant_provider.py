import threading
from chat_assistant import ModelManager

_lock1 = threading.Lock()
_lock2 = threading.Lock()
_instance = None

class ChatAssistantProvider:
    """
    ChatAssistant のインスタンスを共通の設定で管理・取得するためのプロバイダ
    """
    def __init__(self, models:ModelManager=None, model=None, memory=None, **kwargs):
        self._assistant = None
        self._model = model if model is not None else 'deepseek/deepseek-chat'
        self._models = models if models is not None else ModelManager(models=[self._model])

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
            self._assistant = ChatAssistant(memory=self._memory, model_manager=self._models, **self._kwargs)
            self._assistant.model_manager.change_model(self._model)
            return self._assistant

# シングルトン的に使う場合のグローバル関数
def get_chat_assistant(models:ModelManager=None, model=None, memory=None, **kwargs):
    model = model if model is not None else 'deepseek/deepseek-chat'
    models = models if models is not None else ModelManager(models=[model])
    global _instance
    with _lock2:
        if _instance is None:
            _instance = ChatAssistantProvider(models=models, memory=memory, **kwargs)
        return _instance.get_assistant()
