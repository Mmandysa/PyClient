class Singleton:
    # 静态变量（类变量）用于存储单例实例
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        # 如果实例不存在，则创建新实例
        if not cls._instance:
            cls._instance = super().__new__(cls)
            # 可以在这里初始化实例属性
            cls._instance.initialized = False
        return cls._instance