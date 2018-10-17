import sys
import os
import shutil
import prep
from PyQt4.QtCore import *
from PyQt4.QtGui import *


def select_file(start_dir):
    dialog = QFileDialog(None, 'select dir', start_dir)
    dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setSidebarUrls([QUrl.fromLocalFile(start_dir)])
    if dialog.exec_() == QDialog.Accepted:
        return str(dialog.selectedFiles()[0])


def select_dir(start_dir):
    dialog = QFileDialog(None, 'select dir', start_dir)
    dialog.setFileMode(QFileDialog.DirectoryOnly)
    dialog.setSidebarUrls([QUrl.fromLocalFile(start_dir)])
    if dialog.exec_() == QDialog.Accepted:
        return str(dialog.selectedFiles()[0])


class cdi_conf(QWidget):
    def __init__(self, parent=None):
        super(cdi_conf, self).__init__(parent)
        uplayout = QFormLayout()

        self.set_work_dir_button = QPushButton()
        uplayout.addRow("Working Directory", self.set_work_dir_button)
        self.Id_widget = QLineEdit()
        uplayout.addRow("Reconstruction ID", self.Id_widget)

        vbox = QVBoxLayout()
        vbox.addLayout(uplayout)

        self.t = cdi_conf_tab(self)
        vbox.addWidget(self.t)

        self.setLayout(vbox)
        self.setWindowTitle("CDI Configuration")

        self.Id_widget.textChanged.connect(self.set_id)
        self.set_work_dir_button.clicked.connect(self.set_working_dir)


    def set_id(self):
        self.id = str(self.Id_widget.text())


    def set_working_dir(self):
        self.working_dir = select_dir('/local/bfrosik/cdi')
        self.set_work_dir_button.setStyleSheet("Text-align:left")
        self.set_work_dir_button.setText(self.working_dir)


