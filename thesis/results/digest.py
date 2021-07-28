#!/usr/bin/env python3

import pandas as pd
import plotnine as p9
import numpy as np
import json
from sys import exit

from flatten_json import flatten
from pprint import pprint

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

idx = pd.IndexSlice

COLORS = [
    '#599ad3',
    '#f9a65a',
    '#79c36a',
    '#f1595f',
    '#9e66ab',
    '#d77fb3',
    '#cd7058',
    '#727272',
]

def remove_prefix(prefix):
    def inner(x: str):
        if x.startswith(prefix):
            return x[len(prefix):]
        return x
    return inner

def remove_suffix(suffix):
    def inner(x: str):
        if x.endswith(suffix):
            return x[:-len(suffix)]
        return x
    return inner

def pct_std(c):
    return c.std() / c.mean() * 100

def pct_diff(base):
    def pct_diff(c):
        real_base = base[base.index == c.index[0]]
        return (c.mean() - real_base.mean()) / abs(real_base.mean()) * 100
    return pct_diff


def fixup_name(s: str) -> str:
    if s == 'bpfbox':
        return 'BPFBox'
    elif s == 'apparmor':
        return 'AppArmor'
    elif s == 'bpfcontain':
        return 'BPFContain'
    else:
        return s.title()


def create_table(df: pd.DataFrame):
    # for c in RESULT_COLS:
    #     if not df[c, 'pct_diff'].any():
    #         df[c, 'result'] = f"{df[c, 'mean']} ({df[c, 'pct_diff']})"
    #     else:
    #         df[c, 'result'] = f"{df[c, 'mean']}"
    #df = df.sort_index(axis=1)

    #df = fixup_names(df)
    #print(df)
    #print(df.loc[:, ['test', (RESULT_COLS, ('mean', 'pct_std'))]])
    #print(df)
    # tests = df.loc[:, ['test']]
    # tests.columns = [('test', '')]
    # results = df.loc[:, (RESULT_COLS, idx[:], ('mean', 'pct_std'))]
    # df = pd.concat([tests, results], axis=1)
    #print(df.xs(['std', 'mean'], axis=1, level=1))
    pass


def ingest() -> pd.DataFrame:
    """Ingest data from json file"""

    # Load the JSON file
    with open('results.json') as f:
        data = json.load(f)

    # Normalize JSON file into a data frame
    df = pd.json_normalize(data['results'])

    # Rename columns
    df.rename(remove_prefix('results.'), axis=1, inplace=True)
    df.rename(columns={'test':'suite', 'arguments':'test'}, inplace=True)

    # Rename test suites
    df['suite'] = df['suite'].str.replace('pts/osbench-1.0.2', 'OSBench', regex=False)
    df['suite'] = df['suite'].str.replace('pts/build-linux-kernel-1.11.0', 'Kernel Compilation', regex=False)
    df['suite'] = df['suite'].str.replace('pts/apache-1.7.2', 'Apache', regex=False)
    # TODO: handle ipc benchmark here if we include it

    # Rename units
    df['units'] = df['units'].str.replace('us', 'μs')

    # Turn results into lists
    for c in df.filter(regex='all_results'):
        df[c] = df[c].map(lambda s: list(s.split(':')))

    # Grab raw results and explode into values
    df = df[df.columns.drop(list(df.filter(regex='value')))]
    df = df.explode(list(df.filter(regex='all_results')))
    df.rename(remove_suffix('.all_results'), axis='columns', inplace=True)

    # Greedily convert the dataframe to numeric where possible
    df = df.apply(lambda s: pd.to_numeric(s, errors='ignore'))

    # Calulate stats
    df = df.groupby(['suite', 'test', 'units'], as_index=False).agg(['mean', 'std', pct_std, pct_diff(df['base'])])
    # Swap stats names with system names in multiindex
    df = df.swaplevel(axis=1)
    # Flatten the whole dataframe
    df = df.stack().reset_index()

    # Split results by system and case
    df.rename(columns={'level_3': 'system'}, inplace=True)
    df['system'] = df['system'].str.replace('base', 'base-base')
    df[['system', 'case']] = df['system'].str.split('-', expand=True)

    # Fixup system and case names
    df['system'] = df['system'].apply(fixup_name)
    df['case'] = df['case'].apply(fixup_name)

    # Fixup test case names
    df['test'] = df['test'].apply(remove_prefix('Test: '))

    return df

def generate_graphs(df: pd.DataFrame):
    # p9 variables
    dodge_text = p9.position_dodge(width=0.9)
    units = df['units'].iloc[0]

    # Generate
    for test in set(df['test']):
        plot_df = df[df['test'] == test]
        base_val = plot_df[df['case'] == 'Base']['mean'].iloc[0]
        plot_df = plot_df[plot_df['case'] != 'Base']
        plot = (p9.ggplot(plot_df, p9.aes(x='case', y='mean', fill='system'))
                # TODO: Figure out how to change the order
                + p9.geom_col(stat='identity', position='dodge')
                + p9.geom_errorbar(p9.aes(ymin='mean-std', ymax='mean+std'), position=dodge_text, color='black', size=0.4)
                # TODO: Figure out how to shift this over to the left a bit
                + p9.geom_text(p9.aes(y=-.5, label='system'),
                      position=dodge_text,
                      color='gray', size=8, angle=45, va='top')
                + p9.geom_hline(yintercept=base_val, color='#f1595f', linetype='dashed')
                + p9.lims(y=(-5, None))
                + p9.scale_fill_manual(values=COLORS)
                + p9.labs(y=f'Time ({units})', x='Test Case', title=f'{test} Results')
                )
        plot.save(f'graphs/{test.replace(" ", "-")}.pdf')



def main():
    df = ingest()
    generate_graphs(df)

    #kernel = df[df['suite'] == 'Kernel Compilation']
    #digest(kernel, 'kernel-compilation')

    #apache = df[df['suite'] == 'Apache']
    #digest(apache, 'apache')



if __name__ == '__main__':
    main()
