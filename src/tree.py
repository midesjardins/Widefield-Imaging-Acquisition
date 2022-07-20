import os
import random
import numpy as np
from src.waveforms import digital_square, make_signal
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtGui import QBrush, QColor, QIcon
from src.blocks import Block, Stimulation


class Tree(QTreeWidget):
    def __init__(self):
        """ Initialize the tree widget"""
        super().__init__()
        self.x_values = []
        self.stim1_values = []
        self.stim2_values = []
        self.baseline_values = []
        pass

    def first_stimulation(self):
        """ Create the first stimulation in the tree """
        tree_item = QTreeWidgetItem()
        self.addTopLevelItem(tree_item)
        self.set_defaults(tree_item)

    def add_brother(self):
        """ Add a brother to the current item in the tree"""
        if self.currentItem():
            tree_item = QTreeWidgetItem()
            parent = self.selectedItems()[0].parent()
            if parent:
                index = parent.indexOfChild(self.selectedItems()[0])
                parent.insertChild(index + 1, tree_item)
            else:
                self.addTopLevelItem(tree_item)
            self.set_defaults(tree_item)

    def add_child(self):
        """Add a child to the current item in the tree"""
        if self.currentItem():
            self.currentItem().setIcon(
                0, QIcon(os.path.join("gui", "icons", "package.png"))
            )
            self.currentItem().setIcon(
                20, QIcon(os.path.join("gui", "icons", "alert-triangle.png"))
            )
            tree_item = QTreeWidgetItem()
            self.selectedItems()[0].addChild(tree_item)
            self.selectedItems()[0].setExpanded(True)
            self.set_defaults(tree_item)

    def set_defaults(self, item):
        """ Set the default values for a new item in the tree"""
        self.setCurrentItem(item)
        item.setIcon(20, QIcon(os.path.join("gui", "icons", "alert-triangle.png")))
        item.setForeground(0, QBrush(QColor(211, 211, 211)))
        item.setIcon(0, QIcon(os.path.join("gui", "icons", "wave-square.png")))
        item.setText(0, "No Name")
        for i in [4, 11, 23]:
            item.setText(i, "square")
        for i in [17, 18, 19, 30]:
            item.setText(i, "False")

    def delete_item(self):
        """ Delete the current item in the tree and its children"""
        try:
            parent = self.currentItem().parent()
            if parent.childCount() == 1:
                parent.setIcon(
                    0, QIcon(os.path.join("gui", "icons", "wave-square.png"))
                )
        except Exception:
            parent = self.invisibleRootItem()
        parent.removeChild(self.currentItem())

    def create_tree_item(self, block, parent=None):
        """
        Recursively create the items in the block dictionary

        Args:
            block (dict): The dictionary containing the blocks to create
            parent (QTreeWidgetItem): The parent of the block to print. Defaults to None.
        """
        if block["type"] == "Block":
            if block["name"] == "root":
                tree_item = self.invisibleRootItem()
            else:
                tree_item = QTreeWidgetItem()
                parent.addChild(tree_item)
                self.set_block_attributes(tree_item, block)
            for item in block["data"]:
                self.create_tree_item(item, parent=tree_item)
        elif block["type"] == "Stimulation":
            tree_item = QTreeWidgetItem()
            parent.addChild(tree_item)
            self.set_stim_attributes(tree_item, block)

    def set_block_attributes(self, tree_item, dictionary):
        """ Set the attributes of a block in the tree

        Args:
            tree_item (QTreeWidgetItem): The tree item on which to apply the attributes
            dictionary (dict): The dictionary containing the attributes
        """
        tree_item.setIcon(0, QIcon(os.path.join("gui", "icons", "package.png")))
        tree_item.setText(0, dictionary["name"])
        tree_item.setText(1, str(dictionary["iterations"]))
        tree_item.setText(2, str(dictionary["delay"]))
        tree_item.setText(3, str(dictionary["jitter"]))

    def set_stim_attributes(self, tree_item, dictionary):
        """ Set the attributes of a stimulation in the tree
        
        Args:
            tree_item (QTreeWidgetItem): The tree item on which to apply the attributes
            dictionary (dict): The dictionary containing the attributes
        """
        tree_item.setIcon(0, QIcon(os.path.join("gui", "icons", "wave-square.png")))
        tree_item.setText(0, dictionary["name"])
        tree_item.setText(4, str(dictionary["type1"]))
        tree_item.setText(5, str(dictionary["pulses"]))
        tree_item.setText(6, str(dictionary["duration"]))
        tree_item.setText(7, str(dictionary["jitter"]))
        tree_item.setText(8, str(dictionary["width"]))
        tree_item.setText(21, str(dictionary["heigth"]))
        tree_item.setText(9, str(dictionary["freq"]))
        tree_item.setText(10, str(dictionary["duty"]))
        tree_item.setText(11, str(dictionary["type2"]))
        tree_item.setText(12, str(dictionary["pulses2"]))
        tree_item.setText(13, str(dictionary["jitter2"]))
        tree_item.setText(14, str(dictionary["width2"]))
        tree_item.setText(22, str(dictionary["heigth2"]))
        tree_item.setText(15, str(dictionary["freq2"]))
        tree_item.setText(16, str(dictionary["duty2"]))
        tree_item.setText(23, str(dictionary["type3"]))
        tree_item.setText(24, str(dictionary["pulses3"]))
        tree_item.setText(25, str(dictionary["jitter3"]))
        tree_item.setText(26, str(dictionary["width3"]))
        tree_item.setText(29, str(dictionary["heigth3"]))
        tree_item.setText(27, str(dictionary["freq3"]))
        tree_item.setText(28, str(dictionary["duty3"]))
        tree_item.setText(18, str(dictionary["canal1"]))
        tree_item.setText(19, str(dictionary["canal2"]))
        tree_item.setText(30, str(dictionary["canal3"]))

    def graph(self, item=None, current=False):
        """
        Generate the x and y values for an item in the tree

        Args:
            item (QTreeWidgetItem): The item to graph. Defaults to current item.
        """
        try:
            if item == self.invisibleRootItem() or current:
                print("root")
                self.elapsed_time = 0
                self.x_values = []
                self.stim1_values = []
                self.stim2_values = []
                self.stim3_values = np.empty(0, dtype=bool)
            if item.childCount() > 0:
                if item == self.invisibleRootItem():
                    jitter, block_delay, iterations = 0, 0, 1
                else:
                    jitter = float(item.text(3))
                    iterations = int(item.text(1))
                    block_delay = float(item.text(2))
                for i in range(iterations):
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
                    ddata = np.full(len(time_values), False)
                    self.elapsed_time += delay
                    self.x_values = np.concatenate((self.x_values, time_values))
                    self.stim1_values = np.concatenate((self.stim1_values, data))
                    self.stim2_values = np.concatenate((self.stim2_values, data))
                    self.stim3_values = np.concatenate((self.stim3_values, ddata))
            else:
                print(item.text(0))
                print(item.text(6))
                duration = float(item.text(6))
                # PROBLEMATIC
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
                    self.stim1_values = np.concatenate((self.stim1_values, data))
                else:
                    self.stim1_values = np.concatenate(
                        (self.stim1_values, np.zeros(len(time_values)))
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
                    self.stim2_values = np.concatenate((self.stim2_values, data2))
                else:
                    self.stim2_values = np.concatenate(
                        (self.stim2_values, np.zeros(len(time_values)))
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

                    data3 = digital_square(time_values, frequency3, duty3)
                    self.stim3_values = np.concatenate((self.stim3_values, data3))
                else:
                    self.stim3_values = np.concatenate(
                        (self.stim3_values, np.full(len(time_values), False))
                    )


                if (
                    item.text(18) == "False"
                    and item.text(19) == "False"
                    and item.text(30) == "False"
                    and item.text(17) == "True"
                ):
                    baseline_start_index = len(self.x_values)
                    baseline_stop_index = len(self.x_values) + len(time_values)
                    self.baseline_values.append(
                        [baseline_start_index, baseline_stop_index]
                    )
                time_values += self.elapsed_time
                self.x_values = np.concatenate((self.x_values, time_values))
                self.elapsed_time += duration
        except Exception as err:
            print("graph err")
            print(err)
            self.x_values = []
            self.stim1_values = []
            self.stim2_values = []
            self.stim3_values = np.empty(0, dtype=bool)
            self.elapsed_time = 0

    def create_blocks(self, item=None):
        """ Recursively create blocks from tree items
        
        Args:
            item (QTreeWidgetItem): The item to create blocks from. Defaults to current item.
        
        Returns:
            Block: A master block containing all the children blocks
        """
        try:
            if item is None:
                item = self.invisibleRootItem()
            if item.childCount() > 0:
                children = []
                for index in range(item.childCount()):
                    children.append(self.create_blocks(item=item.child(index)))
                if item == self.invisibleRootItem():
                    return Block("root", children)
                return Block(
                    item.text(0),
                    children,
                    delay=int(item.text(2)),
                    iterations=int(item.text(1)),
                )
            else:
                duration = int(item.text(6))
                if item.text(18) == "True":
                    canal1 = True
                    (
                        sign_type,
                        pulses,
                        jitter,
                        width,
                        frequency,
                        duty,
                        heigth,
                    ) = self.get_attributes(item, canal=1)
                else:
                    canal1 = False
                    sign_type, pulses, jitter, width, frequency, duty, heigth = (
                        "",
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                    )

                if item.text(19) == "True":
                    canal2 = True
                    (
                        sign_type2,
                        pulses2,
                        jitter2,
                        width2,
                        frequency2,
                        duty2,
                        heigth2,
                    ) = self.get_attributes(item, canal=2)
                else:
                    sign_type2, pulses2, jitter2, width2, frequency2, duty2, heigth2 = (
                        "",
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                    )
                    canal2 = False

                if item.text(30) == "True":
                    canal3 = True
                    (
                        sign_type3,
                        pulses3,
                        jitter3,
                        width3,
                        frequency3,
                        duty3,
                        heigth3,
                    ) = self.get_attributes(item, canal=3)
                else:
                    sign_type3, pulses3, jitter3, width3, frequency3, duty3, heigth3 = (
                        "",
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                    )
                    canal3 = False
                dictionary = {
                    "type": "Stimulation",
                    "name": item.text(0),
                    "duration": duration,
                    "canal1": canal1,
                    "canal2": canal2,
                    "canal3": canal3,
                    "type1": sign_type,
                    "pulses": pulses,
                    "jitter": jitter,
                    "width": width,
                    "freq": frequency,
                    "duty": duty,
                    "heigth": heigth,
                    "type2": sign_type2,
                    "pulses2": pulses2,
                    "jitter2": jitter2,
                    "width2": width2,
                    "freq2": frequency2,
                    "duty2": duty2,
                    "heigth2": heigth2,
                    "type3": sign_type3,
                    "pulses3": pulses3,
                    "jitter3": jitter3,
                    "width3": width3,
                    "freq3": frequency3,
                    "duty3": duty3,
                    "heigth3": heigth3,
                }
                return Stimulation(dictionary)
        except Exception as err:
            print(err)
            pass

    def check_global_validity(self, item=None):
        """
        Check if an item is a valid stimulation/block.

        Args:
            item (QTreeWidgetItem): The item to check. Defaults to the root item.
        """
        if item is None:
            item = self.invisibleRootItem()
            if self.check_block_validity(item):
                return True
            else:
                return False
        elif item.childCount() > 0:
            self.set_icon(item, self.check_block_validity(item))
        else:
            self.set_icon(item, self.check_stim_validity(item))
        for child_index in range(item.childCount()):
            self.check_global_validity(item.child(child_index))

    def check_stim_validity(self, item=None):
        """
        Check if a stimulation is valid.

        Args:
            item (QTreeWidgetItem): The item to check. Defaults to current item.
        """
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
        self.set_icon(item, valid)
        return valid

    def check_block_validity(self, item=None):
        """
        Check if a block is valid.

        Args:
            item (QTreeWidgetItem): The item to check. Defaults to current item.
        """
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
        self.set_icon(item, valid)
        return valid

    def get_attributes(self, item, canal=1):
        """
        Get the attributes of a stimulation.

        Args:
            item (QTreeWidgetItem): The item to get the attributes from.
            canal (int): The canal to get the attributes from. Defaults to 1.
        """
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
            pulses, jitter, width = 0, 0, 0
            try:
                frequency = float(item.text(27))
                duty = float(item.text(28)) / 100
            except Exception:
                frequency, duty = 1, 0
            return (sign_type, pulses, jitter, width, frequency, duty, 5)

    def set_icon(self, item, valid):
        """
        Set the icon of a tree item.

        Args:
            item (QTreeWidgetItem): The item to set the icon for.
            valid (bool): Whether the item is valid or not.
        """
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