class cdi_conf_tab(QTabWidget):
    def __init__(self, main_win, parent=None):
        super(cdi_conf_tab, self).__init__(parent)
        self.main_win = main_win
        self.tab1 = QWidget()
        self.prep_result_dir = self.id = self.detector = self.scan = self.data_dir = self.specfile = None
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()

        self.addTab(self.tab1, "34ID prep")
        self.addTab(self.tab2, "Data")
        self.addTab(self.tab3, "Reconstruction")
        self.addTab(self.tab4, "Display")
        self.tab1UI()
        self.tab2UI()
        self.tab3UI()
        self.tab4UI()


    def tab1UI(self):
        layout = QFormLayout()
        # self.det_widget = QLineEdit()
        # layout.addRow("Detector", self.det_widget)
        self.data_dir_button = QPushButton()
        layout.addRow("data directory", self.data_dir_button)
        self.spec_file_button = QPushButton()
        layout.addRow("spec file", self.spec_file_button)
        self.scan_widget = QLineEdit()
        layout.addRow("scan(s)", self.scan_widget)
        self.dark_file_button = QPushButton()
        layout.addRow("darkfield file", self.dark_file_button)
        self.white_file_button = QPushButton()
        layout.addRow("whitefield file", self.white_file_button)
        self.prep_button = QPushButton('prepare', self)
        layout.addWidget(self.prep_button)
        self.tab1.setLayout(layout)

        self.prep_button.clicked.connect(self.prepare)
        self.data_dir_button.clicked.connect(self.set_data_dir)
        self.spec_file_button.clicked.connect(self.set_spec_file)
        self.dark_file_button.clicked.connect(self.set_dark_file)
        self.white_file_button.clicked.connect(self.set_white_file)


    def tab2UI(self):
        layout = QFormLayout()
        self.aliens = QLineEdit()
        layout.addRow("aliens", self.aliens)
        self.amp_threshold = QLineEdit()
        layout.addRow("amp_threshold", self.amp_threshold)
        self.binning = QLineEdit()
        layout.addRow("binning", self.binning)
        self.center_shift = QLineEdit()
        layout.addRow("center_shift", self.center_shift)
        self.adjust_dimensions = QLineEdit()
        layout.addRow("adjust_dimensions", self.adjust_dimensions)
        self.config_data_button = QPushButton('create config_data', self)
        layout.addWidget(self.config_data_button)
        self.tab2.setLayout(layout)

        self.config_data_button.clicked.connect(self.config_data)


    def tab3UI(self):
        layout = QVBoxLayout()
        ulayout = QFormLayout()
        llayout = QHBoxLayout()
        self.save_dir = QLineEdit()
        ulayout.addRow("save results dir", self.save_dir)
        self.cont = QCheckBox()
        ulayout.addRow("continuation", self.cont)
        self.cont.setChecked(False)
        self.device = QLineEdit()
        ulayout.addRow("device(s)", self.device)
        self.threads = QLineEdit()
        ulayout.addRow("number of threads", self.threads)
        self.gc = QLineEdit()
        ulayout.addRow("gc triggers", self.gc)
        self.alg_seq = QLineEdit()
        ulayout.addRow("algorithm sequence", self.alg_seq)
        # TODO add logic to show this only if HIO is in sequence
        self.beta = QLineEdit()
        ulayout.addRow("beta", self.beta)
        self.rec_default_button = QPushButton('set to defaults', self)
        ulayout.addWidget(self.rec_default_button)

        layout.addLayout(ulayout)
        layout.addLayout(llayout)
        self.features = Features(self, llayout)
        self.config_rec_button = QPushButton('create config_rec', self)
        layout.addWidget(self.config_rec_button)
        self.tab3.setAutoFillBackground(True)
        self.tab3.setLayout(layout)

        self.config_rec_button.clicked.connect(self.config_rec)
        self.cont.stateChanged.connect(lambda: self.toggle_cont(ulayout))
        self.rec_default_button.clicked.connect(self.rec_default)


    def toggle_cont(self, layout):
        cb_label = layout.labelForField(self.cont)
        if self.cont.isChecked():
            self.cont_dir = QLineEdit()
            layout.insertRow(2, "continue dir", self.cont_dir)
            cb_label.setStyleSheet('color: black')
        else:
            label = layout.labelForField(self.cont_dir)
            self.cont_dir.setParent(None)
            label.setParent(None)
            cb_label.setStyleSheet('color: grey')


    def tab4UI(self):
        layout = QFormLayout()
        self.crop = QLineEdit()
        layout.addRow("crop", self.crop)
        self.save_disp_dir = QLineEdit()
        layout.addRow("save display dir", self.save_disp_dir)
        self.config_disp_button = QPushButton('update config_disp', self)
        layout.addWidget(self.config_disp_button)
        self.tab4.setLayout(layout)

        self.config_disp_button.clicked.connect(self.config_disp)


    def set_spec_file(self):
        self.specfile = select_file('/net/s34data/export/34idc-data/2018')
        self.spec_file_button.setStyleSheet("Text-align:left")
        self.spec_file_button.setText(self.specfile)


    def set_dark_file(self):
        self.darkfile = select_file('/net/s34data/export/34idc-work/2018')
        self.dark_file_button.setStyleSheet("Text-align:left")
        self.dark_file_button.setText(self.darkfile)


    def set_white_file(self):
        self.whitefile = select_file('/net/s34data/export/34idc-work/2018')
        self.white_file_button.setStyleSheet("Text-align:left")
        self.white_file_button.setText(self.whitefile)


    def set_data_dir(self):
        self.data_dir = select_dir('/net/s34data/export/34idc-data/2018')
        self.data_dir_button.setStyleSheet("Text-align:left")
        self.data_dir_button.setText(self.data_dir)


    def prepare(self):
        scan = str(self.scan_widget.text())
        if  self.main_win.working_dir is not None and \
            self.main_win.id is not None and\
            scan is not None and \
            self.data_dir is not None and \
            self.specfile is not None:
            try:
                # after checking that scan is entered convert it to list of int
                scan_range = scan.split('-')
                for i in range(len(scan_range)):
                    scan_range[i] = int(scan_range[i])
            except:
                print ('enter numeric values for scan range')
        else:
            print ('enter all fields')
        prep.prepare(self.main_win.working_dir, self.main_win.id, scan_range, self.data_dir, self.specfile, self.darkfile, self.whitefile)


    def config_data(self):
        conf_map = {}
        data_out_dir = '"' + self.main_win.working_dir + '/' + self.main_win.id + '/data' + '"'
        conf_map['data_dir'] = data_out_dir
        if len(self.aliens.text()) > 0:
            conf_map['aliens'] = str(self.aliens.text())
        else:
            print ("aliens not defined")
        if len(self.amp_threshold.text()) > 0:
            conf_map['amp_threshold'] = str(self.amp_threshold.text())
        else:
            print ('amplitude threshold not defined. Quiting operation.')
            return
        if len(self.binning.text()) > 0:
            conf_map['binning'] = str(self.binning.text())
        else:
            print ("binning not defined")
        if len(self.center_shift.text()) > 0:
            conf_map['center_shift'] = str(self.center_shift.text())
        else:
            print ("center shift not defined")
        if len(self.adjust_dimensions.text()) > 0:
            conf_map['adjust_dimensions'] = str(self.adjust_dimensions.text())
        else:
            print ("adjust dimensions not defined")

        self.create_config('config_data', conf_map)


    def config_rec(self):
        conf_map = {}
        conf_map['data_dir'] = '"' + self.main_win.working_dir + '/' + self.main_win.id + '/data' + '"'
        conf_map['save_dir'] = str(self.save_dir.text())
        conf_map['threads'] = str(self.threads.text())
        conf_map['device'] = str(self.device.text())
        conf_map['garbage_trigger'] = str(self.gc.text())
        conf_map['algorithm_sequence'] = str(self.alg_seq.text())
        conf_map['beta'] = str(self.beta.text())
        if self.cont.isChecked():
            conf_map['continue_dir'] = str(self.cont_dir.text())

        for feat_id in self.features.feature_dir:
            self.features.feature_dir[feat_id].add_config(conf_map)

        self.create_config('config_rec', conf_map)


    def create_config(self, conf_file, conf_map):
        valid = True
        working_dir = os.path.join(self.main_win.working_dir, self.main_win.id)
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)
        conf_dir = os.path.join(working_dir, 'conf')
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        conf_file = os.path.join(conf_dir, conf_file)
        temp_file = os.path.join(self.main_win.working_dir, self.main_win.id, 'conf', 'temp')
        with open(temp_file, 'a') as f:
            for key in conf_map:
                value = conf_map[key]
                if len(value) == 0:
                    print ('the ' + key + ' is not configured')
                    valid = False
                    break
                f.write(key + ' = ' + conf_map[key] + '\n')
        f.close()
        if valid:
            shutil.move(temp_file, conf_file)


    def config_disp(self):
        if len(self.crop.text()) == 0:
            print ('crop not configured')
            #return

        working_dir = os.path.join(self.main_win.working_dir, self.main_win.id)
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)
        conf_dir = os.path.join(working_dir, 'conf')

        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        disp_conf_file = os.path.join(self.main_win.working_dir, self.main_win.id, 'conf', 'config_disp')
        temp_file = os.path.join(self.main_win.working_dir, self.main_win.id, 'conf', 'temp')
        with open(temp_file, 'a') as temp:
            try:
                with open(disp_conf_file, 'r') as f:
                    for line in f:
                        if not line.startswith('crop')and not line.startswith('save_dir'):
                            temp.write(line)
                f.close()
            except:
                pass

            if len(self.crop.text()) != 0:
                temp.write('crop = ' + str(self.crop.text()) + '\n')
            if len(self.save_disp_dir.text()) == 0:
                temp.write('save_dir = ' + working_dir + '/results\n')
            else:
                temp.write('save_dir = ' + str(self.save_disp_dir.text()) + '\n')
        temp.close()
        shutil.move(temp_file, disp_conf_file)


    def rec_default(self):
        if  self.main_win.working_dir is None or self.main_win.id is None or \
            len(self.main_win.working_dir) == 0 or len(self.main_win.id) == 0:
                print ('Working Directory or Reconstruction ID not configured')
        else:
            self.save_dir.setText('"' + str(self.main_win.working_dir) + '/' + str(self.main_win.id) + '/results' + '"')
            self.threads.setText('1')
            self.device.setText('(3)')
            self.gc.setText('(1000)')
            self.alg_seq.setText('((5,("ER",20),("HIO",180)),(1,("ER",40),("HIO",160)),(4,("ER",20),("HIO",180)))')
            self.beta.setText('.9')
            self.cont.setChecked(False)


