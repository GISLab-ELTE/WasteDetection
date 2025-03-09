import numpy as np
from model.treshold import Treshold
from typing import List


def create_heatmap(probabilities: np.ndarray, tresholds: List[Treshold]) -> np.ndarray:
    """
    Creates a heatmap based on given probabilites.
    Tresholds towards the beginning of the list may get overriden by tresholds in the end of the list.
    :param probabilities: an array containing probabilities
    :param nan_mask: a mask signaling where nan values are.
    :param tresholds: a list of Treshold items which are used to mask the heatmap with given values.
    :returns: a heatmap that contains values according to the given tresholds.
    """
    heatmap = np.zeros(shape=probabilities.shape, dtype=int)
    for treshold in tresholds:
        heatmap[probabilities >= treshold.percentage] = treshold.label

    return heatmap
