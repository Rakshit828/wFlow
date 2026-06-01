# from importlib import import_module


# def __getattr__(name: str):
#     if name == "app":
#         module = import_module("src.app")
#         return getattr(module, "app")
#     raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from src.app import app