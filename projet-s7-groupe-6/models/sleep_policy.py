from typing import List, Dict, Text, Optional, Any, Union, Tuple
from rasa.core.policies.policy import Policy, PolicyPrediction, Resource
from rasa.shared.nlu.interpreter import NaturalLanguageInterpreter
from rasa.engine.storage.storage import ModelStorage
from rasa.engine.graph import ExecutionContext
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.generator import TrackerWithCachedStates
from rasa.core.constants import DEFAULT_POLICY_PRIORITY
from rasa.shared.core.constants import ACTION_LISTEN_NAME
from rasa.shared.core.domain import Domain
from rasa.core.featurizers.tracker_featurizers import TrackerFeaturizer
from datetime import time, datetime

from rasa.engine.recipes.default_recipe import DefaultV1Recipe

TIME_FORMAT = "%I:%M %p"

# TODO: Correctly register your graph component
@DefaultV1Recipe.register(
    [DefaultV1Recipe.ComponentType.POLICY_WITHOUT_END_TO_END_SUPPORT], is_trainable=True
)

class SleepPolicy(Policy):
    
    def __init__ (
        self,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
        featurizer: Optional[TrackerFeaturizer] = None,
        sleep_action = "utter_go_away",
        sleep_time = "12:00 AM",
        wake_time = "8:00 AM",
    ) -> None:
        ## useless code here m8
        super().__init__(config, model_storage, resource, execution_context, featurizer)

        self.sleep_action = sleep_action
        self.sleep_time = datetime.strptime(config.get("sleep_time", sleep_time), TIME_FORMAT).time()
        self.wake_time = datetime.strptime(config.get("wake_time", wake_time), TIME_FORMAT).time()

    @classmethod
    def get_default_config(cls) -> Dict[Text, Any]:
        return {
            "sleep_action": "utter_go_away",
            "sleep_time": "12:00 AM",
            "wake_time": "8:00 AM",
            "priority": 6,
        }

    def train(self, training_trackers: List[TrackerWithCachedStates], domain: Domain, **kwargs: Any) -> Resource:
        """Does nothing, as this policy is deterministic"""
        print(kwargs)
        return self

    def predict_action_probabilities(
        self,
        tracker: DialogueStateTracker,
        domain: Domain,
        **kwargs: Any,
        ) -> PolicyPrediction:
        """ This is where the magic happens, and we make our prediction of what the next action should be"""

        current_time = datetime.now().time()
        
        default_probs = [0.0] * domain.num_actions
        # Prevent this from being called twice in a row, after the first time it is called, we need to listen
        if tracker.latest_action_name == self.sleep_action:
            default_probs[domain.index_for_action(ACTION_LISTEN_NAME)] = 1.0
        elif (self.sleep_time < self.wake_time and current_time > self.sleep_time and 
        current_time < self.wake_time) or (self.sleep_time > self.wake_time) and (current_time > self.sleep_time
        or	current_time < self.wake_time):
            default_probs[domain.index_for_action(self.sleep_action)] = 1.0

        return self._prediction(default_probs)

    @classmethod
    def _metadata_filename(cls):
        return "sleep_policy_files.json"

    def _metadata(self):
        return {
        "priority": self.priority,
        "sleep_time": self.sleep_time.strftime(TIME_FORMAT),
        "wake_time": self.wake_time.strftime(TIME_FORMAT),
        "sleep_action": self.sleep_action
        }


