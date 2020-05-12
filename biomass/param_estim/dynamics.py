import os
import re
import numpy as np

from biomass import model
from biomass.observable import observables, NumericalSimulation
from biomass.param_estim import plot_func, search_parameter_index


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
    x = model.f_params()
    y0 = model.initial_values()
    sim = NumericalSimulation()

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
                (sim, successful) = _validate(nth_paramset, x, y0)
                if successful:
                    for j, _ in enumerate(observables):
                        simulations_all[j, i, :, :] = sim.simulations[j, :, :]

            best_fitness_all = np.full(len(n_file), np.inf)
            for i, nth_paramset in enumerate(n_file):
                if os.path.isfile('./out/{:d}/best_fitness.npy'.format(nth_paramset)):
                    best_fitness_all[i] = np.load(
                        './out/{:d}/best_fitness.npy'.format(
                            nth_paramset
                        )
                    )
            best_paramset = n_file[np.argmin(best_fitness_all)]
            write_best_fit_param(best_paramset, x, y0)

            if viz_type == 'average':
                pass
            elif viz_type == 'best':
                sim, _ = _validate(int(best_paramset), x, y0)
            else:
                sim, _ = _validate(int(viz_type), x, y0)

            if len(n_file) >= 2:
                save_param_range(n_file, x, y0, portrait=True)
        else:
            if sim.simulate(x, y0) is not None:
                print(
                    'Simulation failed.'
                )
    plot_func.timecourse(
        sim, n_file, viz_type, show_all, stdev, simulations_all
    )


def update_param(paramset, x, y0):
    search_idx = search_parameter_index()

    if os.path.isfile('./out/{:d}/generation.npy'.format(paramset)):
        best_generation = np.load(
            './out/{:d}/generation.npy'.format(
                paramset
            )
        )
        best_indiv = np.load(
            './out/{:d}/fit_param{:d}.npy'.format(
                paramset, int(best_generation)
            )
        )
        for i, j in enumerate(search_idx[0]):
            x[j] = best_indiv[i]
        for i, j in enumerate(search_idx[1]):
            y0[j] = best_indiv[i+len(search_idx[0])]

    return x, y0


def _validate(nth_paramset, x, y0):
    """Validates the dynamical viability of a set of estimated parameter values.
    """
    sim = NumericalSimulation()

    (x, y0) = update_param(nth_paramset, x, y0)

    if sim.simulate(x, y0) is None:
        return sim, True
    else:
        print(
            'Simulation failed.\nparameter_set #{:d}'.format(
                nth_paramset
            )
        )
        return sim, False


def write_best_fit_param(best_paramset, x, y0):

    (x, y0) = update_param(best_paramset, x, y0)

    with open('./out/best_fit_param.txt', mode='w') as f:
        f.write(
            '# param set: {:d}\n'.format(
                best_paramset
            )
        )
        f.write(
            '\n### Param. const\n'
        )
        for i in range(model.C.len_f_params):
            f.write(
                'x[C.{}] = {:8.3e}\n'.format(
                    model.C.param_names[i], x[i]
                )
            )
        f.write(
            '\n### Non-zero initial conditions\n'
        )
        for i in range(model.V.len_f_vars):
            if y0[i] != 0:
                f.write(
                    'y0[V.{}] = {:8.3e}\n'.format(
                        model.V.var_names[i], y0[i]
                    )
                )


def save_param_range(n_file, x, y0, portrait):
    search_idx = search_parameter_index()
    search_param_matrix = np.empty(
        (len(n_file), len(search_idx[0]) + len(search_idx[1]))
    )
    for k, nth_paramset in enumerate(n_file):
        if os.path.isfile('./out/{:d}/generation.npy'.format(nth_paramset)):
            best_generation = np.load(
                './out/{:d}/generation.npy'.format(
                    nth_paramset
                )
            )
            best_indiv = np.load(
                './out/{:d}/fit_param{:d}.npy'.format(
                    nth_paramset, int(best_generation)
                )
            )
        else:
            best_indiv = np.empty(
                len(search_idx[0]) + len(search_idx[1])
            )
            for i, j in enumerate(search_idx[0]):
                best_indiv[i] = x[j]
            for i, j in enumerate(search_idx[1]):
                best_indiv[i+len(search_idx[0])] = y0[j]

        search_param_matrix[k, :] = best_indiv

    plot_func.param_range(
        search_idx, search_param_matrix, portrait
    )
