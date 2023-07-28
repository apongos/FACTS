#!/usr/bin/env python3
# Public version

# Based on Kim et al. (in review) 
# Released Nov 2022

# Purpose: Main file to run FACTS.

# Contributors:
# Kwang S. Kim
# Jessica L. Gaines
# Vikram Ramanarayanan
# Ben Parrell
# Srikantan Nagarajan
# John Houde

import global_variables as gv
import sys
import numpy as np
import matplotlib.pyplot as plt
import configparser
from FACTS_Modules.Model import model_factory
from FACTS_Modules.util import string2dtype_array
from FACTS_Modules.TADA import MakeGestScore
from facts_visualizations import single_trial_plots, multi_trial_plots
import os 
import pdb

def facts_for_SBI(theta):
    ini='DesignA_pert.ini'
    gFile='GesturalScores/KimetalOnlinepert2.G',
    config = configparser.ConfigParser()
    config.read(ini)

    # Replace the parameter value from ini file
    print(config)
    config['SensoryNoise']['Somato_sensor_scale'] = theta

    model = model_factory(config)
    #pdb.set_trace()
    if 'MultTrials' in config.sections(): 
        ntrials = int(config['MultTrials']['ntrials'])
        target_noise= float(config['MultTrials']['Target_noise'])
    else: 
        ntrials = 1
        target_noise = 0

    gest_name = gFile.split('/')[-1]
    np.random.seed(100)
    GestScore, ART, ms_frm, last_frm = MakeGestScore(gFile,target_noise)
    
    # initialize vectors to monitor position at each timestep
    a_record = np.empty([ntrials,last_frm,gv.a_dim])
    x_record = np.empty([ntrials,last_frm,gv.x_dim])
    formant_record = np.empty([ntrials,last_frm,3])
    shift_record = np.empty([ntrials,last_frm,3])
    a_tilde_record = np.empty([ntrials,last_frm,gv.a_dim])
    a_dot_record = np.empty([ntrials,last_frm,gv.a_dim])
    a_dotdot_record = np.empty([ntrials,last_frm,gv.a_dim])
    predict_formant_record = np.empty([ntrials,last_frm,3])

    #Check if catch trials (no perturbation) are specified in the config file
    if 'CatchTrials' in config.keys():
        catch_trials = string2dtype_array(config['CatchTrials']['catch_trials'], dtype='int')
        catch_types = string2dtype_array(config['CatchTrials']['catch_types'], dtype='int')
        if len(catch_trials) != len(catch_types):
            raise Exception("Catch trial and catch type lengths not matching, please check the config file.")
    else: catch_trials = np.array([])

    #pdb.set_trace()

    #Run FACTS for each trial
    for trial in range(ntrials):
        print("trial:", trial)
        #Gestural score (task)
        GestScore, ART, ms_frm, last_frm = MakeGestScore(gFile,target_noise)         #this is similar with MakeGest in the matlab version

        # initial condition
        x_tilde = string2dtype_array(config['InitialCondition']['x_tilde_init'],'float')
        a_tilde = string2dtype_array(config['InitialCondition']['a_tilde_init'],'float')
        a_actual = string2dtype_array(config['InitialCondition']['a_tilde_init'],'float')
        model.artic_sfc_law.reset_prejb() #save the initial artic-to-task model.

        if trial in catch_trials: catch = catch_types[np.where(catch_trials==trial)[0][0]]
        else: catch = False
        print("catch:", catch)
        
        for i_frm in range(last_frm):
            #model function runs FACTS by each frame
            x_tilde, a_tilde, a_actual, formants, formants_shifted, adotdot, y_hat = model.run_one_timestep(x_tilde, a_tilde, a_actual, GestScore, ART, ms_frm, i_frm, trial, catch)
            
            #save the FACTS results
            a_record[trial, i_frm,:] = a_actual[0:gv.a_dim]
            a_tilde_record[trial, i_frm,:] = a_tilde[0:gv.a_dim]
            a_dot_record[trial, i_frm,:] = a_tilde[gv.a_dim:]
            x_record[trial, i_frm,:] = x_tilde[0:gv.x_dim]
            formant_record[trial, i_frm,:] = formants
            predict_formant_record[trial, i_frm,:] = y_hat
            shift_record[trial, i_frm, :] = formants_shifted
            a_dotdot_record[trial, i_frm,:] = adotdot
            
        return formant_record
        # #Update the task state estimator after each trial (if it's not a catch trial)
        # model.artic_state_estimator.update()
        # model.task_state_estimator.update(catch)
        
        # plot = False
        # if plot:
        #     if trial < model.auditory_perturbation.PerturbOnsetTrial-1:
        #         condition = 'baseline'
        #     elif trial >= model.auditory_perturbation.PerturbOnsetTrial-1 and trial < model.auditory_perturbation.PerturbOffsetTrial: 
        #         condition = 'learning'
        #     elif trial >= model.auditory_perturbation.PerturbOffsetTrial:
        #         condition = 'aftereffect'
        #     single_trial_plots(condition,trial,a_record,a_tilde_record,formant_record,shift_record,x_record,argv)
            # save = True
            # if save:
            #     write_path = f'Simulation/Pert/DesignA_lower/{pp}/'
            #     # Check if folder exists, if not, write it
            #     if not os.path.exists(write_path):
            #         # If not, then create it
            #         os.makedirs(write_path)
            #     datafile_name = ''
            #     np.savetxt(write_path + 'formant_'+ datafile_name + '_' + str(trial) + '.csv',formant_record[trial],delimiter=',')
            #     np.savetxt(write_path + 'predictformant_'+ datafile_name + '_' + str(trial) + '.csv',predict_formant_record[trial],delimiter=',')
            #     np.savetxt(write_path + 'shiftformant_'+ datafile_name + '_' + str(trial) + '.csv',shift_record[trial],delimiter=',')
            #     np.savetxt(write_path + 'articact_'+ datafile_name + '_' + str(trial) + '.csv',a_record[trial],delimiter=',')            
            #     np.savetxt(write_path + 'articest_'+ datafile_name + '_' + str(trial) + '.csv',a_tilde_record[trial],delimiter=',')            
            #     np.savetxt(write_path + 'task_'+ datafile_name + '_' + str(trial) + '.csv',x_record[trial],delimiter=',') 
            #     np.savetxt(write_path + 'adotdot_'+ datafile_name + '_' + str(trial) + '.csv',a_dotdot_record[trial],delimiter=',')


# if __name__ == "__main__":
#     main(sys.argv[1:])
    # Sri class project
    # main(['DesignA_pert.ini','GesturalScores/KimetalOnlinepert2.G',theta]) #datafile_name: ClassicArtUp

   
   