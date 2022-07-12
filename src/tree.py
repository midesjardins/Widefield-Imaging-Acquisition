import os
import random
import numpy as np
from src.waveforms import make_signal
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtGui import QBrush, QColor, QIcon
from src.timeit import timeit

class Tree(QTreeWidget):
    def __init__(self):
       super().__init__()
       self.plot_x_values = []
       self.plot_stim1_values = []
       self.plot_stim2_values = []
       self.baseline_values = []
       pass

    def set_app(self, app):
        self.app = app

    def first_stimulation(self):
        # self.run_button.setEnabled(True)
        tree_item = QTreeWidgetItem()
        self.style_tree_item(tree_item)
        self.addTopLevelItem(tree_item)
        self.setCurrentItem(tree_item)
        self.app.tree_switch_window.setCurrentIndex(0)
        for i in [4, 11, 23]:
                tree_item.setText(i, "square")
        for i in [17, 18, 19, 30]:
            tree_item.setText(i, "False")
        #self.app.canals_to_tree(first=True)
        #self.app.type_to_tree(first=True)
        #self.check_global_validity()

    def add_brother(self):
        if self.currentItem():
            tree_item = QTreeWidgetItem()
            self.style_tree_item(tree_item)
            parent = self.selectedItems()[0].parent()
            if parent:
                index = parent.indexOfChild(self.selectedItems()[0])
                parent.insertChild(index + 1, tree_item)
            else:
                self.addTopLevelItem(tree_item)
            self.setCurrentItem(tree_item)
            for i in [4, 11, 23]:
                tree_item.setText(i, "square")
            for i in [17, 18, 19, 30]:
                tree_item.setText(i, "False")
            #self.app.type_to_tree(first=True)
            #self.app.canals_to_tree(first=True)
            #self.check_global_validity()

    def add_child(self):
        if self.currentItem():
            self.currentItem().setIcon(
                0, QIcon(os.path.join("gui", "icons", "package.png"))
            )
            self.currentItem().setIcon(
                20, QIcon(os.path.join("gui", "icons", "alert-triangle.png"))
            )
            tree_item = QTreeWidgetItem()
            self.style_tree_item(tree_item)
            self.selectedItems()[0].addChild(tree_item)
            self.selectedItems()[0].setExpanded(True)
            self.setCurrentItem(tree_item)
            for i in [4, 11, 23]:
                tree_item.setText(i, "square")
            for i in [17, 18, 19, 30]:
                tree_item.setText(i, "False")
            #self.app.type_to_tree(first=True)
            #self.app.canals_to_tree(first=True)
            #self.check_global_validity()

    def delete_branch(self):
        try:
            parent = self.currentItem().parent()
            if parent.childCount() == 1:
                parent.setIcon(
                    0, QIcon(os.path.join("gui", "icons", "wave-square.png"))
                )
        except Exception:
            parent = self.invisibleRootItem()
        parent.removeChild(self.currentItem())
        #self.check_global_validity()
        #self.app.actualize_window()

    @timeit
    def graph(self, item=None):
        try:
            if item == self.currentItem() or item == self.invisibleRootItem():
                self.elapsed_time = 0
                self.plot_x_values = []
                self.plot_stim1_values = []
                self.plot_stim2_values = []
                self.plot_stim3_values = []
                self.baseline_values = []
            if item.childCount() > 0:
                if item == self.invisibleRootItem():
                    jitter, block_delay, iterations_number = 0, 0, 1
                else:
                    jitter = float(item.text(3))
                    iterations_number = int(item.text(1))
                    block_delay = float(item.text(2))
                for iteration in range(iterations_number):
                    for index in range(item.childCount()):
                        child = item.child(index)
                        self.graph(child)
                    delay = block_delay + random.random() * jitter
                    time_values = np.linspace(
                        self.elapsed_time,
                        self.elapsed_time + delay,
                        int(round(delay * 3000)),
                    )
                    data = np.zeros(len(time_values))
                    self.elapsed_time += delay
                    self.plot_x_values = np.concatenate(
                        (self.plot_x_values, time_values)
                    )
                    self.plot_stim1_values = np.concatenate(
                        (self.plot_stim1_values, data)
                    )
                    self.plot_stim2_values = np.concatenate(
                        (self.plot_stim2_values, data)
                    )
            else:
                duration = float(item.text(6))
                time_values = np.linspace(0, duration, int(round(duration * 3000)))
                if item.text(18) == "True":
                    (
                        sign_type,
                        pulses,
                        jitter,
                        width,
                        frequency,
                        duty,
                        heigth,
                    ) = self.get_attributes(item, canal=1)
                    print(time_values,
                        sign_type,
                        width,
                        pulses,
                        jitter,
                        frequency,
                        duty,
                        heigth,)
                    data = make_signal(
                        time_values,
                        sign_type,
                        width,
                        pulses,
                        jitter,
                        frequency,
                        duty,
                        heigth,
                    )
                    print("data")
                    print(self.plot_stim1_values, data)
                    self.plot_stim1_values = np.concatenate(
                        (self.plot_stim1_values, data)
                    )
                else:
                    print("no stim")
                    print(self.plot_stim1_values, np.zeros(len(time_values)))
                    self.plot_stim1_values = np.concatenate(
                        (self.plot_stim1_values, np.zeros(len(time_values)))
                    )

                if item.text(19) == "True":
                    (
                        sign_type2,
                        pulses2,
                        jitter2,
                        width2,
                        frequency2,
                        duty2,
                        heigth2,
                    ) = self.get_attributes(item, canal=2)
                    data2 = make_signal(
                        time_values,
                        sign_type2,
                        width2,
                        pulses2,
                        jitter2,
                        frequency2,
                        duty2,
                        heigth2,
                    )
                    self.plot_stim2_values = np.concatenate(
                        (self.plot_stim2_values, data2)
                    )
                else:
                    self.plot_stim2_values = np.concatenate(
                        (self.plot_stim2_values, np.zeros(len(time_values)))
                    )

                if item.text(30) == "True":
                    (
                        sign_type3,
                        pulses3,
                        jitter3,
                        width3,
                        frequency3,
                        duty3,
                        heigth3,
                    ) = self.get_attributes(item, canal=3)
                    data3 = make_signal(
                        time_values,
                        sign_type3,
                        width3,
                        pulses3,
                        jitter3,
                        frequency3,
                        duty3,
                        heigth3,
                    )
                    self.plot_stim3_values = np.concatenate(
                        (self.plot_stim3_values, data3)
                    )
                else:
                    self.plot_stim3_values = np.concatenate(
                        (self.plot_stim3_values, np.zeros(len(time_values)))
                    )

                if (
                    item.text(18) == "False"
                    and item.text(19) == "False"
                    and item.text(30) == "False"
                    and item.text(17) == "True"
                ):
                    baseline_start_index = len(self.plot_x_values)
                    baseline_stop_index = len(self.plot_x_values) + len(time_values)
                    self.baseline_values.append(
                        [baseline_start_index, baseline_stop_index]
                    )
                time_values += self.elapsed_time
                self.plot_x_values = np.concatenate((self.plot_x_values, time_values))
                self.elapsed_time += duration
        except Exception as err:
            print(err)
            self.plot_x_values = []
            self.plot_stim1_values = []
            self.plot_stim2_values = []
            self.plot_stim3_values = []
            self.elapsed_time = 0
    @timeit
    def check_global_validity(self, item=None):
        if item is None:
            item = self.invisibleRootItem()
            # if self.check_block_validity(item) is True and (self.ir_checkbox.isChecked() or self.red_checkbox.isChecked() or self.green_checkbox.isChecked() or self.fluorescence_checkbox.isChecked()):
            if self.check_block_validity(item):
                self.app.enable_run()
            else:
                self.app.disable_run()
        elif item.childCount() > 0:
            self.set_icon(item, self.check_block_validity(item))
        else:
            self.set_icon(item, self.check_stim_validity(item))
        for child_index in range(item.childCount()):
            self.check_global_validity(item.child(child_index))

    def check_stim_validity(self, item=None):
        valid = True
        if item is None:
            item == self.currentItem()
        if item.text(6) == "":
            valid = False

        if item.text(18) == "True":
            if (
                item.text(4) == "square"
                and item.text(9) != ""
                and item.text(10) != ""
                and item.text(21) != ""
            ):
                pass
            elif (
                item.text(4) == "random-square"
                and item.text(5) != ""
                and item.text(7) != ""
                and item.text(8) != ""
            ):
                pass
            else:
                valid = False

        if item.text(19) == "True":
            if (
                item.text(11) == "square"
                and item.text(15) != ""
                and item.text(16) != ""
                and item.text(22) != ""
            ):
                pass
            elif (
                item.text(11) == "random-square"
                and item.text(12) != ""
                and item.text(13) != ""
                and item.text(4) != ""
            ):
                pass
            else:
                valid = False
        if item.text(30) == "True":
            if (
                item.text(23) == "square"
                and item.text(27) != ""
                and item.text(28) != ""
                and item.text(29) != ""
            ):
                pass
            elif (
                item.text(23) == "random-square"
                and item.text(24) != ""
                and item.text(25) != ""
                and item.text(26) != ""
            ):
                pass
            else:
                valid = False
        return valid

    def check_block_validity(self, item=None):
        valid = True
        if item is None:
            item = self.currentItem()
        if item.childCount() == 0:
            return self.check_stim_validity(item=item)
        if item == self.invisibleRootItem():
            if item.childCount() == 0:
                valid = False
        elif item.childCount() > 0:
            valid = item.text(1) != "" and item.text(2) != "" and item.text(3) != ""
        for child_index in range(item.childCount()):
            if not self.check_block_validity(item.child(child_index)):
                valid = False
        return valid

    def get_attributes(self, item, canal=1):
        if canal == 1:
            sign_type = item.text(4)
            try:
                pulses = int(item.text(5))
                jitter = float(item.text(7))
                width = float(item.text(8))
            except Exception:
                pulses, jitter, width = 0, 0, 0
            try:
                frequency = float(item.text(9))
                duty = float(item.text(10)) / 100
                heigth = float(item.text(21))
            except Exception:
                frequency, duty, heigth = 0, 0, 0
            return (sign_type, pulses, jitter, width, frequency, duty, heigth)

        elif canal == 2:
            sign_type = item.text(11)
            try:
                pulses = int(item.text(12))
                jitter = float(item.text(13))
                width = float(item.text(14))
            except Exception:
                pulses, jitter, width = 0, 0, 0
            try:
                frequency = float(item.text(15))
                duty = float(item.text(16)) / 100
                heigth = float(item.text(22))
            except Exception:
                frequency, duty, heigth = 0, 0, 0
            return (sign_type, pulses, jitter, width, frequency, duty, heigth)

        elif canal == 3:
            sign_type = item.text(23)
            try:
                pulses = int(item.text(23))
                jitter = float(item.text(25))
                width = float(item.text(26))
            except Exception:
                pulses, jitter, width = 0, 0, 0
            try:
                frequency = float(item.text(27))
                duty = float(item.text(28)) / 100
                heigth = float(item.text(29))
            except Exception:
                frequency, duty, heigth = 0, 0, 0
            return (sign_type, pulses, jitter, width, frequency, duty, heigth)

    def set_icon(self, item, valid):
        try:
            if valid:
                item.setIcon(
                    20, QIcon(os.path.join("gui", "icons", "circle-check.png"))
                )
            else:
                item.setIcon(
                    20, QIcon(os.path.join("gui", "icons", "alert-triangle.png"))
                )
        except Exception:
            pass

    def style_tree_item(self, item):
        item.setIcon(20, QIcon(os.path.join("gui", "icons", "alert-triangle.png")))
        item.setForeground(0, QBrush(QColor(211, 211, 211)))
        item.setIcon(0, QIcon(os.path.join("gui", "icons", "wave-square.png")))
        item.setText(0, "No Name")