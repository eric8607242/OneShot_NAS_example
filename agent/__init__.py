import sys


def get_agent_cls(name):
    return getattr(sys.modules[__name__], name)


from .classification_agent import CFSearchAgent, CFEvaluateAgent
from .face_agent import FRSearchAgent, FREvaluateAgent