class Feature(object):
    def __init__(self):
        self.stack = QWidget()


    def stackUI(self, item, feats):
        layout = QFormLayout()
        self.active = QCheckBox("active")
        self.active.setChecked(True)
        layout.addWidget(self.active)
        self.toggle(layout, item, feats)
        self.stack.setLayout(layout)
        self.active.stateChanged.connect(lambda: self.toggle(layout, item, feats))


    def toggle(self, layout, item, feats):
        if self.active.isChecked():
            self.fill_active(layout)

            self.default_button = QPushButton('set to defaults', feats)
            layout.addWidget(self.default_button)
            self.default_button.clicked.connect(self.rec_default)

            item.setForeground(QColor('black'));
        else:
            for i in reversed(range(1, layout.count())):
                layout.itemAt(i).widget().setParent(None)
            item.setForeground(QColor('grey'));

    def fill_active(self, layout):
        pass


    def rec_default(self):
        pass


    def add_config(self, conf_map):
        if self.active.isChecked():
            self.add_feat_conf(conf_map)

    def add_feat_conf(self, conf_map):
        pass


class GA(Feature):
    def __init__(self):
        super(GA, self).__init__()
        self.id = 'GA'

    # override setting the active to set it False
    def stackUI(self, item, feats):
        super(GA, self).stackUI(item, feats)
        self.active.setChecked(False)


    def fill_active(self, layout):
        self.generations = QLineEdit()
        layout.addRow("generations", self.generations)
        self.lr_generations = QLineEdit()
        layout.addRow("low resolution generations", self.lr_generations)
        self.lr_sigma_alg = QLineEdit()
        layout.addRow("low resolution sigma algorithm", self.lr_sigma_alg)
        self.lr_sigmas = QLineEdit()
        layout.addRow("low resolution sigmas", self.lr_sigmas)
        self.lr_sigma_min = QLineEdit()
        layout.addRow("low resolution sigma min", self.lr_sigma_min)
        self.lr_sigma_max = QLineEdit()
        layout.addRow("low resolution sigma max", self.lr_sigma_max)
        self.lr_scale_power = QLineEdit()
        layout.addRow("low resolution scale power", self.lr_scale_power)
        self.lr_algorithm = QLineEdit()
        layout.addRow("low resolution algorithm", self.lr_algorithm)


    def add_feat_conf(self, conf_map):
        conf_map['generations'] = str(self.generations.text())
        conf_map['low_resolution_generations'] = str(self.lr_generations.text())
        conf_map['low_resolution_sigma_alg'] = str(self.lr_sigma_alg.text())
        conf_map['low_resolution_sigmas'] = str(self.lr_sigmas.text())
        conf_map['low_resolution_sigma_min'] = str(self.lr_sigma_min.text())
        conf_map['low_resolution_sigma_max'] = str(self.lr_sigma_max.text())
        conf_map['low_resolution_scale_power'] = str(self.lr_scale_power.text())
        conf_map['low_resolution_alg'] = str(self.lr_algorithm.text())


