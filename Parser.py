import sys

"""Test parser class"""

class Error(Exception):
    """Parent class for errors in the parser

    Constants:
        NAN_ERROR -- Message for not a number error
        NAME -- The name for the error
        FORM1 -- The format the error should follow if info is given
        FORM2 -- The format the error should follow if no info given
    """

    NAN_ERROR = "Must Be A Valid Integer"
    NAME = "Error"
    FORM1 = "{}: '{}' {}" #if info/message given on the error 
    FORM2 = "{}: {}" #error without further info

    def __init__(self, info, error):
        self.info = info # record the info/message for the error
        self.error = [] # the error is a list of errors
        if type(error) == type(""): # if it's a simple string then it has to be appended to the list
            if self.info: # If info has been given
                self.error.append(self.FORM1.format(self.NAME, info, error)) # use form 1 if info/message on the error is given
            else:
                self.error.append(self.FORM2.format(self.NAME, error)) # else use form 2. error without info/message. States 'Error' and type of error
        else: # else we just need to add a header error, and append the rest of the errors
            self.error.append(self.FORM2.format(self.NAME, self.info if self.info else "")) # form 2 works here too
            self.error += error.error

    def __str__(self):
        output_str = "" # start with an empty string
        for indent, message in enumerate(self.error): # loop through the errors, appending and indenting each as we go
            output_str = "{}\n{}{}".format(output_str, "\t" * indent, message) # this appends and indents the messages nicely
        return output_str.lstrip("\n") # remove that pesky new line at the start

    def output(self):
        print(self) # print out the error
        exit() # halt execution

class RouterIdError(Error):
    """Exception raised for errors regarding router ids

    Constants:
        NEGATIVE_ERROR -- Message for negative id error
        EXISTS_ERROR -- Message for an existing router id used
        FORMAT -- Output format for error
    """

    NEGATIVE_ERROR = "Must Be A Positive Integer"
    EXISTS_ERROR = "Router ID has been used before"
    NAME = "RouterIdError"

class PortError(Error):
    """Exception raised for errors regarding port numbers

    Constants:
        RANGE_ERROR -- Message for port out of range
        EXISTS_ERROR -- Message for port that exists

    Attributes:
        port -- invalid port number
        message -- explanation of the error
        NAME -- The name for the error
    """

    EMPTY_ERROR = "Empty Port List"
    RANGE_ERROR = "Port Out Of Range (1024 - 64000)" # so there's no likely conflict with another application if num < 1024
    EXISTS_ERROR = "Port Already Exists" # port num already in use
    NAME = "PortError"

class MetricError(Error):
    """Exception raised for errors regarding metrics

    Constants:
        RANGE_ERROR -- Message for metric out of range
        NAME -- The name for the error
    """

    RANGE_ERROR = "Metric Out Of Range (1 - 16)"
    NAME = "MetricError"

class TimeError(Error):
    """Exception raised for errors regarding metrics

    Constants:
        INVALID_ERROR -- Message for times less than one
        INVALID_PERIOD_ERROR -- Message for a period that does not satisfy period>=1; period*6=timeout; period*8=garbage
        INVALID_TIMEOUT_ERROR -- Message for a timeout that does not satisfy timeout>=6; timeout=period*6; timeout=garbage*3/4
        INVALID_GARBAGE_ERROR -- Message for a garbage that does not satisfy garbage>=8; garbage=period*8; garbage=timeout*4/3
        NAME -- The name for the error
    """

    INVALID_ERROR = "Time Must Be Greater Than Zero"
    INVALID_PERIOD_ERROR = "Period must be at least 1, equal to timeout/6, and garbage/8"
    INVALID_TIMEOUT_ERROR = "Timeout must be at least 6, equal to 6 * period, and 3/4 * garbage"
    INVALID_GARBAGE_ERROR = "Garbage must be at least 8, equal to 4/3 * timeout, and 8 * period"
    NAME = "TimeError"

class OutputError(Error):
    """Exception raised for errors regarding outputs

    Constants:
        INVALID_ERROR -- Message for an invalid output format
        EMPTY_ERROR -- Message for an empty output list
        NAME -- The name for the error
        FORM1 -- The format the error should follow if info/message is given
        FORM2 -- The format the error should follow if no info/message given
    """

    INVALID_ERROR = "Invalid Output Format (Port-Metric-ID)"
    EMPTY_ERROR = "Empty Output List"
    NAME = "OutputError"
    FORM1 = "{}: Output {}: {}"
    FORM2 = "{}: Output {}:"

class ConfigError(Error):
    """Exception raised for errors regarding config file

    Constants:
        EXISTS_ERROR -- Message for an entry that exists
        INVALID_ERROR -- Message for an invalid entry
        NAME -- The name for the error
        FORM1 -- The format the error should follow if info is given
        FORM2 -- The format the error should follow if no info given
    """

    EXISTS_ERROR = "Entry Already Exists"
    INVALID_ERROR = "Invalid Entry"
    NAME = "ConfigError"
    FORM1 = "{}: Line {}: {}"
    FORM2 = "{}: Line {}:"

