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
from datetime import datetime
import time

from rasa.engine.recipes.default_recipe import DefaultV1Recipe

TIME_FORMAT = "%I:%M %p"
WAIT_TIME = 20

@DefaultV1Recipe.register(
    [DefaultV1Recipe.ComponentType.POLICY_WITHOUT_END_TO_END_SUPPORT], is_trainable=False
)

class DynamicHealthPolicy(Policy):
    '''
    Dynamic Health Custom Policy
    This policy asks once a day about the sleeping habits of the user, if 
    he hasn't filled in that information already
    '''
    
    def __init__ (
        self,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
        featurizer: Optional[TrackerFeaturizer] = None,
        dynamic_action = "check_latest_health_form",
        wait_time = WAIT_TIME,
    ) -> None:
        super().__init__(config, model_storage, resource, execution_context, featurizer)

        self.dynamic_action = config.get("dynamic_action", dynamic_action)
        self.asked_today = False
        self.wait_time = config.get("wait_time", wait_time)
        self.start_time = time.time()


    @classmethod
    def get_default_config(cls) -> Dict[Text, Any]:
        return {
            "dynamic_action": "dynamic_action",
            "asked_today": False,
            "wait_time": WAIT_TIME,
            "priority": 6,
        }

    def train(self, training_trackers: List[TrackerWithCachedStates], domain: Domain, **kwargs: Any) -> Resource:
        """Does nothing, as this policy is deterministic"""
        return self

    def predict_action_probabilities(
        self,
        tracker: DialogueStateTracker,
        domain: Domain,
        **kwargs: Any,
        ) -> PolicyPrediction:
        """ This is where the magic happens, and we make our prediction of what the next action should be"""

        current_dif = time.time() - self.start_time
        already_registered = tracker.get_slot("already_registered")
        
        default_probs = [0.0] * domain.num_actions
        # Prevent this from being called twice in a row, after the first time it is called, we need to listen
        if tracker.latest_action_name == self.dynamic_action:
            default_probs[domain.index_for_action(ACTION_LISTEN_NAME)] = 1.0
        # If user is registered, it has been more than wait_time seconds since the conversation started, ask again (if not asked today)
        elif already_registered and current_dif > self.wait_time and not self.asked_today:
            default_probs[domain.index_for_action(self.dynamic_action)] = 1.0
            self.asked_today = True

        return self._prediction(default_probs)

    @classmethod
    def _metadata_filename(cls):
        return "dynamic_health_policy_files.json"

    def _metadata(self):
        return {
        "priority": self.priority,
        "wait_time": self.wait_time,
        "asked_today": self.asked_today,
        "dynamic_action": self.dynamic_action,
        }


