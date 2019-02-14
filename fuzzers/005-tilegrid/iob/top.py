import os
import random
random.seed(int(os.getenv("SEED"), 16))
from prjxray import util
from prjxray import verilog
from prjxray.db import Database


def gen_sites():
    '''
    IOB33S: main IOB of a diff pair
    IOB33M: secondary IOB of a diff pair
    IOB33: not a diff pair. Relatively rare (at least in ROI...2 of them?)
    Focus on IOB33S to start
    '''
    db = Database(util.get_db_root())
    grid = db.grid()
    for tile_name in sorted(grid.tiles()):
        loc = grid.loc_of_tilename(tile_name)
        gridinfo = grid.gridinfo_at_loc(loc)

        for site_name, site_type in gridinfo.sites.items():
            if site_type == 'IOB33S':
                yield tile_name, site_name


def write_params(params):
    pinstr = ''
    for tile, (site, val, pin) in sorted(params.items()):
        pinstr += '%s,%s,%s,%s\n' % (tile, val, site, pin)
    open('params.csv', 'w').write(pinstr)


def run():
    sites = list(gen_sites())
    print(
        '''
`define N_DI {}

module top(input wire [`N_DI-1:0] di);
    wire [`N_DI-1:0] di_buf;
    '''.format(len(sites)))

    params = {}
    print('''
        (* KEEP, DONT_TOUCH *)
        LUT6 dummy_lut();''')

    for idx, ((tile_name, site_name), isone) in enumerate(zip(
            sites, util.gen_fuzz_states(len(sites)))):
        params[tile_name] = (site_name, isone, "di[%u]" % idx)
        print(
            '''
    (* KEEP, DONT_TOUCH *)
    IBUF #(
    ) ibuf_{site_name} (
        .I(di[{idx}]),
        .O(di_buf[{idx}])
        );'''.format(site_name=site_name, idx=idx))

        if isone:
            print(
                '''
    (* KEEP, DONT_TOUCH *)
    PULLUP #(
    ) pullup_{site_name} (
        .O(di[{idx}])
        );'''.format(site_name=site_name, idx=idx))

    print("endmodule")
    write_params(params)


if __name__ == '__main__':
    run()
