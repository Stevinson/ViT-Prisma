from sae_lens import SAETrainingRunner
from sae_lens.config import LanguageModelSAERunnerConfig
from sae_lens.training.training_sae import TrainingSAE, TrainStepOutput



from sae.vision_activations_store import VisionActivationsStore



class VisionSAERunner(SAETrainingRunner):
    def __init__(
        self,
        cfg: LanguageModelSAERunnerConfig,
        vision_activations_store: VisionActivationsStore,

        # override_dataset: HfDataset | None = None,
        # override_model: HookedRootModule | None = None,
    ):
        # if override_dataset is not None:
        #     logging.warning(
        #         f"You just passed in a dataset which will override the one specified in your configuration: {cfg.dataset_path}. As a consequence this run will not be reproducible via configuration alone."
        #     )
        # if override_model is not None:
        #     logging.warning(
        #         f"You just passed in a model which will override the one specified in your configuration: {cfg.model_name}. As a consequence this run will not be reproducible via configuration alone."
        #     )

        # This class contains a method to override the language activations store with the vision activations store

        self.cfg = cfg

        if override_model is None:
            self.model = load_model(
                self.cfg.model_class_name,
                self.cfg.model_name,
                device=self.cfg.device,
                model_from_pretrained_kwargs=self.cfg.model_from_pretrained_kwargs,
            )
        else:
            self.model = override_model

        # The motivation for having this config is to change the vision activations store
        self.activations_store = vision_activations_store

        if self.cfg.from_pretrained_path is not None:
            self.sae = TrainingSAE.load_from_pretrained(
                self.cfg.from_pretrained_path, self.cfg.device
            )
        else:
            self.sae = TrainingSAE(
                TrainingSAEConfig.from_dict(
                    self.cfg.get_training_sae_cfg_dict(),
                )
            )
            self._init_sae_group_b_decs()