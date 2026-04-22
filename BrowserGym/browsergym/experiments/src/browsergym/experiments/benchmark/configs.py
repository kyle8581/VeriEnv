import numpy as np
from browsergym.experiments.benchmark.metadata.utils import (
    task_list_from_metadata,
    task_metadata,
)
from browsergym.experiments.loop import EnvArgs
from browsergym.experiments.benchmark.utils import (
    make_env_args_list_from_fixed_seeds,
    make_env_args_list_from_repeat_tasks,
    make_env_args_list_from_workarena_curriculum,
)

from .base import Benchmark, HighLevelActionSetArgs

# These are mean as the default highlevel action set to fairly evaluate agents on each benchmark.
# They are mostly arbitrary, the important thing is to evaluate different agents using the same action set for fairness.
DEFAULT_HIGHLEVEL_ACTION_SET_ARGS = {
    "miniwob_all": HighLevelActionSetArgs(
        subsets=["miniwob_all"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    "miniwob_liu18": HighLevelActionSetArgs(
        subsets=["miniwob_liu18"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    "miniwob_shi17": HighLevelActionSetArgs(
        subsets=["miniwob_shi17"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    "miniwob_humphreys22": HighLevelActionSetArgs(
        subsets=["miniwob_humphreys22"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    "workarena": HighLevelActionSetArgs(
        subsets=["workarena"],  # no need for infeasible action
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    "workarena++": HighLevelActionSetArgs(
        subsets=["workarena++"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    # from https://arxiv.org/abs/2307.13854
    "webarena": HighLevelActionSetArgs(
        subsets=["webarena"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    # from https://arxiv.org/abs/2401.13649
    "visualwebarena": HighLevelActionSetArgs(
        subsets=["visualwebarena"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    "assistantbench": HighLevelActionSetArgs(
        subsets=["assistantbench"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    "weblinx": HighLevelActionSetArgs(
        subsets=["weblinx"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    "mind2webonline": HighLevelActionSetArgs(
        subsets=["webarena"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
    "webvoyager": HighLevelActionSetArgs(
        subsets=["webarena"],
        multiaction=False,
        strict=False,
        retry_with_force=True,
        demo_mode="off",
    ),
}

# ----------------------------
# VeriEnv (local websites)
# ----------------------------


def _make_verienv_site_benchmark(site: str, n_repeats: int = 1) -> Benchmark:
    import json
    from pathlib import Path

    root = Path(os.getenv("CLONE_CODING_ROOT", str(Path(__file__).resolve().parents[5]))).resolve()
    path = root / "websites" / site / "task_instructions.json"
    tasks = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        tasks = data if isinstance(data, list) else (data.get("tasks") or [])
        if not isinstance(tasks, list):
            tasks = []
    except Exception:
        tasks = []

    def _max_steps(t: dict) -> int:
        # Fixed max_steps for all VeriEnv tasks
        return 30

    env_args_list = []
    for idx, t in enumerate(tasks):
        if not isinstance(t, dict):
            continue
        if t.get("is_valid") is False:
            continue
        task_name = f"verienv.{site}.{idx}"
        for _ in range(max(1, int(n_repeats))):
            env_args_list.append(
                EnvArgs(
                    task_name=task_name,
                    task_seed=0,
                    max_steps=_max_steps(t),
                )
            )

    return Benchmark(
        name=f"verienv_{site}",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["webarena"],
        is_multi_tab=False,
        supports_parallel_seeds=True,
        backends=[],
        env_args_list=env_args_list,
        task_metadata=None,
    )


def _make_webvoyager_benchmark(n_repeats: int = 1, max_tasks: int = 0) -> Benchmark:
    """Build a WebVoyager benchmark from the original WebVoyager JSONL file (643 tasks).

    Args:
        n_repeats: number of times to repeat each task.
        max_tasks: maximum number of tasks to include (0 = all 643).
    """
    import json
    import os

    data_path = os.getenv(
        "WEBVOYAGER_DATA_PATH",
        os.path.join(os.getenv("CLONE_CODING_ROOT", "."), "tools", "webvoyager_original.jsonl"),
    )

    task_ids: list[str] = []
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                tid = d.get("id", str(len(task_ids))).replace(" ", "_")
                task_ids.append(f"webvoyager.{tid}")
                if 0 < max_tasks <= len(task_ids):
                    break

    env_args_list = []
    for tid in task_ids:
        for _ in range(max(1, int(n_repeats))):
            env_args_list.append(
                EnvArgs(
                    task_name=tid,
                    task_seed=0,
                    max_steps=30,
                )
            )

    return Benchmark(
        name="webvoyager",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["webvoyager"],
        is_multi_tab=True,
        supports_parallel_seeds=True,
        backends=[],
        env_args_list=env_args_list,
        task_metadata=None,
    )


# all benchmarks are callables designed for lazy loading, i.e. `bench = DEFAULT_BENCHMARKS["miniwob_all"]()`
DEFAULT_BENCHMARKS = {
    "miniwob": lambda n_repeats=5: Benchmark(
        name="miniwob",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["miniwob_all"],
        is_multi_tab=False,
        supports_parallel_seeds=True,
        backends=["miniwob"],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=task_list_from_metadata(metadata=task_metadata("miniwob")),
            max_steps=10,
            n_repeats=n_repeats,
            seeds_rng=np.random.RandomState(42),
        ),
        task_metadata=task_metadata("miniwob"),
    ),
    "miniwob_tiny_test": lambda n_repeats=2: Benchmark(
        name="miniwob_tiny_test",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["miniwob_all"],
        is_multi_tab=False,
        supports_parallel_seeds=True,
        backends=["miniwob"],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=["miniwob.click-dialog", "miniwob.click-checkboxes"],
            max_steps=5,
            n_repeats=n_repeats,
            seeds_rng=np.random.RandomState(42),
        ),
        task_metadata=task_metadata("miniwob"),
    ),
    "webarena": lambda n_repeats=1: Benchmark(
        name="webarena",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["webarena"],
        is_multi_tab=True,
        supports_parallel_seeds=False,
        backends=["webarena"],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=task_list_from_metadata(metadata=task_metadata("webarena")),
            max_steps=30,
            n_repeats=n_repeats,
            seeds_rng=np.random.RandomState(42),
        ),
        task_metadata=task_metadata("webarena"),
    ),
    "webarena_lite": lambda n_repeats=1: Benchmark(
        name="webarena_lite",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["webarena"],
        is_multi_tab=True,
        supports_parallel_seeds=False,
        backends=["webarena"],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=task_list_from_metadata(metadata=task_metadata("webarenalite")),
            max_steps=30,
            n_repeats=n_repeats,
            seeds_rng=np.random.RandomState(42),
        ),
        task_metadata=task_metadata("webarenalite"),
    ),
    "webarena_tiny": lambda n_repeats=1: Benchmark(
        name="webarena_tiny",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["webarena"],
        is_multi_tab=True,
        supports_parallel_seeds=False,
        backends=["webarena"],
        env_args_list=make_env_args_list_from_fixed_seeds(
            task_list=[
                "webarena.410",
                "webarena.533",
                "webarena.537",
                "webarena.552",
                "webarena.561",
                "webarena.562",
            ],
            max_steps=30,
            fixed_seeds=[0],
        ),
        task_metadata=task_metadata("webarena"),
    ),
    "visualwebarena_tiny": lambda n_repeats=10: Benchmark(
        name="visualwebarena_tiny",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["visualwebarena"],
        is_multi_tab=True,
        supports_parallel_seeds=False,
        backends=["visualwebarena"],
        env_args_list=make_env_args_list_from_fixed_seeds(
            task_list=[
                "visualwebarena.228",
                "visualwebarena.263",
                "visualwebarena.550",
                "visualwebarena.784",
            ],
            max_steps=30,
            fixed_seeds=[0],
        ),
        task_metadata=task_metadata("visualwebarena"),
    ),
    "visualwebarena": lambda n_repeats=1: Benchmark(
        name="visualwebarena",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["visualwebarena"],
        is_multi_tab=True,
        supports_parallel_seeds=False,
        backends=["visualwebarena"],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=task_list_from_metadata(metadata=task_metadata("visualwebarena")),
            max_steps=30,
            n_repeats=n_repeats,
            seeds_rng=np.random.RandomState(42),
        ),
        task_metadata=task_metadata("visualwebarena"),
    ),
    "workarena_l1": lambda n_repeats=10: Benchmark(
        name="workarena_l1",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["workarena"],
        is_multi_tab=False,
        supports_parallel_seeds=True,
        backends=["workarena"],
        env_args_list=make_env_args_list_from_workarena_curriculum(
            level="l1",
            task_category_filter=None,
            meta_seed=42,  # meta seed for evaluation curriculum
            max_steps=15,
            curriculum_type="agent",
            seeds_l1=n_repeats,
        ),
        task_metadata=task_metadata("workarena"),
    ),
    "workarena_l2_agent_curriculum_eval": lambda n_repeats=1: Benchmark(
        name="workarena_l2_agent_curriculum_eval",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["workarena++"],
        is_multi_tab=True,
        supports_parallel_seeds=True,
        backends=["workarena"],
        env_args_list=make_env_args_list_from_workarena_curriculum(
            level="l2",
            task_category_filter=None,
            meta_seed=42,  # meta seed for evaluation curriculum
            max_steps=50,
            curriculum_type="agent",
        ),
        task_metadata=task_metadata("workarena"),
    ),
    "workarena_l3_agent_curriculum_eval": lambda n_repeats=1: Benchmark(
        name="workarena_l3_agent_curriculum_eval",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["workarena++"],
        is_multi_tab=True,
        supports_parallel_seeds=True,
        backends=["workarena"],
        env_args_list=make_env_args_list_from_workarena_curriculum(
            level="l3",
            task_category_filter=None,
            meta_seed=42,  # meta seed for evaluation curriculum
            max_steps=50,
            curriculum_type="agent",
        ),
        task_metadata=task_metadata("workarena"),
    ),
    "assistantbench": lambda n_repeats=1: Benchmark(
        name="assistantbench",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["assistantbench"],
        is_multi_tab=True,
        supports_parallel_seeds=True,
        backends=["assistantbench"],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=task_list_from_metadata(
                metadata=task_metadata("assistantbench"), filter={"browsergym_split": "valid|test"}
            ),
            max_steps=30,
            n_repeats=n_repeats,
            seeds_rng=np.random.RandomState(42),
        ),
        task_metadata=task_metadata("assistantbench"),
    ),
    "weblinx": lambda n_repeats=1: Benchmark(
        name="weblinx",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["weblinx"],
        is_multi_tab=True,
        supports_parallel_seeds=True,
        backends=["weblinx"],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=task_list_from_metadata(metadata=task_metadata("weblinx")),
            max_steps=1,
            n_repeats=n_repeats,
            seeds_rng=np.random.RandomState(42),
        ),
        task_metadata=task_metadata("weblinx"),
    ),
    "mind2webonline": lambda n_repeats=1: Benchmark(
        name="mind2webonline",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["mind2webonline"],
        is_multi_tab=True,
        supports_parallel_seeds=True,
        backends=[],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=task_list_from_metadata(metadata=task_metadata("mind2webonline_accessible")),
            max_steps=30,
            n_repeats=n_repeats,
            seeds_rng=np.random.RandomState(42),
        ),
        task_metadata=task_metadata("mind2webonline_accessible"),
    ),
    # WebVoyager: live-website tasks with VLM judge evaluation
    "webvoyager": lambda n_repeats=1, max_tasks=0: _make_webvoyager_benchmark(
        n_repeats=n_repeats, max_tasks=max_tasks
    ),
    # VeriEnv: local websites/*/task_instructions.json
    # Server lifecycle is handled by AgentLab/experiments/run_verienv.py (or your own runner).
    # Dynamic registration happens below via _register_all_verienv_benchmarks()
}


def _register_all_verienv_benchmarks() -> None:
    """Dynamically register all verienv benchmarks from websites/ directory."""
    import os
    from pathlib import Path

    root = Path(os.getenv("CLONE_CODING_ROOT", str(Path(__file__).resolve().parents[5]))).resolve()
    websites_dir = root / "websites"
    if not websites_dir.is_dir():
        return

    for site_dir in sorted(websites_dir.iterdir()):
        if not site_dir.is_dir():
            continue
        task_file = site_dir / "task_instructions.json"
        if not task_file.exists():
            continue

        site = site_dir.name
        bench_name = f"verienv_{site}"
        if bench_name not in DEFAULT_BENCHMARKS:
            # Use default argument to capture site in closure
            DEFAULT_BENCHMARKS[bench_name] = (
                lambda n_repeats=1, _site=site: _make_verienv_site_benchmark(_site, n_repeats=n_repeats)
            )


# Register all verienv benchmarks on module load
_register_all_verienv_benchmarks()
