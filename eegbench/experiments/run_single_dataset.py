"""Run one classifier on one EEG dataset with tsml-eval.

This is the smallest complete example of generating results in the format the
rest of this repository reads. tsml-eval writes one file per classifier,
dataset and resample

    <results_path>/<classifier>/Predictions/<dataset>/testResample<id>.csv

containing the class labels, the predictions, the probability estimates and the
fit and predict times. Those files are the input to eegbench.experiments.ingest.

Only resample 0, the default split, is used. The default splits keep each
subject on one side, and tsml-eval's other resamples are stratified by class
alone, so they would put the same subject in train and test.

Edit the settings in main and run it with

    python -m eegbench.experiments.run_single_dataset

The classifier name is anything tsml-eval can resolve, which covers the aeon
classifiers. For anything else, pass the estimator to single_experiment instead
of leaving it to be looked up by name: the EEG specific classifiers are in
aeon-neuro and the ports of general multivariate classifiers are in
multiverse.classification. Neither is kept in this repository.
"""

from tsml_eval.experiments import (
    get_classifier_by_name,
    load_and_run_classification_experiment,
)

data_path = "C:/Data/EEG"
results_path = "./results-raw"


def single_experiment(dataset, classifier_name, classifier=None, random_state=0):
    """Run one classifier on the default split of one dataset."""
    if classifier is None:
        classifier = get_classifier_by_name(classifier_name, random_state=random_state)
    load_and_run_classification_experiment(
        problem_path=data_path,
        results_path=results_path,
        dataset=dataset,
        classifier=classifier,
        classifier_name=classifier_name,
        resample_id=0,
        overwrite=False,
    )


def main():
    dataset = "Blink"
    classifier = "MRHydra"

    single_experiment(dataset, classifier)
    print(f"{classifier} on {dataset} written to {results_path}")


if __name__ == "__main__":
    main()
