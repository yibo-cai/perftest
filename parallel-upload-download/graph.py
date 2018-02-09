import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', help='image title')
    parser.add_argument('-n', '--nograph', action='store_true')
    parser.add_argument('csvfiles', nargs='+')
    return parser.parse_args()


def process_df(csvfile):

    def sz2str(x):
        if x < 1024:
            return '{}B'.format(x)
        x //= 1024
        if x < 1024:
            return '{}KB'.format(x)
        x //= 1024
        return '{}MB'.format(x)

    df = pd.read_csv(csvfile)

    # objsz -> 0,    1,    2,  ...
    # szmap -> 256K, 512K, 1M, ...
    objsz_lst = np.sort(df['objsz'].unique())
    objsz_idx = {sz: idx for idx, sz in enumerate(objsz_lst)}
    df['objsz'] = df['objsz'].apply(lambda x: objsz_idx[x])
    szmap = [sz2str(x) for x in objsz_lst]

    return df, szmap


def process_df_lst(args):
    df_lst, szmap_lst = [], []
    for csvfile in args.csvfiles:
        df, szmap = process_df(csvfile)
        df_lst.append(df)
        szmap_lst.append(szmap)

    # validate
    df, szmap = df_lst[0], szmap_lst[0]
    for i in range(1, len(df_lst)):
        assert(df.shape == df_lst[i].shape)
        assert(szmap == szmap_lst[i])

    return df_lst, szmap


def render_graph(df, ax, szmap):
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


# plot write/read bandwidth of one csvfile
def render_one(args, df, szmap):
    fig, ax = plt.subplots(1, 2, figsize=(16, 6))
    fig.subplots_adjust(wspace=0.2)
    render_graph(df[df['type'] == 'put'], ax[0], szmap)
    render_graph(df[df['type'] == 'get'], ax[1], szmap)
    ax[0].set_title('Write bandwidth')
    ax[1].set_title('Read bandwidth')

    f = os.path.splitext(args.csvfiles[0])[0] + '.png'
    fig.savefig(f, bbox_inches='tight')

    if not args.nograph:
        plt.show()


# plot bandwidth comparison of multiple csvfiles
def render_multi(args, df_lst, szmap):

    def render1(df_lst, titles):
        df_cnt = len(df_lst)
        fig, ax = plt.subplots(1, df_cnt, figsize=(8*df_cnt, 6))
        fig.subplots_adjust(wspace=0.2)

        ymin, ymax = 88888888, 0
        for i in range(df_cnt):
            render_graph(df_lst[i], ax[i], szmap)
            ax[i].set_title(titles[i])
            ymin = min(ymin, ax[i].get_ylim()[0])
            ymax = max(ymax, ax[i].get_ylim()[1])
        # normalize y
        for i in range(df_cnt):
            ax[i].set_ylim([ymin, ymax])

        return fig

    titles = [os.path.splitext(os.path.basename(s))[0].upper()
              for s in args.csvfiles]

    df_lst_put = [df[df['type'] == 'put'] for df in df_lst]
    fig = render1(df_lst_put, titles)
    fig.savefig('write-cmp.png', bbox_inches='tight')

    df_lst_get = [df[df['type'] == 'get'] for df in df_lst]
    fig = render1(df_lst_get, titles)
    fig.savefig('read-cmp.png', bbox_inches='tight')

    if not args.nograph:
        plt.show()


if __name__ == '__main__':
    args = parse_args()

    df_lst, szmap = process_df_lst(args)
    if len(df_lst) == 1:
        render_one(args, df_lst[0], szmap)
    else:
        render_multi(args, df_lst, szmap)
