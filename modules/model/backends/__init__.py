from .kcpp_model import KcppModel
from .lcpp_model import LcppModel
try:
    from .lpy_model import LpyModel
    LPY_PRESENT = True
except ModuleNotFoundError as e:
    LPY_PRESENT = False