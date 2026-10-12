"""Run a set of classifiers over the EEG archive with tsml-eval.

Note this is for guidance only, showing how to access the classifiers and
datasets. Running it like this on a single machine will take a very long time:
HC2 alone averaged 78 hours a dataset in the paper, and the published results
were distributed over a cluster.

Every combination writes one file

    <results_path>/<classifier>/Predictions/<dataset>/testResample0.csv

Combinations that already have a result file are skipped, so an interrupted run
can be started again. A combination that fails is reported and the run
continues.

Edit the settings in main and run it with

    python -m eegbench.experiments.run_benchmark
"""

from eegbench.datasets import eegbench_open
from eegbench.experiments.run_single_dataset import single_experiment


def main():
    classifiers = ["MRHydra", "HC2"]
    datasets = sorted(eegbench_open)

    print(f"{len(classifiers)} classifiers x {len(datasets)} datasets")
    for classifier in classifiers:
        for dataset in datasets:
            try:
                single_experiment(dataset, classifier)
                print(f"  done   {classifier} {dataset}")
            except Exception as e:
                print(f"  failed {classifier} {dataset}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