class Output(object):
    """Class for outputs

    Attributes:
        id -- Target router id
        port -- Port number of the target router
        metric -- Cost of the link to the target router
    """

    def __init__(self, port, metric, rid):
        self.id = rid
        self.port = port
        self.metric = metric

    def __repr__(self): #gives an output string, formatting id, port, metric "offcial represntation"
        return "(ID: {}, Port: {}, Metric: {})".format(self.id, self.port, self.metric)

class Config(object):
    """Class for the config

    Attributes:
        id -- the id of the router
        inputs -- a list of input ports for the router
        outputs -- a list of outputs for the router
        period -- the period that the router updates
        timeout -- the timeout period that the router uses
        garbage -- the garbage collection period that the router uses

    Methods:
        add_inputs -- add port to the inputs
        add_outputs -- add outputs to the outputs
        set_id -- set the id of the router
        set_period -- set the period for the router
        set_timeout -- set the timeout for the router
        set_garbage -- set the garbage collection for the router
        infer_timers -- fill in any gaps in the timers, defaulting if none set
    """

    def __init__(self):
        self.id = None
        self.inputs = []
        self.outputs = []
        self.period = None
        self.timeout = None
        self.garbage = None

    def __str__(self):
        #returns a string formatting config objects
        return "ID: {}\nInput Ports: {}\nOutputs: {}\nPeriod: {}\nTimeout: {}\nGarbage: {}".format(self.id, self.inputs, self.outputs, self.period, self.timeout, self.garbage)

    def set_id(self, rid, used_ids):
        self.id = validate_id(rid, used_ids) # validate the id before setting it

    def add_inputs(self, ports, used_ports):
        """validates port numbers and append them to a list. 
        Will give an error if there are no input ports"""
        ports = ports.strip(" ").split() # split them by the spaces
        if len(ports) == 0: # there must be at least one input port
            raise PortError(None, PortError.EMPTY_ERROR)
        for port in ports:
            self.inputs.append(validate_port(port.strip(","), used_ports)) # strip off the trailing comma, and validate ports as we append them

    def add_outputs(self, outputs, used_ports, used_ids):
        """adds id nums, port nums and metrics to an output object. Preforms error 
        checking on empty output lists, valid length of output object and if entries
        cannot be validated"""
        outputs = outputs.split() # split them by the spaces
        if len(outputs) == 0: # there must be at least one output
            raise OutputError(None, OutputError.EMPTY_ERROR)
        for output_num, output_str in enumerate(outputs):
            output_num += 1           
            output_list = output_str.strip(",").split("-") # strip off the trailing comma, and split it by the hyphens
            if len(output_list) != 3: # there must be exactly three values
                raise OutputError(output_num, OutputError.INVALID_ERROR) 
            try: # validate each entry before setting it
                port = validate_port(output_list[0], used_ports) #validate port
                metric = validate_metric(output_list[1]) #validate metric value
                rid = validate_id(output_list[2], used_ids)#
            except Error as error:
                raise OutputError(output_num, error)
            self.outputs.append(Output(port, metric, rid)) # combine the elements into an Output object and append it

    def set_period(self, period):
        """sets the period to at least 1 second, 6 second timeouts and 8 second
        garbage collections and checks the ratios"""
        self.period = validate_time(period) # validate the time is valid
        if (self.timeout and self.timeout/self.period != 6) or (self.garbage and self.garbage/self.period != 8): # validate that the period time is correct
            raise TimeError(self.period, TimeError.INVALID_PERIOD_ERROR) #doesn't keep the ratio

    def set_timeout(self, timeout):
        """sets the timeout and checks that timeout ration is kept"""
        self.timeout = validate_time(timeout) # validate the time is valid
        if (self.timeout < 6) or (self.period and float(self.timeout)/self.period != 6) or (self.garbage and float(self.timeout)/self.garbage != 0.75): # validate that the timeout is correct
            raise TimeError(self.timeout, TimeError.INVALID_TIMEOUT_ERROR)

    def set_garbage(self, garbage):
        """sets garbage collection and checks if ratios are kept"""
        self.garbage = validate_time(garbage) # validate the time is valid
        if (self.garbage < 8) or (self.period and float(self.garbage)/self.period != 8) or (self.timeout and self.timeout/float(self.garbage) != 0.75): # validate that the garbage is correct
            raise TimeError(self.garbage, TimeError.INVALID_GARBAGE_ERROR)

    def infer_timers(self):
        """sets the period (1 second to start and bases the other timers off it
        otherwise, it gives a default time period"""
        if self.period: # if a period is set, base the others off it
            self.timeout = self.period * 6
            self.garbage = self.period * 8
        elif self.timeout: # if the timeout is set but the period is not, base them off this
            self.period = int(self.timeout/6)
            self.garbage = int(self.timeout * 4.0/3.0)
        elif self.garbage: # if the garbage is set but the other two are not, base them off this
            self.period = int(self.garbage/8)
            self.timeout = int(self.garbage * 0.75)
        else: # else none are set, so default them
            self.period = 30
            self.timeout = 180
            self.garbage = 240 #change to 120??

