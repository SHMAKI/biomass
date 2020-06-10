import os
import re
import numpy as np

from biomass.current_model import (param_values, initial_values, observables,
                                    NumericalSimulation, get_search_index)
from biomass.param_estim import plot_func
from .load_out import load_param, write_best_fit_param, get_optimized_param


def _validate(nth_paramset):
    """Validates the dynamical viability of a set of estimated parameter values.
    """
    sim = NumericalSimulation()

    (x, y0) = load_param(nth_paramset)

    if sim.simulate(x, y0) is None:
        return sim, True
    else:
        print(
            'Simulation failed.\nparameter_set #{:d}'.format(
                nth_paramset
            )
        )
        return sim, False


def simulate_all(viz_type, show_all, stdev):
    """Simulate ODE model with estimated parameter values.

    Parameters
    ----------
    viz_type : str
        - 'average': The average of simulation results with parameter sets in "out/".
        - 'best': The best simulation result in "out/", simulation with "best_fit_param".
        - 'original': Simulation with the default parameters and initial values defined in "biomass/model/".
        - 'n(=1,2,...)': Use the parameter set in "out/n/".

    show_all : bool
        Whether to show all simulation results.
        
    stdev : bool
        If True, the standard deviation of simulated values will be shown
        (only available for 'average' visualization type).
        
    """
    sim = NumericalSimulation()

    search_idx = get_search_index()
    
    n_file = []
    if viz_type != 'original':
        if os.path.isdir('./out'):
            fit_param_files = os.listdir('./out')
            for file in fit_param_files:
                if re.match(r'\d', file):
                    n_file.append(int(file))
    simulations_all = np.full(
        (len(observables), len(n_file), len(sim.t), len(sim.conditions)),
        np.nan
    )
    if viz_type != 'experiment':
        if len(n_file) > 0:
            if len(n_file) == 1 and viz_type == 'average':
                viz_type = 'best'
            for i, nth_paramset in enumerate(n_file):
                if os.path.isfile('./out/{:d}/generation.npy'.format(nth_paramset)):
                    (sim, successful) = _validate(nth_paramset)
                    if successful:
                        for j, _ in enumerate(observables):
                            simulations_all[j, i, :, :] = sim.simulations[j, :, :]
                else:
                    continue

            best_fitness_all = np.full(len(n_file), np.inf)
            for i, nth_paramset in enumerate(n_file):
                if os.path.isfile('./out/{:d}/best_fitness.npy'.format(nth_paramset)):
                    best_fitness_all[i] = np.load(
                        './out/{:d}/best_fitness.npy'.format(
                            nth_paramset
                        )
                    )
            best_paramset = n_file[np.argmin(best_fitness_all)]
            write_best_fit_param(best_paramset)

            if viz_type == 'average':
                pass
            elif viz_type == 'best':
                sim, _ = _validate(int(best_paramset))
            else:
                sim, _ = _validate(int(viz_type))

            if 2 <= len(n_file):
                popt = get_optimized_param(n_file, search_idx)
                plot_func.param_range(
                    search_idx, popt, portrait=True
                )
        else:
            x = param_values()
            y0 = initial_values()
            if sim.simulate(x, y0) is not None:
                print(
                    'Simulation failed.'
                )
    plot_func.timecourse(
        sim, n_file, viz_type, show_all, stdev, simulations_all
    )