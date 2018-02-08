import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', help='image title')
    parser.add_argument('-n', '--nograph', action='store_true')
    parser.add_argument('csvfile')
    return parser.parse_args()


def process_df(args):

    def sz2str(x):
        if x < 1024:
            return '{}B'.format(x)
        x //= 1024
        if x < 1024:
            return '{}KB'.format(x)
        x //= 1024
        return '{}MB'.format(x)

    df = pd.read_csv(args.csvfile)

    # objsz -> 0,    1,    2,  ...
    # szmap -> 256K, 512K, 1M, ...
    objsz_lst = np.sort(df['objsz'].unique())
    objsz_idx = {sz: idx for idx, sz in enumerate(objsz_lst)}
    df['objsz'] = df['objsz'].apply(lambda x: objsz_idx[x])
    szmap = [sz2str(x) for x in objsz_lst]

    return df, szmap


def render_graphs(args, df, szmap):

    def render_graph(df, ax):
        colors = [ 'r', 'b', 'y', 'g', 'm', 'c', 'k' ]

        workers_lst = np.sort(df['workers'].unique())
        assert(len(colors) >= len(workers_lst))

        gap = 0.25
        bar_width = (1 - gap) / len(workers_lst)
        xshift = (1 - gap) / 2
        for x in range(len(szmap)):
            xpos = 1 + x - xshift
            for dx, workers in enumerate(workers_lst):
                bw = df[(df['objsz']==x) & (df['workers']==workers)]['bandwidth']
                label = workers if x == 0 else ''
                ax.bar(xpos, bw, width=bar_width, color=colors[dx],
                       align='center', label=label)
                xpos += bar_width
        ax.set_xticks(range(1, len(szmap)+1))
        ax.set_xticklabels(szmap)
        ax.set_xlabel('Object size')
        ax.set_ylabel('Bandwidth(MB/s)')
        ax.legend(title='Workers')

    fig, ax = plt.subplots(1, 2, figsize=(16, 6))
    fig.subplots_adjust(wspace=0.2)
    render_graph(df[df['type'] == 'put'], ax[0])
    render_graph(df[df['type'] == 'get'], ax[1])
    ax[0].set_title('Write bandwidth')
    ax[1].set_title('Read bandwidth')

    f = os.path.splitext(args.csvfile)[0] + '.png'
    fig.savefig(f, bbox_inches='tight')

    if not args.nograph:
        plt.show()


if __name__ == '__main__':
    args = parse_args()

    df, szmap = process_df(args)
    render_graphs(args, df, szmap)
