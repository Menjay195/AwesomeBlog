# -*- coding:utf-8 -*-


#只实现到一层的属性处理，只能x.y，不能x.y.z，能x.y[z]
class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    '''
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        # zip([seql, ...])接受一系列可迭代对象作为参数->
        # 将对象中对应的元素打包成一个个tuple（元组）->
        # 然后返回由这些tuples组成的list（列表）
        for k, v in zip(names, values):
            self[k] = v

    # 属性动态化处理；当使用点号获取类实例属性时，如果属性不存在就自动调用__getattr__方法
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    # 属性赋值；当设置类实例属性时自动调用。
    def __setattr__(self, key, value):
        self[key] = value

#配合Dict实现多层属性处理，可以x.y.z
def toDict(d):
    D = Dict()
    for k, v in d.items():
        D[k] = toDict(v) if isinstance(v, dict) else v
    return D


# ---------------------------------------------------------------------------


def merge(defaults, override):
    r = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r


# ---------------------------------------------------------------------------


import config_default

configs = config_default.configs

try:
    import config_override

    configs = merge(configs, config_override.configs)
except ImportError as e:
    print(e)

configs = toDict(configs)