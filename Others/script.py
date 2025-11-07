import importlib
import sys

def reload_package(package):
    """
    Reload all submodules of a given package recursively.
    Usage: reload_package(droma_py)
    """
    assert hasattr(package, "__package__")
    fn = package.__file__
    if not fn or not fn.endswith("__init__.py"):
        raise ValueError(f"{package.__name__} is not a package")
    # 获取包名前缀
    prefix = package.__name__ + "."
    modules_to_reload = []
    # 找出所有已导入的、属于该包的子模块
    for name, module in sys.modules.items():
        if name.startswith(prefix) and module is not None:
            modules_to_reload.append(name)
    # 按层级深度排序（确保子模块先于父模块？其实 reload 顺序影响不大）
    modules_to_reload.sort(key=lambda x: x.count('.'), reverse=True)
    # 重载所有子模块
    for name in modules_to_reload:
        if name in sys.modules:
            importlib.reload(sys.modules[name])
            print(f"Reloaded: {name}")
    # 最后重载顶层包本身
    importlib.reload(package)
    print(f"Reloaded: {package.__name__}")