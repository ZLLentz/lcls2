#--------------------
"""
:py:class:`CGWMainConfiguration` - widget for configuration
============================================================================================

Usage::

    # Import
    from psdaq.control_gui.CGWMainConfiguration import CGWMainConfiguration

    # Methods - see test

See:
    - :py:class:`CGWMainConfiguration`
    - `lcls2 on github <https://github.com/slac-lcls/lcls2/psdaq/psdaq/control_gui>`_.

This software was developed for the LCLS2 project.
If you use all or part of it, please give an appropriate acknowledgment.

Created on 2019-01-25 by Mikhail Dubrovin
"""
#--------------------

import logging
logger = logging.getLogger(__name__)

from PyQt5.QtWidgets import QGroupBox, QLabel, QCheckBox, QPushButton, QComboBox, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QPoint

from psdaq.control_gui.CGWConfigEditor import CGWConfigEditor
from psdaq.control_gui.QWPopupSelectItem import popup_select_item_from_list
from psdaq.control_gui.CGConfigDBUtils import get_configdb
from psdaq.control_gui.CGJsonUtils import str_json

from psdaq.control_gui.QWUtils import confirm_or_cancel_dialog_box

#--------------------
char_expand  = u' \u25BC' # down-head triangle

class CGWMainConfiguration(QGroupBox) :
    """
    """
    LIST_OF_SEQUENCES = ('1', '2', '3', '4', '5', '6', '7', '8')

    def __init__(self, parent=None, parent_ctrl=None):

        QGroupBox.__init__(self, 'Configuration', parent)

        self.parent_ctrl = parent_ctrl

        self.lab_type = QLabel('Type')
        self.lab_dev  = QLabel('Detector')

        #self.but_type = QPushButton('BEAM %s' % char_expand)
        #self.but_dev  = QPushButton('testdev0 %s' % char_expand)
        self.but_type = QPushButton('Select %s' % char_expand)
        self.but_dev  = QPushButton('Select %s' % char_expand)
        self.but_edit = QPushButton('Edit')
        self.but_scan = QPushButton('Scan')

        self.cbx_seq = QCheckBox('Sync Sequence')
        self.box_seq = QComboBox(self)
        self.box_seq.addItems(self.LIST_OF_SEQUENCES)
        self.box_seq.setCurrentIndex(0)

        self.hbox1 = QHBoxLayout() 
        self.hbox1.addStretch(1)
        self.hbox1.addWidget(self.lab_type)
        self.hbox1.addWidget(self.but_type) 
        self.hbox1.addStretch(1)
        self.hbox1.addWidget(self.lab_dev)
        self.hbox1.addWidget(self.but_dev)

        self.hbox2 = QHBoxLayout() 
        self.hbox2.addStretch(1)
        self.hbox2.addWidget(self.cbx_seq)
        self.hbox2.addWidget(self.box_seq) 
        self.hbox2.addStretch(1)

        self.vbox = QVBoxLayout() 
        self.vbox.addLayout(self.hbox1)
        self.vbox.addWidget(self.but_edit, 0, Qt.AlignCenter)
        self.vbox.addWidget(self.but_scan, 0, Qt.AlignCenter)
        self.vbox.addLayout(self.hbox2)

        #self.grid = QGridLayout()
        #self.grid.addWidget(self.lab_type,       0, 0, 1, 1)
        #self.grid.addWidget(self.but_type,       0, 2, 1, 1)
        #self.grid.addWidget(self.but_edit,       1, 1, 1, 1)
        #self.grid.addWidget(self.but_scan,       2, 1, 1, 1)

        self.setLayout(self.vbox)

        self.set_tool_tips()
        self.set_style()

        self.but_edit.clicked.connect(self.on_but_edit)
        self.but_scan.clicked.connect(self.on_but_scan)
        self.but_type.clicked.connect(self.on_but_type)
        self.but_dev .clicked.connect(self.on_but_dev)
        self.box_seq.currentIndexChanged[int].connect(self.on_box_seq)
        self.cbx_seq.stateChanged[int].connect(self.on_cbx_seq)

        self.w_edit = None
        self.type_old = None

#--------------------

    def set_tool_tips(self) :
        #self.setToolTip('Configuration') 
        self.but_edit.setToolTip('Edit configuration dictionary.')
        self.but_type.setToolTip('Select configuration type.') 
        self.but_dev .setToolTip('Select device for configuration.') 

#--------------------

    def set_buts_enabled(self) :
        is_selected_type = self.but_type.text()[:6] != 'Select'
        is_selected_det  = self.but_dev .text()[:6] != 'Select'
        self.but_dev .setEnabled(is_selected_type)
        self.but_edit.setEnabled(is_selected_type and is_selected_det)

#--------------------

    def set_style(self) :
        from psdaq.control_gui.Styles import style
        self.setStyleSheet(style.qgrbox_title)
        self.but_edit.setFixedWidth(60)
        self.but_scan.setFixedWidth(60)
        self.set_buts_enabled()

        #self.setMinimumWidth(350)
        #self.setWindowTitle('File name selection widget')
        #self.setFixedHeight(34) # 50 if self.show_frame else 34)
        #self.layout().setContentsMargins(0,0,0,0)
        #self.setMinimumSize(725,360)
        #self.setFixedSize(750,270)
        #self.setMaximumWidth(800)
 
