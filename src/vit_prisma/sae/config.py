'''
Some code is based off Joseph Bloom's SAE Lens: 
https://github.com/jbloomAus/SAELens/blob/main/sae_lens/config.py
'''

import json
import os
from dataclasses import dataclass, field, fields
from typing import Any, Literal, Optional, cast


import torch
import wandb
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict

from vit_prisma.utils.saving_utils import get_version

DTYPE_MAP = {
    "float32": torch.float32,
    "float64": torch.float64,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
    "torch.float32": torch.float32,
    "torch.float64": torch.float64,
    "torch.float16": torch.float16,
    "torch.bfloat16": torch.bfloat16,
}

HfDataset = DatasetDict | Dataset | IterableDatasetDict | IterableDataset
__version__ = get_version()

@dataclass
class VisionModelSAERunnerConfig:
    
    # Sonia Note: make sure that everything here is essential for vision models, group together hyperparams that are vision-specific
    """
    Configuration for training a sparse autoencoder on a vision model.

    Args:
        model_name (str): The name of the model to use. This should be the name of the model in the Hugging Face model hub.
        model_class_name (str): The name of the class of the model to use. This should be 'HookedViT'.
        hook_name (str): The name of the hook to use. This should be a valid TransformerLens hook.
        hook_eval (str): NOT CURRENTLY IN USE. The name of the hook to use for evaluation.
        hook_layer (int): The index of the layer to hook. Used to stop forward passes early and speed up processing.
        hook_head_index (int, optional): When the hook if for an activatio with a head index, we can specify a specific head to use here.
        dataset_path (str): A Hugging Face dataset path.
        dataset_trust_remote_code (bool): Whether to trust remote code when loading datasets from Huggingface.
        streaming (bool): Whether to stream the dataset. Streaming large datasets is usually practical.
        context_size (int): The context size to use when generating activations on which to train the SAE.
        use_cached_activations (bool): Whether to use cached activations. This is useful when doing sweeps over the same activations.
        cached_activations_path (str, optional): The path to the cached activations.
        d_in (int): The input dimension of the SAE.
        d_sae (int, optional): The output dimension of the SAE. If None, defaults to `d_in * expansion_factor`.
        b_dec_init_method (str): The method to use to initialize the decoder bias. Zeros is likely fine.
        expansion_factor (int): The expansion factor. Larger is better but more computationally expensive.
        activation_fn (str): The activation function to use. Relu is standard.
        normalize_sae_decoder (bool): Whether to normalize the SAE decoder. Unit normed decoder weights used to be preferred.
        noise_scale (float): Using noise to induce sparsity is supported but not recommended.
        from_pretrained_path (str, optional): The path to a pretrained SAE. We can finetune an existing SAE if needed.
        apply_b_dec_to_input (bool): Whether to apply the decoder bias to the input. Not currently advised.
        decoder_orthogonal_init (bool): Whether to use orthogonal initialization for the decoder. Not currently advised.
        decoder_heuristic_init (bool): Whether to use heuristic initialization for the decoder. See Anthropic April Update.
        init_encoder_as_decoder_transpose (bool): Whether to initialize the encoder as the transpose of the decoder. See Anthropic April Update.
        n_batches_in_buffer (int): The number of batches in the buffer. When not using cached activations, a buffer in ram is used. The larger it is, the better shuffled the activations will be.
        training_tokens (int): The number of training tokens.
        finetuning_tokens (int): The number of finetuning tokens. See [here](https://www.lesswrong.com/posts/3JuSjTZyMzaSeTxKk/addressing-feature-suppression-in-saes)
        store_batch_size_prompts (int): The batch size for storing activations. This controls how many prompts are in the batch of the language model when generating actiations.
        train_batch_size_tokens (int): The batch size for training. This controls the batch size of the SAE Training loop.
        normalize_activations (str): Activation Normalization Strategy. Either none, expected_average_only_in (estimate the average activation norm and divide activations by it -> this can be folded post training and set to None), or constant_norm_rescale (at runtime set activation norm to sqrt(d_in) and then scale up the SAE output).
        device (str): The device to use. Usually cuda.
        act_store_device (str): The device to use for the activation store. CPU is advised in order to save vram.
        seed (int): The seed to use.
        dtype (str): The data type to use.
        prepend_bos (bool): Whether to prepend the beginning of sequence token. You should use whatever the model was trained with.
        autocast (bool): Whether to use autocast during training. Saves vram.
        autocast_lm (bool): Whether to use autocast during activation fetching.
        compile_llm (bool): Whether to compile the LLM.
        llm_compilation_mode (str): The compilation mode to use for the LLM.
        compile_sae (bool): Whether to compile the SAE.
        sae_compilation_mode (str): The compilation mode to use for the SAE.
        train_batch_size_tokens (int): The batch size for training.
        adam_beta1 (float): The beta1 parameter for Adam.
        adam_beta2 (float): The beta2 parameter for Adam.
        mse_loss_normalization (str): The normalization to use for the MSE loss.
        l1_coefficient (float): The L1 coefficient.
        lp_norm (float): The Lp norm.
        scale_sparsity_penalty_by_decoder_norm (bool): Whether to scale the sparsity penalty by the decoder norm.
        l1_warm_up_steps (int): The number of warm-up steps for the L1 loss.
        lr (float): The learning rate.
        lr_scheduler_name (str): The name of the learning rate scheduler to use.
        lr_warm_up_steps (int): The number of warm-up steps for the learning rate.
        lr_end (float): The end learning rate for the cosine annealing scheduler.
        lr_decay_steps (int): The number of decay steps for the learning rate.
        n_restart_cycles (int): The number of restart cycles for the cosine annealing warm restarts scheduler.
        finetuning_method (str): The method to use for finetuning.
        use_ghost_grads (bool): Whether to use ghost gradients.
        feature_sampling_window (int): The feature sampling window.
        dead_feature_window (int): The dead feature window.
        dead_feature_threshold (float): The dead feature threshold.
        n_eval_batches (int): The number of evaluation batches.
        eval_batch_size_prompts (int): The batch size for evaluation.
        log_to_wandb (bool): Whether to log to Weights & Biases.
        log_activations_store_to_wandb (bool): NOT CURRENTLY USED. Whether to log the activations store to Weights & Biases.
        log_optimizer_state_to_wandb (bool): NOT CURRENTLY USED. Whether to log the optimizer state to Weights & Biases.
        wandb_project (str): The Weights & Biases project to log to.
        wandb_id (str): The Weights & Biases ID.
        run_name (str): The name of the run.
        wandb_entity (str): The Weights & Biases entity.
        wandb_log_frequency (int): The frequency to log to Weights & Biases.
        eval_every_n_wandb_logs (int): The frequency to evaluate.
        resume (bool): Whether to resume training.
        n_checkpoints (int): The number of checkpoints.
        checkpoint_path (str): The path to save checkpoints.
        verbose (bool): Whether to print verbose output.
        model_kwargs (dict[str, Any]): Additional keyword arguments for the model.
        model_from_pretrained_kwargs (dict[str, Any]): Additional keyword arguments for the model from pretrained.
    """

    # VISION-SPECIFIC HYPERPARAMETERS
    store_batch_size: int = 32 # num images ## Sonia: ?? Can we make this better-named? 

    # TO DO
    # put number of imges, number of tokens, but calculate automatically

    l1_loss_wd_norm: bool = False # Not sure what this means either

    # Data Generating Function (Model + Training Distibuion)
    model_name: str = "wkcn/TinyCLIP-ViT-40M-32-Text-19M-LAION400M"
    model_class_name: str = "HookedViT"
    
    # Add a property for hook_name
    @property
    def hook_name(self) -> str:
        return f"blocks.{self.hook_layer}.hook_mlp_out"

    hook_eval: str = "NOT_IN_USE"
    hook_layer: int = 9
    hook_head_index: Optional[int] = None
    
    # Dataset path names
    dataset_name = 'imagenet1k' # Some datasets have hardcoded pre-processing functions
    dataset_path = "/network/scratch/s/sonia.joseph/datasets/kaggle_datasets"
    dataset_train_path: str = "/network/scratch/s/sonia.joseph/datasets/kaggle_datasets/ILSVRC/Data/CLS-LOC/train"
    dataset_val_path: str = "/network/scratch/s/sonia.joseph/datasets/kaggle_datasets/ILSVRC/Data/CLS-LOC/val"
    dataset_trust_remote_code: bool = True
    
    # More dataset functionality
    streaming: bool = True
    is_dataset_tokenized: bool = True
    context_size: int = 50 # this is the patch number
    use_cached_activations: bool = False
    cached_activations_path: Optional[str] = (
        None  # Defaults to "activations/{dataset}/{model}/{full_hook_name}_{hook_head_index}"
    )

    # SAE Parameters
    architecture: Literal["standard", "gated"] = "standard"
    d_in: int = 512
    d_sae: Optional[int] = None
    b_dec_init_method: str = "geometric_median"
    expansion_factor: int = 32
    activation_fn: str = "relu"  # relu, tanh-relu, topk
    activation_fn_kwargs: dict[str, Any] = field(default_factory=dict)  # for topk
    normalize_sae_decoder: bool = False
    noise_scale: float = 0.0
    from_pretrained_path: Optional[str] = None
    apply_b_dec_to_input: bool = True
    decoder_orthogonal_init: bool = False
    decoder_heuristic_init: bool = False
    init_encoder_as_decoder_transpose: bool = True

    # Activation Store Parameters
    n_batches_in_buffer: int = 200
    training_tokens: int = 100_000_000  # Can we calculate this automatically from train? 
    finetuning_tokens: int = 0
    store_batch_size_prompts: int = 32
    normalize_activations: str = (
        "none"  # none, expected_average_only_in (Anthropic April Update), constant_norm_rescale (Anthropic Feb Update)
    )

    # Misc
    device: str = "cuda"
    act_store_device: str = "with_model"  # will be set by post init if with_model
    seed: int = 42
    dtype: str = "float32"  # type: ignore #
    prepend_bos: bool = True

    # Performance - see compilation section of lm_runner.py for info
    autocast: bool = False  # autocast to autocast_dtype during training
    autocast_lm: bool = False  # autocast lm during activation fetching
    compile_llm: bool = False  # use torch.compile on the LLM
    llm_compilation_mode: str | None = None  # which torch.compile mode to use
    compile_sae: bool = False  # use torch.compile on the SAE
    sae_compilation_mode: str | None = None

    # Training Parameters

    ## Batch size
    train_batch_size_tokens: int = 4096

    ## Adam
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999

    ## Loss Function
    mse_loss_normalization: Optional[str] = None
    l1_coefficient: float = 0.01 # 0.00008 # doubled this from 0.00008
    lp_norm: float = 1
    scale_sparsity_penalty_by_decoder_norm: bool = False
    l1_warm_up_steps: int = 0

    ## Learning Rate Schedule
    lr: float = 0.0004 # 0.0004
    lr_scheduler_name: str = (
        "constant"  # constant, cosineannealing, cosineannealingwarmrestarts
    )
    lr_warm_up_steps: int = 0
    lr_end: Optional[float] = None  # only used for cosine annealing, default is lr / 10
    lr_decay_steps: int = 0
    n_restart_cycles: int = 1  # used only for cosineannealingwarmrestarts

    ## FineTuning
    finetuning_method: Optional[str] = None  # scale, decoder or unrotated_decoder

    # Resampling protocol args
    use_ghost_grads: bool = True  
    feature_sampling_window: int = 1000
    dead_feature_window: int = 5000  # unless this window is larger feature sampling,

    dead_feature_threshold: float = 1e-8

    # Evals
    n_eval_batches: int = 10
    eval_batch_size_prompts: int | None = None  # useful if evals cause OOM

    # WANDB
    log_to_wandb: bool = True
    log_activations_store_to_wandb: bool = False
    log_optimizer_state_to_wandb: bool = False
    wandb_project: str = "mats_sae_training_language_model"
    wandb_id: Optional[str] = None
    run_name: Optional[str] = None
    wandb_entity: Optional[str] = None
    wandb_log_frequency: int = 10 #10
    eval_every_n_wandb_logs: int = 30 #100  # logs every 1000 steps.

    # Misc
    resume: bool = False
    n_checkpoints: int = 0
    checkpoint_path: str = "/network/scratch/s/sonia.joseph/checkpoints"
    verbose: bool = True
    model_kwargs: dict[str, Any] = field(default_factory=dict)
    model_from_pretrained_kwargs: dict[str, Any] = field(default_factory=dict)
    vit_prisma_version: str = field(default_factory=lambda: __version__)

    def __post_init__(self):

        if self.resume:
            raise ValueError(
                "Resuming is no longer supported. You can finetune a trained SAE using cfg.from_pretrained path."
                + "If you want to load an SAE with resume=True in the config, please manually set resume=False in that config."
            )

        if self.use_cached_activations and self.cached_activations_path is None:
            self.cached_activations_path = _default_cached_activations_path(
                self.dataset_path,
                self.model_name,
                self.hook_name,
                self.hook_head_index,
            )

        if not isinstance(self.expansion_factor, list):
            self.d_sae = self.d_in * self.expansion_factor
        self.tokens_per_buffer = (
            self.train_batch_size_tokens * self.context_size * self.n_batches_in_buffer
        )

        if self.run_name is None:
            self.run_name = f"Expansion-{self.expansion_factor}-L1-{self.l1_coefficient}-LR-{self.lr}-Tokens-{self.training_tokens:3.3e}"

        if self.b_dec_init_method not in ["geometric_median", "mean", "zeros"]:
            raise ValueError(
                f"b_dec_init_method must be geometric_median, mean, or zeros. Got {self.b_dec_init_method}"
            )

        if self.normalize_sae_decoder and self.decoder_heuristic_init:
            raise ValueError(
                "You can't normalize the decoder and use heuristic initialization."
            )

        if self.normalize_sae_decoder and self.scale_sparsity_penalty_by_decoder_norm:
            raise ValueError(
                "Weighting loss by decoder norm makes no sense if you are normalizing the decoder weight norms to 1"
            )

        # if we use decoder fine tuning, we can't be applying b_dec to the input
        if (self.finetuning_method == "decoder") and (self.apply_b_dec_to_input):
            raise ValueError(
                "If we are fine tuning the decoder, we can't be applying b_dec to the input.\nSet apply_b_dec_to_input to False."
            )

        if self.normalize_activations not in [
            "none",
            "expected_average_only_in",
            "constant_norm_rescale",
            "layer_norm",
        ]:
            raise ValueError(
                f"normalize_activations must be none, expected_average_only_in, or constant_norm_rescale. Got {self.normalize_activations}"
            )

        if self.act_store_device == "with_model":
            self.act_store_device = self.device

        if self.lr_end is None:
            self.lr_end = self.lr / 10

        unique_id = self.wandb_id
        if unique_id is None:
            unique_id = cast(
                Any, wandb
            ).util.generate_id()  # not sure why this type is erroring
        self.checkpoint_path = f"{self.checkpoint_path}/{unique_id}"

        if self.verbose:
            print(
                f"Run name: {self.d_sae}-L1-{self.l1_coefficient}-LR-{self.lr}-Tokens-{self.training_tokens:3.3e}"
            )
            # Print out some useful info:
            n_tokens_per_buffer = (
                self.store_batch_size_prompts
                * self.context_size
                * self.n_batches_in_buffer
            )
            print(f"n_tokens_per_buffer (millions): {n_tokens_per_buffer / 10 ** 6}")
            n_contexts_per_buffer = (
                self.store_batch_size_prompts * self.n_batches_in_buffer
            )
            print(
                f"Lower bound: n_contexts_per_buffer (millions): {n_contexts_per_buffer / 10 ** 6}"
            )

            total_training_steps = (
                self.training_tokens + self.finetuning_tokens
            ) // self.train_batch_size_tokens
            print(f"Total training steps: {total_training_steps}")

            total_wandb_updates = total_training_steps // self.wandb_log_frequency
            print(f"Total wandb updates: {total_wandb_updates}")

            # how many times will we sample dead neurons?
            # assert self.dead_feature_window <= self.feature_sampling_window, "dead_feature_window must be smaller than feature_sampling_window"
            n_feature_window_samples = (
                total_training_steps // self.feature_sampling_window
            )
            print(
                f"n_tokens_per_feature_sampling_window (millions): {(self.feature_sampling_window * self.context_size * self.train_batch_size_tokens) / 10 ** 6}"
            )
            print(
                f"n_tokens_per_dead_feature_window (millions): {(self.dead_feature_window * self.context_size * self.train_batch_size_tokens) / 10 ** 6}"
            )
            print(
                f"We will reset the sparsity calculation {n_feature_window_samples} times."
            )
            # print("Number tokens in dead feature calculation window: ", self.dead_feature_window * self.train_batch_size_tokens)
            print(
                f"Number tokens in sparsity calculation window: {self.feature_sampling_window * self.train_batch_size_tokens:.2e}"
            )

        if self.use_ghost_grads:
            print("Using Ghost Grads.")

    @property
    def total_training_tokens(self) -> int:
        return self.training_tokens + self.finetuning_tokens

    @property
    def total_training_steps(self) -> int:
        return self.total_training_tokens // self.train_batch_size_tokens

    def get_base_sae_cfg_dict(self) -> dict[str, Any]:
        return {
            # TEMP
            "architecture": self.architecture,
            "d_in": self.d_in,
            "d_sae": self.d_sae,
            "dtype": self.dtype,
            "device": self.device,
            "model_name": self.model_name,
            "hook_name": self.hook_name,
            "hook_layer": self.hook_layer,
            "hook_head_index": self.hook_head_index,
            "activation_fn_str": self.activation_fn,
            "apply_b_dec_to_input": self.apply_b_dec_to_input,
            "context_size": self.context_size,
            "prepend_bos": self.prepend_bos,
            "dataset_train_path": self.dataset_train_path,
            "dataset_val_path": self.dataset_val_path,
            "dataset_trust_remote_code": self.dataset_trust_remote_code,
            "finetuning_scaling_factor": self.finetuning_method is not None,
            "sae_lens_training_version": self.vit_prisma_version,
            "normalize_activations": self.normalize_activations,
            "activation_fn_kwargs": self.activation_fn_kwargs,
        }

    def get_training_sae_cfg_dict(self) -> dict[str, Any]:
        return {
            **self.get_base_sae_cfg_dict(),
            "l1_coefficient": self.l1_coefficient,
            "lp_norm": self.lp_norm,
            "use_ghost_grads": self.use_ghost_grads,
            "normalize_sae_decoder": self.normalize_sae_decoder,
            "noise_scale": self.noise_scale,
            "decoder_orthogonal_init": self.decoder_orthogonal_init,
            "mse_loss_normalization": self.mse_loss_normalization,
            "decoder_heuristic_init": self.decoder_heuristic_init,
            "init_encoder_as_decoder_transpose": self.init_encoder_as_decoder_transpose,
            "normalize_activations": self.normalize_activations,
        }

    def to_dict(self) -> dict[str, Any]:

        cfg_dict = {
            **self.__dict__,
            # some args may not be serializable by default
            "dtype": str(self.dtype),
            "device": str(self.device),
            "act_store_device": str(self.act_store_device),
        }

        return cfg_dict

    def to_json(self, path: str) -> None:

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        with open(path + "cfg.json", "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "VisionModelSAERunnerConfig":
        with open(path + "cfg.json", "r") as f:
            cfg = json.load(f)
        return cls(**cfg)


def _default_cached_activations_path(
    dataset_path: str,
    model_name: str,
    hook_name: str,
    hook_head_index: int | None,
) -> str:
    path = f"activations/{dataset_path.replace('/', '_')}/{model_name.replace('/', '_')}/{hook_name}"
    if hook_head_index is not None:
        path += f"_{hook_head_index}"
    return path



def print_config_prettily(config: VisionModelSAERunnerConfig):
    print("\n=== Vision Model SAE Runner Configuration ===\n")

    # Get all fields from the dataclass
    all_fields = fields(config)

    # Group fields by their comment sections
    grouped_fields = {}
    current_group = "Miscellaneous"
    
    for field in all_fields:
        if field.name.isupper() and field.name.endswith("PARAMETERS"):
            current_group = field.name
            continue
        
        if current_group not in grouped_fields:
            grouped_fields[current_group] = []
        
        grouped_fields[current_group].append(field)

    # Print each group
    for group, group_fields in grouped_fields.items():
        print(f"\n--- {group} ---\n")
        
        max_name_length = max(len(field.name) for field in group_fields)
        
        for field in group_fields:
            value = getattr(config, field.name)
            if isinstance(value, str) and len(value) > 50:
                value = value[:47] + "..."
            print(f"{field.name:<{max_name_length}} : {value}")

    print("\n=== End of Configuration ===\n")


@dataclass
class CacheActivationsRunnerConfig:
    """
    Configuration for caching activations of an LLM.
    """

    # Data Generating Function (Model + Training Distibuion)
    model_name: str = "wkcn/TinyCLIP-ViT-8M-16-Text-3M-YFCC15M"
    model_class_name: str = "HookedVit"
    hook_name: str = "blocks.{layer}.hook_mlp_out"
    hook_layer: int = 0
    hook_head_index: Optional[int] = None
    dataset_train_path: str = ""
    dataset_val_path: str = ""
    dataset_trust_remote_code: bool | None = None
    streaming: bool = True
    context_size: int = 50
    new_cached_activations_path: Optional[str] = (
        None  # Defaults to "activations/{dataset}/{model}/{full_hook_name}_{hook_head_index}"
    )
    # dont' specify this since you don't want to load from disk with the cache runner.
    cached_activations_path: Optional[str] = None
    # SAE Parameters
    d_in: int = 512

    # Activation Store Parameters
    n_batches_in_buffer: int = 20
    training_tokens: int = 2_000_000
    store_batch_size_prompts: int = 32
    train_batch_size_tokens: int = 4096
    normalize_activations: str = "none"  # should always be none for activation caching

    # Misc
    device: str = "cpu"
    act_store_device: str = "with_model"  # will be set by post init if with_model
    seed: int = 42
    dtype: str = "float32"
    prepend_bos: bool = True
    autocast_lm: bool = False  # autocast lm during activation fetching

    # Activation caching stuff
    shuffle_every_n_buffers: int = 10
    n_shuffles_with_last_section: int = 10
    n_shuffles_in_entire_dir: int = 10
    n_shuffles_final: int = 100
    model_kwargs: dict[str, Any] = field(default_factory=dict)
    model_from_pretrained_kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Autofill cached_activations_path unless the user overrode it
        if self.new_cached_activations_path is None:
            self.new_cached_activations_path = _default_cached_activations_path(
                self.dataset_path,
                self.model_name,
                self.hook_name,
                self.hook_head_index,
            )

        if self.act_store_device == "with_model":
            self.act_store_device = self.device


