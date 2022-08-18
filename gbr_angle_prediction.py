#!/usr/bin/python3
# # *************************************************************************
import os
import argparse
import shutil
import utils
import encode_res_calc_angles as erca
import nonred
import graphing
import gbr_latex as ltp
from sklearn_methods import *


# *************************************************************************
def preprocessing(ds):
    encoded_df, ang_df = erca.extract_and_export_packing_residues(
        ds, ds, 'expanded_residues.dat')
    nonred_df = nonred.NR2(encoded_df, ds, f'{ds}_NR2_expanded_residues')
    return nonred_df, ang_df


# *************************************************************************
def runGBReg(train_df, test_df, model_name):
    X_train, y_train, _x_ = make_sets_from_df(train_df)
    X_test, y_true, df_test = make_sets_from_df(test_df)
    df = run_GradientBoostingRegressor(
        X_train, y_train, X_test, df_test, model_name)
    df.to_csv(f'results_for_{model_name}', index=False)
    return df


# *************************************************************************
def postprocessing(df, dataset, ang_df):
    name = 'train_PreAF2_test_PostAF2'
    graphing.actual_vs_predicted_from_df(df, dataset, name, f'{name}_pa')
    graphing.sq_error_vs_actual_angle(
        dataset, df, f'{name}_sqerror_vs_actual')
    graphing.angle_distribution(
        dataset, ang_df, f'{name}_angledistribution')
    graphing.error_distribution(
        dataset, df, f'{name}_errordistribution')


# *************************************************************************
# parser = argparse.ArgumentParser(description='Program for compiling angles')
# parser.add_argument('--preprocess', action='store_true', default=False)
# parser.add_argument('--process', action='store_true', default=False)
# parser.add_argument('--postprocess', action='store_true', default=False)
# parser.add_argument('--latex', action='store_true', default=False)

# args = parser.parse_args()

# if not args.preprocess and not args.process and not args.postprocess and not args.latex:
#     print('Neither --preprocess nor --process nor --postprocess nor --latex has been specified. Enabling all of them.')
#     args.process = args.postprocess = args.latex = True


# if args.preprocess:
#     df_train = preprocessing('Everything')
#     df_test = preprocessing('new_files')

# if args.process:
#     print('Processing...')
#     result_df = runGBReg(df_train, df_test, 'train_Everything_test_abdbnew')

# if args.postprocess:
#     print('Postprocessing...')
#     postprocessing(result_df, 'new_files')

# if args.latex:
#     print('Generating LaTeX...')
#     # ltp.generate_latex('PostAF2', 'Everything', 'GBReg_PostAF2')

df_train, train_angles = preprocessing('PreAF2')
df_test, test_angles= preprocessing('PostAF2')
print('Processing...')
result_df = runGBReg(df_train, df_test, 'train_PreAF2_H100G_residues_considered')
print(result_df)
print('Postprocessing...')
postprocessing(result_df, 'PostAF2', test_angles)
print('Goodbye!')
