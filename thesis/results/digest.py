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

    # Fixup test case names
    df['test'] = df['test'].apply(remove_prefix('Test: '))
    df['test'] = df['test'].replace('Time To Compile', 'Kernel Compilation')
    df['test'] = df['test'].replace('Static Web Page Serving', 'Apache')

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

    # Apply ordered categoricals
    df['case'] = pd.Categorical(df['case'], categories=['Base', 'Passive', 'Allow', 'Complaining'], ordered=True)
    df['system'] = pd.Categorical(df['system'], categories=['BPFBox', 'BPFContain', 'AppArmor', 'Base'], ordered=True)

    return df

def generate_tables(df: pd.DataFrame):
    for test in set(df['test']):
        # Get only the values in the current test
        tab_df = df[df['test'] == test]
        units = tab_df['units'].iloc[0].replace('μs', '$\mu$s')
        # Fixup column names
        tab_df = tab_df.rename(columns={'case': 'Test Case', 'system': 'System', 'mean': 'Mean', 'std': 'Std', 'pct_diff': 'Overhead'})
        # Select and order columns
        tab_df = tab_df [['Test Case', 'System', 'Mean', 'Std', 'Overhead']]
        # HIB
        if test == 'Apache':
            hib = 'Higher is better'
            tab_df['Overhead'] = -tab_df['Overhead']
        else:
            hib = 'Lower is better'
        # Sort
        tab_df = tab_df.sort_values(['Test Case', 'System'])
        # Fixup base system
        tab_df['System'] = tab_df['System'].replace('Base', '---', regex=False)
        # Fixup overhead
        tab_df['Overhead'] = tab_df['Overhead'].map(lambda x: f'{x:.2f}\\%')
        tab_df.loc[tab_df['Test Case'] == 'Base', 'Overhead'] = '---'
        # Convert test case and system to index
        tab_df.set_index(['Test Case', 'System'], inplace=True)
        # Make table
        tab_df = tab_df.round(2)
        caption = (f'Results of the {test.lower()} benchmark. Units are {units}. {hib}. Percent overhead is compared to the baseline result.', f'Results of the {test.lower()} benchmark')
        test_name = test.lower().replace(" ", "-")
        label = f'tab:phoronix-{test_name}'
        tab_df.to_latex(f'tables/{test_name}.tex', multirow=True, caption=caption, label=label, column_format='llrrr', position='htp!', escape=False)


def generate_graphs(df: pd.DataFrame):
    # p9 variables
    dodge_text = p9.position_dodge(width=0.9)
    ccolor = '#555555'
    lcolor = '#a4031f'

    # Generate
    for test in set(df['test']):
        # Get only the values in the current test
        plot_df = df[df['test'] == test]
        # Get the units for the test
        units = plot_df['units'].iloc[0]
        # Find the value of the base to make the line later
        base_val = plot_df[plot_df['case'] == 'Base']['mean'].iloc[0]
        # Strip out base since it's a line
        plot_df = plot_df[plot_df['case'] != 'Base']
        # Set y lim by test case
        if test == 'Kernel Compilation':
            ylim = -45
        elif test == 'Create Threads':
            ylim = -3
        elif test == 'Create Processes':
            ylim = -6
        elif test == 'Launch Programs':
            ylim = -15
        elif test == 'Create Files':
            ylim = -15
        elif test == 'Memory Allocations':
            ylim = -20
        elif test == 'Apache':
            ylim = -3000
        else:
            ylim = None

        # Make the plot
        plot = (p9.ggplot(plot_df, p9.aes(x='case', y='mean', fill='system'))
                # TODO: Figure out how to change the order
                + p9.geom_col(stat='identity', position='dodge', show_legend=False)
                + p9.geom_errorbar(p9.aes(ymin='mean-std', ymax='mean+std'), position=dodge_text, color=ccolor, size=0.2)
                # TODO: Figure out how to shift this over to the left a bit
                + p9.geom_text(p9.aes(y=-.5, label='system'),
                    position=dodge_text,
                    color=ccolor, size=8, angle=45, va='top')
                + p9.geom_hline(yintercept=base_val, color=lcolor, linetype='dashed', size=0.4)
                + p9.lims(y=(ylim, None))
                + p9.scale_fill_manual(values=COLORS)
                + p9.labs(y=f'{units}', x='Test Case', title=f'{test} Results')
                + p9.theme(axis_line_x=p9.element_line(color=ccolor),
                    axis_text_x=p9.element_text(color=ccolor),
                    axis_text_y=p9.element_text(color=ccolor))
                )
        # Save the plot
        plot.save(f'graphs/{test.replace(" ", "-")}.pdf')



def main():
    df = ingest()
    #generate_graphs(df)
    generate_tables(df)

    #kernel = df[df['suite'] == 'Kernel Compilation']
    #digest(kernel, 'kernel-compilation')

    #apache = df[df['suite'] == 'Apache']
    #digest(apache, 'apache')



if __name__ == '__main__':
    main()
