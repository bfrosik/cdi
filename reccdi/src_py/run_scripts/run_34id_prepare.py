import argparse
import pylibconfig2 as cfg
import sys
import os
import reccdi.src_py.beamlines.aps_34id.prep as prep
import reccdi.src_py.utilities.parse_ver as ver
import shutil


def prepare(experiment_dir, scan_range, conf_file):
    prep.prepare(experiment_dir, scan_range, conf_file)

    return experiment_dir


def copy_conf(src, dest):
    try:
        main_conf = os.path.join(src, 'config_prep')
        shutil.copy(main_conf, dest)
        conf_data = os.path.join(src, 'config_data')
        shutil.copy(conf_data, dest)
        conf_rec = os.path.join(src, 'config_rec')
        shutil.copy(conf_rec, dest)
        conf_disp = os.path.join(src, 'config_disp')
        shutil.copy(conf_disp, dest)
    except:
        pass


def parse_and_prepare(prefix, scan, conf_dir):
    id = prefix + '_' + scan
    print ('reading data files for experiment ' + id)

    if not os.path.isdir(conf_dir):
        print ('configured directory ' + conf_dir + ' does not exist')
        return

    main_conf = os.path.join(conf_dir, 'config')
    if not os.path.isfile(main_conf):
        print ('the configuration directory does not contain "config" file')
        return

    try:
        # convert it to list of int
        scan_range = scan.split('-')
        scan_num = []
        for i in range(len(scan_range)):
            scan_num.append(int(scan_range[i]))
    except:
        print ('enter numeric values for scan range')
        return

    if not ver.ver_config_prep(main_conf):
        return

    try:
        with open(main_conf, 'r') as f:
            config_map = cfg.Config(f.read())
    except Exception as e:
        print ('Please check the configuration file ' + main_conf + '. Cannot parse ' + str(e))
        return

    try:
        working_dir = config_map.working_dir.strip()
    except:
        working_dir = os.getcwd()

    experiment_dir = os.path.join(working_dir, id)
    if not os.path.exists(experiment_dir):
        os.makedirs(experiment_dir)
    # copy config_data, config_rec, cofig_disp files from cofig directory into the experiment conf directory
    experiment_conf_dir = os.path.join(experiment_dir, 'conf')
    if not os.path.exists(experiment_conf_dir):
        os.makedirs(experiment_conf_dir)

    experiment_main_config = os.path.join(experiment_conf_dir, 'config')
    conf_map = {}
    conf_map['working_dir'] = '"' + working_dir + '"'
    conf_map['experiment_id'] = '"' + prefix + '"'
    conf_map['scan'] = '"' + scan + '"'
    temp_file = os.path.join(experiment_conf_dir, 'temp')
    with open(temp_file, 'a') as f:
        for key in conf_map:
            value = conf_map[key]
            if len(value) > 0:
                f.write(key + ' = ' + conf_map[key] + '\n')
    f.close()
    if not ver.ver_config(temp_file):
#        os.remove(temp_file)
        print('please check the entered parameters. Cannot save this format')
    else:
        shutil.copy(temp_file, experiment_main_config)
        os.remove(temp_file)

    copy_conf(conf_dir, experiment_conf_dir)
    prep_conf = os.path.join(experiment_conf_dir, 'config_prep')
    if os.path.isfile(prep_conf):
        prep.prepare(experiment_dir, scan_num, prep_conf)
    else:
        print ('missing ' + prep_conf + ' file')

    return experiment_dir


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="prefix to name of the experiment/data reconstruction")
    parser.add_argument("scan", help="a range of scans to prepare data from")
    parser.add_argument("conf_dir", help="directory where the configuration files are located")
    args = parser.parse_args()
    scan = args.scan
    id = args.id
    conf_dir = args.conf_dir

    return parse_and_prepare(id, scan, conf_dir)


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
