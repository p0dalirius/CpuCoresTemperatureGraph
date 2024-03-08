#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import math
import matplotlib
import matplotlib.pyplot
import psutil
import platform
import os
import time
from threading import *


VERSION = "1.1"


def get_processor_info():
    if platform.system() == "Windows":
        return platform.processor()
    elif platform.system() == "Darwin":
        p = os.popen("/usr/sbin/sysctl -n machdep.cpu.brand_string")
        model = p.read().strip()
        return model
    elif platform.system() == "Linux":
        p = os.popen("cat /proc/cpuinfo")
        data = p.read().strip()
        data = [l for l in data.split('\n') if l.startswith("model name\t:")]
        if len(data) != 0:
            model = data[0].split(':',1)[1].strip()
            return model
        else:
            return ""
    return ""


class Monitor(object):
    """docstring for Monitor."""

    def __init__(self, refresh_time=0.5, window_size=120):
        super(Monitor, self).__init__()
        self.window_size = window_size
        self.x_time = list(range(self.window_size))
        self.refresh_time = refresh_time

        self.running = True

        self.init_UI()
        self.update()

    def init_UI(self):
        """Documentation for init_UI"""

        matplotlib.rcParams['toolbar'] = 'None'
        matplotlib.rcParams['grid.color'] = '#3c3c3c'

        matplotlib.pyplot.ion()

        self.fig = matplotlib.pyplot.figure()

        self.fig.suptitle(get_processor_info(), fontsize=14, color='white')

        self.fig.patch.set_facecolor('black')
        self.fig.patch.set_edgecolor('white')

        cpu_cores = [
            c for c in psutil.sensors_temperatures()["coretemp"]
            if c.label.startswith("Core")
        ]

        self.views = {}

        square_size = round(math.sqrt(len(cpu_cores)))
        for ncol in range(0, square_size):
            for nrow in range(0, square_size):
                index = ncol*square_size + nrow
                if (index < len(cpu_cores)):
                    cpucore = cpu_cores[index]
                    self.views[cpucore.label] = {
                        "ax": self.fig.add_subplot(square_size, square_size, index+1),
                        "data": {
                            "current": [0] * self.window_size,
                            "high": [cpu_cores[index].high] * self.window_size,
                            "critical": [cpu_cores[index].critical] * self.window_size,
                        },
                        "core": cpucore
                    }
        
        matplotlib.pyplot.tight_layout(pad=1, w_pad=1, h_pad=1)
        
        return

    def update(self):
        """
        
        """
        def dyn_update(ax, lx, data, marker='', title='', color="blue"):
            ax.clear()

            ax.patch.set_facecolor('#1c1c1c')
            ax.patch.set_edgecolor('white')
            # Set the plot border to white
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white') 
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            # Set the axis ticks to white
            ax.tick_params(axis='x', colors='black')
            ax.tick_params(axis='y', colors='white')
            # Set the labels to white
            ax.yaxis.label.set_color('white')
            ax.xaxis.label.set_color('black')
            # Set the title to white
            ax.title.set_color('white')

            ax.plot(lx, data["current"], marker=marker, color=color, label="Temp (C)")
            ax.fill_between(lx, 0, data["current"], alpha=.5, color=color)
            ax.plot(lx, data["high"], marker=marker, color="orange", label=None)
            ax.plot(lx, data["critical"], marker=marker, color="red", label=None)

            ax.set_title(title)
            ax.set_ylabel("Temp (°C)")
            ax.grid(True)
            max_value_critical = max(data["critical"])
            ax.set_ylim(0, 1.1*max_value_critical)
            ax.set_xlim(0, max(lx)+1)

            return None
        
        #==========================================

        # Iterate on cores
        for core_label in self.views.keys():
            cpucore = [c for c in psutil.sensors_temperatures()["coretemp"] if c.label == core_label]
            if len(cpucore) == 0:
                cpucore = 0
            else:
                cpucore = cpucore[0]
            
            self.views[core_label]["data"]["current"] = self.views[core_label]["data"]["current"][1:self.window_size] + [cpucore.current]
            self.views[core_label]["data"]["high"] = self.views[core_label]["data"]["high"][1:self.window_size] + [cpucore.high]
            self.views[core_label]["data"]["critical"] = self.views[core_label]["data"]["critical"][1:self.window_size] + [cpucore.critical]

            dyn_update(
                ax=self.views[core_label]["ax"],
                lx=self.x_time,
                data=self.views[core_label]["data"],
                title=cpucore.label,
                color='green'
            )

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        return None

    def run(self):
        """
        Generate data for monitoring purposes.

        This function generates data by reading network interface statistics from specified hosts,
        calculates the total transmitted (TX) and received (RX) bytes excluding loopback interface,
        and updates the internal data arrays for TX, RX, and time.

        Returns:
        None
        """
        while self.running:
            time.sleep(self.refresh_time)
            try:
                self.update()
            except Exception as e:
                self.running = False
        return None

    def request_stop(self):
        """Documentation for stop"""
        self.running = False
        return None


def parseArgs():
    parser = argparse.ArgumentParser(add_help=True, description="")

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode. (default: False).")

    options = parser.parse_args()

    return options


if __name__ == '__main__':
    options = parseArgs()
    Monitor(window_size=600, refresh_time=0.1).run()
