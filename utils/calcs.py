"""functions to calculate stuff."""

from statsmodels.stats.contingency_tables import Table2x2
from typing import Union, Tuple, List


def odds_ratio(
    condition1_yes_no: Union[Tuple[int], List[int]],
    condition2_yes_no: Union[Tuple[int], List[int]],
    ci: float = 0.95,
):
    """Computes the odds ratio and the upper and lower bounds of the confidence interval
    Args:
        condition1_yes_no: with condition 1 [# with event, # without event]
        condition2_yes_no: with condition 2 [# with event, # without event]
        ci: float b/w 0 and 1 (confidence interval) = (1- alpha)
    Returns:
        tuple: odds ratio for data, lower bound, upper bound (all floats)
    """
    if (ci < 0) | (ci > 1):
        raise ValueError("Confidence interval value must be between 0 and 1")
    if (
        (not isinstance(condition1_yes_no, list))
        | (not isinstance(condition2_yes_no, list))
        | (len(condition1_yes_no) != 2)
        | (len(condition2_yes_no) != 2)
    ):
        raise TypeError(
            "Arguments condition1_yes_no and condition2_yes_no should be two-member lists of integer values"
        )

    t = Table2x2([condition1_yes_no, condition2_yes_no])
    upper_lower = t.oddsratio_confint((1 - ci))
    return t.oddsratio, upper_lower[0], upper_lower[1]