class low_resolution(Feature):
    def __init__(self):
        super(low_resolution, self).__init__()
        self.id = 'low resolution'


    def fill_active(self, layout):
        self.res_triggers = QLineEdit()
        layout.addRow("low resolution triggers", self.res_triggers)
        self.sigma_range = QLineEdit()
        layout.addRow("sigma range", self.sigma_range)
        self.det_range = QLineEdit()
        layout.addRow("det range", self.det_range)


    def rec_default(self):
        #TODO add to accept fractions in trigger, so the default will be (.5,1)
        self.res_triggers.setText('(0, 1, 500)')
        self.sigma_range.setText('(2.0)')
        self.det_range.setText('(.7)')


    def add_feat_conf(self, conf_map):
        conf_map['resolution_trigger'] = str(self.res_triggers.text())
        conf_map['iter_res_sigma_range'] = str(self.sigma_range.text())
        conf_map['iter_res_det_range'] = str(self.det_range.text())


class amplitude_support(Feature):
    def __init__(self):
        super(amplitude_support, self).__init__()
        self.id = 'amplitude support'


    def fill_active(self, layout):
        self.support_triggers = QLineEdit()
        layout.addRow("support triggers", self.support_triggers)
        self.support_type = QLineEdit()
        layout.addRow("support algorithm", self.support_type)
        self.support_area = QLineEdit()
        layout.addRow("starting support area", self.support_area)
        self.threshold = QLineEdit()
        layout.addRow("threshold", self.threshold)
        self.sigma = QLineEdit()
        layout.addRow("sigma", self.sigma)


    def rec_default(self):
        self.support_triggers.setText('(1,1)')
        self.support_type.setText('"GAUSS"')
        self.support_area.setText('[.5,.5,.5]')
        self.sigma.setText('1.0')
        self.threshold.setText('0.1')


    def add_feat_conf(self, conf_map):
        conf_map['amp_support_trigger'] = str(self.support_triggers.text())
        conf_map['support_type'] = str(self.support_type.text())
        conf_map['support_threshold'] = str(self.threshold.text())
        conf_map['support_sigma'] = str(self.sigma.text())
        conf_map['support_area'] = str(self.support_area.text())


