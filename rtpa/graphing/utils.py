import os
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import AutoMinorLocator, MaxNLocator
import matplotlib.patches as mpatches

def plot_bar_with_ci(x, means, cis, significant, title, xlabel, ylabel, filename):
    plt.style.use('./rose-pine-dawn.mplstyle')
    valid = ~np.isnan(means)
    x = np.array(x)[valid]
    means = np.array(means)[valid]
    cis = np.array(cis)[:, valid]
    significant = np.array(significant)[valid]
    error = np.abs(cis - means) if cis.ndim == 2 else None

    if len(x) > 10:
        fig, ax = plt.subplots(figsize=(len(x), 8))
    else:
        fig, ax = plt.subplots()

    non_sig_color = 'lightgrey'
    sig_color = '#FFD580'
    sig_patch = mpatches.Patch(color=sig_color, label='Significant')
    non_sig_patch = mpatches.Patch(color=non_sig_color, label='Not Significant')
    plt.legend(handles=[sig_patch, non_sig_patch])

    for xi, mean, err, sig in zip(x, means, error.T if error is not None else [None]*len(means), significant):
        color = sig_color if sig else non_sig_color
        ax.bar(xi, mean, color=color, edgecolor='black',
               yerr=err.reshape(2, 1) if err is not None else None, capsize=5)

    ax.axhline(y=0, color='grey', linestyle='--', linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(x, rotation=45, ha='right')
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_major_locator(MaxNLocator(10))
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)
    fig.savefig(f'{filename}.png', bbox_inches='tight')
    plt.close(fig)
    return f"{filename}.png"
