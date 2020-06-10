import warnings
warnings.filterwarnings('ignore')

from biomass.models.Nakakuki_Cell_2010 import *
from biomass.dynamics import SignalingSystems

if __name__ == '__main__':
    erbb_network = SignalingSystems(
        parameters=C.parameters,
        species=V.species,
        pval=param_values,
        ival=initial_values,
        obs=observables,
        sim=NumericalSimulation(),
        exp=ExperimentalData(),
        sp=SearchParam()
    )
    erbb_network.simulate_all(viz_type='average', show_all=False, stdev=True)