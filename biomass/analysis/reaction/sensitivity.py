import os
import sys
import re
import numpy as np
from math import fabs, log
from scipy.integrate import simps

from biomass.model.name2idx import parameters as C
from biomass.model.name2idx import variables as V
from biomass.model import differential_equation as ode
from biomass.model.param_const import f_params
from biomass.model.initial_condition import initial_values
from biomass.observable import observables, NumericalSimulation
from biomass.param_estim.search_parameter import search_parameter_index


def get_duration(time_course_vector):
    """
    Calculation of the duration as the time it takes to decline below 10% of its maximum
    """
    maximum_value = np.max(time_course_vector)
    t_max = np.argmax(time_course_vector)
    time_course_vector = time_course_vector - 0.1*maximum_value
    time_course_vector[time_course_vector > 0.0] = -np.inf
    duration = np.argmax(time_course_vector[t_max:]) + t_max

    return duration


def analyze_sensitivity(metric, num_reaction):
    """Compute sensitivity coefficients

    Parameters
    ----------
    metric: str
        - 'amplitude': The maximum value.
        - 'duration': The time it takes to decline below 10% of its maximum.
        - 'integral': The integral of concentration over the observation time.
    num_reaction: int
        len(v) in model/differential_equation.py

    Returns
    -------
    sensitivity_coefficients: numpy array
    
    """
    sim = NumericalSimulation()

    rate = 1.01  # 1% change
    epsilon = 1e-9  # If |M - M*| < epsilon, sensitivity_coefficient = 0

    x = f_params()
    y0 = initial_values()

    n_file = []
    fitparam_files = os.listdir('./out')
    for file in fitparam_files:
        if re.match(r'\d', file):
            n_file.append(int(file))

    signaling_metric = np.full(
        (len(n_file), num_reaction, len(observables), len(sim.conditions)), np.nan
    )
    search_idx = search_parameter_index()
    for i, nth_paramset in enumerate(n_file):
        if os.path.isfile('./out/%d/generation.npy' % (nth_paramset)):
            best_generation = np.load(
                './out/%d/generation.npy' % (
                    nth_paramset
                )
            )
            best_indiv = np.load(
                './out/%d/fit_param%d.npy' % (
                    nth_paramset, int(best_generation)
                )
            )
            for m, n in enumerate(search_idx[0]):
                x[n] = best_indiv[m]
            for m, n in enumerate(search_idx[1]):
                y0[n] = best_indiv[m+len(search_idx[0])]
            for j in range(num_reaction):
                ode.perturbation = [1]*num_reaction
                ode.perturbation[j] = rate
                if sim.simulate(x, y0) is None:
                    for k, _ in enumerate(observables):
                        for l, _ in enumerate(sim.conditions):
                            if metric == 'amplitude':
                                signaling_metric[i, j, k, l] = np.max(
                                    sim.simulations[k, :, l]
                                )
                            elif metric == 'duration':
                                signaling_metric[i, j, k, l] = get_duration(
                                    sim.simulations[k, :, l]
                                )
                            elif metric == 'integral':
                                signaling_metric[i, j, k, l] = simps(
                                    sim.simulations[k, :, l]
                                )
                            else:
                                raise ValueError(
                                    "metric ∈ {'amplitude', 'duration', 'integral'}"
                                )
                sys.stdout.write(
                    '\r%d / %d' % (
                        i*num_reaction+j+1, len(n_file)*num_reaction
                    )
                )
    sensitivity_coefficients = np.empty_like(signaling_metric)
    for i, _ in enumerate(n_file):
        for j in range(num_reaction):
            for k, _ in enumerate(observables):
                for l, _ in enumerate(sim.conditions):
                    if np.isnan(signaling_metric[i, j, k, l]):
                        sensitivity_coefficients[i, j, k, l] = np.nan
                    elif fabs(
                        signaling_metric[i, j, k, l] - signaling_metric[i, 0, k, l]
                    ) < epsilon or (
                        signaling_metric[i, j, k, l] / signaling_metric[i, 0, k, l]
                    ) < 0:
                        sensitivity_coefficients[i, j, k, l] = 0.0
                    else:
                        sensitivity_coefficients[i, j, k, l] = (
                            log(
                                signaling_metric[i, j, k, l] /
                                signaling_metric[i, 0, k, l]
                            ) / log(rate)
                        )
    return sensitivity_coefficients
