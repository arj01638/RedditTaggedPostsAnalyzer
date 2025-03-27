from scipy import stats

def perform_analysis_with_groups(group_with_value, group_without_value, metric, confidence_level):
    # Perform an independent two-sample T-test
    t_stat, p_value = stats.ttest_ind(
        group_with_value[metric],
        group_without_value[metric],
        equal_var=False,
        nan_policy='omit'
    )

    mean_diff, ci_low, ci_high = calculate_confidence_interval(
        group_with_value, group_without_value, metric, confidence_level
    )
    return mean_diff, ci_low, ci_high, p_value, t_stat

def calculate_confidence_interval(group1, group2, metric, confidence_level):
    se1 = stats.sem(group1[metric], nan_policy='omit')
    se2 = stats.sem(group2[metric], nan_policy='omit')
    se_diff = (se1 ** 2 + se2 ** 2) ** 0.5
    df = min(len(group1[metric]) - 1, len(group2[metric]) - 1)
    t_critical = stats.t.ppf((1 + confidence_level) / 2, df)
    mean_diff = group1[metric].mean() - group2[metric].mean()
    ci_low = mean_diff - t_critical * se_diff
    ci_high = mean_diff + t_critical * se_diff
    return mean_diff, ci_low, ci_high