class phase_support(Feature):
    def __init__(self):
        super(phase_support, self).__init__()
        self.id = 'phase support'


    def fill_active(self, layout):
        self.phase_triggers = QLineEdit()
        layout.addRow("phase support triggers", self.phase_triggers)
        self.phase_min = QLineEdit()
        layout.addRow("phase minimum", self.phase_min)
        self.phase_max = QLineEdit()
        layout.addRow("phase maximum", self.phase_max)


    def rec_default(self):
        self.phase_triggers.setText('(0,1,20)')
        self.phase_min.setText('-1.57')
        self.phase_max.setText('1.57')


    def add_feat_conf(self, conf_map):
        conf_map['phase_support_trigger'] = str(self.phase_triggers.text())
        conf_map['phase_min'] = str(self.phase_min.text())
        conf_map['phase_max'] = str(self.phase_max.text())


class pcdi(Feature):
    def __init__(self):
        super(pcdi, self).__init__()
        self.id = 'pcdi'


    def fill_active(self, layout):
        self.pcdi_triggers = QLineEdit()
        layout.addRow("pcdi triggers", self.pcdi_triggers)
        self.pcdi_type = QLineEdit()
        layout.addRow("partial coherence algorithm", self.pcdi_type)
        self.pcdi_iter = QLineEdit()
        layout.addRow("pcdi iteration number", self.pcdi_iter)
        self.pcdi_normalize = QLineEdit()
        layout.addRow("normalize", self.pcdi_normalize)
        self.pcdi_roi = QLineEdit()
        layout.addRow("pcdi kernel area", self.pcdi_roi)


    def rec_default(self):
        self.pcdi_triggers.setText('(50,50)')
        self.pcdi_type.setText('"LUCY"')
        self.pcdi_iter.setText('20')
        self.pcdi_normalize.setText('true')
        self.pcdi_roi.setText('[32,32,16]')


    def add_feat_conf(self, conf_map):
        conf_map['pcdi_trigger'] = str(self.pcdi_triggers.text())
        conf_map['partial_coherence_type'] = str(self.pcdi_type.text())
        conf_map['partial_coherence_iteration_num'] = str(self.pcdi_iter.text())
        conf_map['partial_coherence_normalize'] = str(self.pcdi_normalize.text())
        conf_map['partial_coherence_roi'] = str(self.pcdi_roi.text())


class twin(Feature):
    def __init__(self):
        super(twin, self).__init__()
        self.id = 'twin'


    def fill_active(self, layout):
        self.twin_triggers = QLineEdit()
        layout.addRow("twin triggers", self.twin_triggers)


    def rec_default(self):
        self.twin_triggers.setText('(2)')


    def add_feat_conf(self, conf_map):
        conf_map['twin_trigger'] = str(self.twin_triggers.text())


class average(Feature):
    def __init__(self):
        super(average, self).__init__()
        self.id = 'average'


    def fill_active(self, layout):
        self.average_triggers = QLineEdit()
        layout.addRow("average triggers", self.average_triggers)


    def rec_default(self):
        self.average_triggers.setText('(-400,1)')


    def add_feat_conf(self, conf_map):
        conf_map['avarage_trigger'] = str(self.average_triggers.text())


class Features(QWidget):
    def __init__(self, tab, layout):
        super(Features, self).__init__()
        feature_ids = ['GA', 'low resolution', 'amplitude support', 'phase support', 'pcdi', 'twin', 'average']
        self.leftlist = QListWidget()
        self.feature_dir = {'GA' : GA(),
                            'low resolution' : low_resolution(),
                            'amplitude support' : amplitude_support(),
                            'phase support' : phase_support(),
                            'pcdi' : pcdi(),
                            'twin' : twin(),
                            'average' : average()}
        self.Stack = QStackedWidget(self)
        for i in range(len(feature_ids)):
            id = feature_ids[i]
            self.leftlist.insertItem(i, id)
            feature = self.feature_dir[id]
            feature.stackUI(self.leftlist.item(i), self)
            self.Stack.addWidget(feature.stack)

        layout.addWidget(self.leftlist)
        layout.addWidget(self.Stack)

        self.leftlist.currentRowChanged.connect(self.display)


    def display(self, i):
        self.Stack.setCurrentIndex(i)


def main():
    app = QApplication(sys.argv)
    ex = cdi_conf()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()