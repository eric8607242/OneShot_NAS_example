# How to customize the agent
To supprot searching architectures for various tasks (e.g., classification, face recognition, and object detection), OSNASLib allow users to customize the training agent for different training pipeline. With the the customizing training agent, user do not need to implement the detail of searching process and evaluating process. By incorporate the training agent into the pre-implemented search agent and evaluate agent, user can search the architectures and evaluate the searched architecture by scratch easily. In this document, will briefly introduce how to customize the agent for your task in `agnet/` easily.

## Generate Interface
```
python3 build_interface.py -t agent --customize-name [CUSTOMIZE NAME] --customize-class [CUSTOMIZE CLASS]
```

After generating the agent interface, the directory `[CUSTOMIZE NAME]/` will be created in `agent/`, and the corresponding files (`__init__.py`, `training_agent.py`, and `agents.py`) are created in the directory `[CUSTOMIZE NAME]/`.

### Template Struture
```
- agent/
    |- [CUSTOMIZE NAME]/
    |         |- __init__.py
    |         |- training_agent.py
    |         -- agents.py
        ...
```


## Agent Interface
For customizing agent for various tasks, you should implement the training interface `[CUSTOMIZE CLASS]TrainingAgent` with the training pipeline. We describe the three interface classes in detail as follows:

### Training Agent Interface
`[CUSTOMIZE CLASS]TrainingAgent` is the training agent implemented the training pipeline specific for customizing task. In `[CUSTOMIZE CLASS]TrainingAgent`, you shoud implement the `_search_training_step()`, `_search_validate_step()`, `_evaluate_training_step()`, `_evaluate_validate_step()`, and `searching_evaluate()` for your task.
> Note that we provide the example training pipeline in the interface. You shoud modify the training pipeline to specific for your task.

```python3
import os
import time

import torch

from utils import AverageMeter, save
from ..base_training_agent import MetaTrainingAgent

class {{customize_class}}TrainingAgent(MetaTrainingAgent):
    """The training agent to train the supernet and the searched architecture.

    By implementing TrainingAgent class, users can adapt the searching and evaluating agent into
    various tasks easily.
    """
    @staticmethod
    def searching_evaluate(model, val_loader, device, criterion):
        """ Evaluating the performance of the supernet. The search strategy will evaluate
        the architectures by this static method to search.

        Args:
            model (nn.Module)
            val_loader (torch.utils.data.DataLoader)
            device (torch.device)
            criterion (nn.Module)

        Return:
            evaluate_metric (float): The performance of the supernet.
        """
        model.eval()
        with torch.no_grad():
            for step, (X, y) in enumerate(val_loader):
                raise NotImplemented
        return evaluate_metric


    def _training_step(self, model, train_loader, agent, epoch, print_freq=100):
        """
        Args:
            model (nn.Module)
            train_loader (torch.utils.data.DataLoader)
            agent (Object): The evaluate agent
            epoch (int)
        """
        model.train()
        start_time = time.time()

        for step, (X, y) in enumerate(train_loader):
            if agent.agent_state == "search":
                agent._iteration_preprocess()

        raise NotImplemented

    def _validate_step(self, model, val_loader, agent, epoch):
        """
        Args:
            model (nn.Module)
            val_loader (torch.utils.data.DataLoader)
            agent (Object): The evaluate agent
            epoch (int)

        Return:
            evaluate_metric (float): The performance of the searched model.
        """
        model.eval()
        start_time = time.time()
        if agent.agent_state == "search":
            agent._iteration_preprocess()
        raise NotImplemented

```

### Agents Interface
After constructing the train agent, in the `agents.py`, the `[CUSTOMIZE CLASS]SearchAgent` and the `[CUSTOMIZE CLASS]EvaluateAgent` are created by inherited the abstract class `MetaSearchAgent` and `MetaEvaluateAgent`. And in the customizing agents, the customizing training agent is set as the property to incorporate into the searching pipeline and evaluating pipeline. 
> Note that this file and the corresponding codes are created automatically.

```python3
from .training_agent import {{customize_class}}TrainingAgent
from ..base_search_agent import MetaSearchAgent
from ..base_evaluate_agent import MetaEvaluateAgent

class {{customize_class}}SearchAgent(MetaSearchAgent):
    agent_state = "search"
    training_agent = {{customize_class}}TrainingAgent()

class {{customize_class}}EvaluateAgent(MetaEvaluateAgent):
    agent_state = "evaluate"
    training_agent = {{customize_class}}TrainingAgent()
```

## Setting Config File
After constructing agent for your task, you can utilize your agent by setting the agent into the config file easily.
### Search Mode
```
agent:
    main_agent: "[CUSTOMIZE CLASS]SearchAgent"
```

### Evlauate Mode
```
agent:
    main_agent: "[CUSTOMIZE CLASS]EvaluateAgent"
```
