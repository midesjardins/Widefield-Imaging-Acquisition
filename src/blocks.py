import json


class Stimulation:
    def __init__(self, dictionary):
        """ Initialize the stimulation object with a dictionary
        
        Args:
            dictionary (dict): dictionary containing the stimulation parameters
        """
        self.dico = dictionary

    def __str__(self, indent=""):
        """ Return a string representation of the stimulation object 
        
        Args:
            indent (str): indentation for the current line of the string representation
            
        Returns:
            str: string representation of the stimulation object
        """
        return_value = []
        if self.dico["type1"] == "random-square" and self.dico["canal1"]:
            return_value.append(
                indent
                + f"{self.dico['name']} - Channel 1 --- Duration: {self.dico['duration']}, Pulses: {self.dico['pulses']}, Width: {self.dico['width']}, Jitter: {self.dico['jitter']}"
            )
        elif self.dico["type1"] == "square" and self.dico["canal1"]:
            return_value.append(
                indent
                + f"{self.dico['name']} - Channel 1 --- Duration: {self.dico['duration']}, Heigth: {self.dico['heigth']}, Frequency: {self.dico['freq']}, Duty: {self.dioc['duty']}"
            )
        if self.dico["type2"] == "random-square" and self.dico["canal2"]:
            return_value.append(
                indent
                + f"{self.dico['name']} - Channel 2 --- Duration: {self.dico['duration']}, Pulses: {self.dico['pulses2']}, Width: {self.dico['width2']}, Jitter: {self.dico['jitter2']}"
            )
        elif self.dico["type2"] == "square" and self.dico["canal2"]:
            return_value.append(
                indent
                + f"{self.dico['name']} - Channel 2 --- Duration: {self.dico['duration']}, Heigth: {self.dico['heigth2']}, Frequency: {self.dico['freq2']}, Duty: {self.dico['duty2']}"
            )
        if self.dico["type3"] == "random-square" and self.dico["canal3"]:
            return_value.append(
                indent
                + f"{self.dico['name']} - Channel 3 --- Duration: {self.dico['duration']}, Pulses: {self.dico['pulses3']}, Width: {self.dico['width3']}, Jitter: {self.dico['jitter3']}"
            )
        elif self.dico["type3"] == "square" and self.dico["canal3"]:
            return_value.append(
                indent
                + f"{self.dico['name']} - Channel 3 --- Duration: {self.dico['duration']}, Heigth: {self.dico['heigth3']}, Frequency: {self.dico['freq3']}, Duty: {self.dico['duty3']}"
            )
        if (
            not self.dico["canal1"]
            and not self.dico["canal2"]
            and not self.dico["canal3"]
        ):
            return_value.append(
                indent
                + f"{self.dico['name']} - No Channels --- Duration: {self.dico['duration']}"
            )
        return_value.append("***")
        return "\n".join(return_value)

    def to_json(self):
        """ Return a json representation of the stimulation object """
        return self.dico


class Block:
    def __init__(self, name, data, delay=0, iterations=1, jitter=0):
        """ Initialize the block object
        
        Args:
            name (str): Name of the block
            data (list): List of stimulation/block objects
            delay (int): Delay between each block iteration
            iterations (int): Number of iterations of the block
            jitter (int): Jitter of the block
        """
        self.name = name
        self.data = data
        self.iterations = iterations
        self.delay = delay
        self.jitter = jitter
        self.exp = None

    def __str__(self, indent=""):
        """ Return a string representation of the block object

        Args:
            indent (str): indentation for the current line of the string representation

        Returns:
            str: string representation of the block object
        """
        stim_list = []
        for iteration in range(self.iterations):
            stim_list.append(
                indent
                + self.name
                + f" ({iteration+1}/{self.iterations}) --- Delay: {self.delay}, Jitter: {self.jitter}"
            )
            for item in self.data:
                stim_list.append(item.__str__(indent=indent + "   "))
        return "\n".join(stim_list)

    def to_json(self):
        """ Return a json representation of the block object """
        data_list = []
        for item in self.data:
            data_list.append(item.to_json())
        dictionary = {
            "type": "Block",
            "name": self.name,
            "iterations": self.iterations,
            "delay": self.delay,
            "jitter": self.jitter,
            "data": data_list,
        }
        return dictionary


class Experiment:
    def __init__(
        self, blocks, framerate, exposition, mouse_id, directory, daq, name="No Name"
    ):
        """ Initialize the experiment object

        Args:
            blocks (list): List of block objects
            framerate (int): Framerate of the experiment
            exposition (int): Exposition time of the experiment
            mouse_id (str): Mouse ID of the experiment
            directory (str): Directory of the experiment
            daq (str): DAQ used for the experiment
            name (str): Name of the experiment
        """
        self.name = name
        self.blocks = blocks
        self.framerate = framerate
        self.exposition = exposition
        self.mouse_id = mouse_id
        self.directory = directory + f"/{name}"
        self.daq = daq

    def save(self, extents=None):
        """ Save the experiment object to multiple files

        Args:
            extents (list): Positions of the ROI corners used for the experiment
        """
        print("saving exeperiment")
        with open(f"{self.directory}/experiment-metadata.txt", "w") as file:
            file.write(
                f"Blocks\n{self.blocks.__str__()}\n\nFramerate\n{self.framerate}\n\nExposition\n{self.exposition}\n\nMouse ID\n{self.mouse_id}"
            ) 

        dictionary = {
            "Blocks": self.blocks.to_json(),
            "Lights": self.daq.return_lights(),
            "Framerate": self.framerate,
            "Exposition": self.exposition,
            "Mouse ID": self.mouse_id,
            "Dimensions": [round(extents[1])-round(extents[0]), round(extents[3])-round(extents[2])]
        }

        with open(f"{self.directory}/experiment-metadata.json", "w") as file:
            json.dump(dictionary, file)

        self.daq.camera.save(self.directory, extents)
        self.daq.save(self.directory)