def validate_time(time):
    """Validate that a time value is greater than or equal to 1"""
    try:
        time = int(time)
    except ValueError:
        raise TimeError(time, TimeError.NAN_ERROR)
    if time < 1:
        raise TimeError(time, TimeError.INVALID_ERROR)
    else:
        return time

def validate_id(rid, used_ids):
    """Validate that an id is a positive integer, and hasn't been used before"""
    try:
        rid = int(rid)
    except ValueError:
        raise RouterIdError(rid, RouterIdError.NAN_ERROR)
    if rid < 0:
        raise RouterIdError(rid, RouterIdError.NEGATIVE_ERROR)
    elif rid in used_ids: # collision check if a router already exsists
        raise RouterIdError(rid, RouterIdError.EXISTS_ERROR)
    else:
        used_ids.add(rid) # add router id to used ids to prevent collisions
        return rid

def validate_port(port, used_ports):
    """Validate that a port is in range, and hasn't been used before"""
    try:
        port = int(port)
    except ValueError:
        raise PortError(port, PortError.NAN_ERROR)
    if port < 1024 or port > 64000: # so there's no likely conflict with another application if # < 1024
        raise PortError(port, PortError.RANGE_ERROR)
    elif port in used_ports: # collision check
        raise PortError(port, PortError.EXISTS_ERROR)
    else:
        used_ports.add(port) # add the port to the set of used ports to ensure no collisions
        return port

def validate_metric(metric):
    """Validate the metric is an integer between 1 and 16"""
    try:
        metric = int(metric)
    except ValueError:
        raise MetricError(metric, MetricError.NAN_ERROR)
    if metric < 1 or metric > 16: # set 16 to infinity
        raise MetricError(metric, MetricError.RANGE_ERROR)
    else:
        return metric


def read_config(filename):
    """Read the config file stored in 'filename' and return a complete Config object"""
    config = Config() # stores relevant information
    used_ids = set() # store used router id's
    used_ports = set() # store used ports
    config_file = open(filename, "r") # open file
    config_lines = config_file.readlines() # read the lines into a list
    try:
        for line_num, line in enumerate(config_lines): # loop over all the lines
            line_num += 1 # # line numbers start at 1 not 0
            try:
                if line.startswith("router-id "):
                    if config.id: # if there is already an id
                        raise ConfigError(line_num, ConfigError.EXISTS_ERROR) # raise an error saying as much
                    config.set_id(line[9:].strip("\n"), used_ids) # strip out unneccesary information, and set the id
                elif line.startswith("input-ports "):
                    if config.inputs: # if there is already an input list
                        raise ConfigError(line_num, ConfigError.EXISTS_ERROR) # raise an error saying as much
                    config.add_inputs(line[11:].strip("\n"), used_ports) # strip out unneccesary information and add the inputs
                elif line.startswith("outputs "):
                    if config.outputs: # if there is already an output list
                        raise ConfigError(line_num, ConfigError.EXISTS_ERROR) # raise an error saying as much
                    config.add_outputs(line[7:].strip("\n"), used_ports, used_ids) # strip out unneccesary information and add outputs
                elif line.startswith("period "):
                    if config.period: # if there is already a period
                        raise ConfigError(line_num, ConfigError.EXISTS_ERROR) # raise an error saying as much
                    config.set_period(line[6:].strip("\n")) # strip out unneccesary information and set the period
                elif line.startswith("timeout "):
                    if config.timeout: # if there is already a timeout
                        raise ConfigError(line_num, ConfigError.EXISTS_ERROR) # raise an error saying as much
                    config.set_timeout(line[7:].strip("\n")) # strip out unneccesary information and set the timeout
                elif line.startswith("garbage "):
                    if config.garbage: # if there is already a garbage
                        raise ConfigError(line_num, ConfigError.EXISTS_ERROR) # raise an error saying as much
                    config.set_garbage(line[7:].strip("\n")) # strip out unneccesary information and set the garbage
                elif line.strip(" \n\t") == "": # ignore whitespace lines
                    pass
                else: # anything else is an invalid line, so raise an error
                    raise ConfigError(line_num, ConfigError.INVALID_ERROR)
            except ConfigError as error: # catch any ConfigError's and re-raise them
                raise error
            except Error as error: # catch any other error and change to a config error
                raise ConfigError(line_num, error)
        config.infer_timers() # infer the timers if any were not set
    except ConfigError as error: # any ConfigError's should now be printed out and the program halted
        error.output()
   # print(config) # print out the config object for viewing
    return config

def main():
    read_config(sys.argv[1])
    

if __name__ == "__main__":
    main()