#--------------------
 
    def inst_configdb(self, msg=''):
        parent = self.parent_ctrl
        uris = getattr(parent, 'uris', 'mcbrowne:psana@psdb-dev:9306')
        inst = getattr(parent, 'inst', 'TMO')
        logger.debug('%sconnect to configdb(uri_suffix=%s, inst=%s)' % (msg, uris, inst))
        return inst, get_configdb(uri_suffix=uris, inst=inst)

#--------------------

    def save_dictj_in_db(self, dictj, msg='') :
        logger.debug('%ssave_dictj_in_db' % msg)
        cfgtype, devname = self.cfgtype_and_device()
        inst, confdb = self.inst_configdb('CGWConfigEditor.on_but_apply: ')

        resp = confirm_or_cancel_dialog_box(parent=None,
                                            text='Save changes in configuration DB',\
                                            title='Confirm or cancel') 
        if resp : 
            new_key = confdb.modify_device(cfgtype, devname, dictj, hutch=inst)
            logger.debug('save_dictj_in_db new_key: %d' % new_key)
            
        else :
            logger.warning('Saving of configuration in DB is cancelled...')

#--------------------
 
    def on_but_type(self):
        #logger.debug('on_but_type')
        inst, confdb = self.inst_configdb('on_but_type: ')
        list_of_aliases = confdb.get_aliases(hutch=inst) # ['NOBEAM', 'BEAM']
        selected = popup_select_item_from_list(self.but_type, list_of_aliases, min_height=80, dx=-10, dy=0)
        self.set_but_type_text(selected)
        msg = 'selected %s of the list %s' % (selected, str(list_of_aliases))
        logger.debug(msg)

        if selected != self.type_old :
            self.set_but_dev_text()
            self.type_old = selected

        self.set_buts_enabled()

#--------------------
 
    def set_but_type_text(self, txt='Select'): self.but_type.setText('%s %s' % (txt, char_expand))
    def set_but_dev_text (self, txt='Select'): self.but_dev .setText('%s %s' % (txt, char_expand))

    def but_type_text(self): return str(self.but_type.text()).split(' ')[0] # 'NOBEAM' or 'BEAM'
    def but_dev_text (self): return str(self.but_dev .text()).split(' ')[0] # 'testdev0'

#--------------------

    def cfgtype_and_device(self):
        return self.but_type_text(), self.but_dev_text()

#--------------------
 
    def on_but_dev(self):
        #logger.debug('on_but_dev')
        inst, confdb = self.inst_configdb('on_but_dev: ')
        cfgtype = str(self.but_type.text()).split(' ')[0] # 'NOBEAM' or 'BEAM'
        list_of_device_names = confdb.get_devices(cfgtype, hutch=inst)
        selected = popup_select_item_from_list(self.but_dev, list_of_device_names, min_height=80, dx=-20, dy=10)
        self.set_but_dev_text(selected)
        msg = 'selected %s of the list %s' % (selected, str(list_of_device_names))
        logger.debug(msg)

        self.set_buts_enabled()

#--------------------
 
    def on_box_seq(self, ind):
        selected = str(self.box_seq.currentText())
        msg = 'selected ind:%d %s' % (ind,selected)
        logger.debug(msg)

#--------------------
 
    def on_cbx_seq(self, ind):
        #if self.cbx.hasFocus() :
        cbx = self.cbx_seq
        tit = cbx.text()
        #self.cbx_runc.setStyleSheet(style.styleGreenish if cbx.isChecked() else style.styleYellowBkg)
        msg = 'Check box "%s" is set to %s' % (tit, cbx.isChecked())
        logger.info(msg)

#--------------------
 
    def on_but_edit(self):
        #logger.debug('on_but_edit')
        if self.w_edit is None :
            inst, confdb = self.inst_configdb('on_but_edit: ')
            cfgtype = self.but_type_text()
            dev     = self.but_dev_text()
            self.config = confdb.get_configuration(cfgtype, dev, hutch=inst)
            msg = 'get_configuration(%s, %s, %s):\n' % (cfgtype, dev, inst)\
                + '%s\n    type(config): %s'%(str_json(self.config), type(self.config))
            logger.debug(msg)

            self.w_edit = CGWConfigEditor(dictj=self.config, parent_ctrl=self)
            self.w_edit.move(self.pos() + QPoint(self.width()+30, 0))
            self.w_edit.show()

        else :
            self.w_edit.close()
            self.w_edit = None

#--------------------
 
    def on_but_scan(self):
        logger.debug('on_but_scan')

#--------------------

    def closeEvent(self, e):
        print('CGWMainConfiguration.closeEvent')
        if self.w_edit is not None :
           self.w_edit.close()
        QGroupBox.closeEvent(self, e)

#--------------------
 
if __name__ == "__main__" :

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = CGWMainConfiguration(parent=None)
    w.show()
    app.exec_()

#--------------------
