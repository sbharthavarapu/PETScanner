# Copyright 2019 Stanislav Pidhorskyi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import csv
from collections import OrderedDict
import matplotlib.pyplot as plt
import numpy as np
import torch
import os


class RunningMean:
    def __init__(self):
        self.mean = 0.0
        self.n = 0

    def __iadd__(self, value):
        self.mean = (float(value) + self.mean * self.n)/(self.n + 1)
        self.n += 1
        return self

    def reset(self):
        self.mean = 0.0
        self.n = 0

    def mean(self):
        return self.mean


class RunningMeanTorch:
    def __init__(self):
        self.values = []

    def __iadd__(self, value):
        self.values.append(value.detach().unsqueeze(0))
        return self

    def reset(self):
        self.values = []

    def mean(self):
        if len(self.values) == 0:
            return 0.0
        return float(torch.cat(self.values).mean().item())


class LossTracker:
    def __init__(self, output_folder='.'):
        self.tracks = OrderedDict()
        self.epochs = []
        self.means_over_epochs = OrderedDict()
        self.output_folder = output_folder

    def update(self, d):
        for k, v in d.items():
            if k not in self.tracks:
                self.add(k)
            self.tracks[k] += v

    def add(self, name, pytorch=True):
        assert name not in self.tracks, "Name is already used"
        if pytorch:
            track = RunningMeanTorch()
        else:
            track = RunningMean()
        self.tracks[name] = track
        self.means_over_epochs[name] = []
        return track

    def register_means(self, epoch):
        self.epochs.append(epoch)
        for key, value in self.tracks.items():
            self.means_over_epochs[key].append(value.mean())
            value.reset()

        with open(os.path.join(self.output_folder, 'log.csv'), mode='w') as csv_file:
            fieldnames = ['epoch'] + list(self.tracks.keys())
            writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(fieldnames)
            for i in range(len(self.epochs)):
                writer.writerow([self.epochs[i]] + [self.means_over_epochs[x][i] for x in self.tracks.keys()])

    def __str__(self):
        result = ""
        for key, value in self.tracks.items():
            result += "%s: %.7f, " % (key, value.mean())
        return result[:-2]

    def plot(self):
        plt.figure(figsize=(12, 8))
        for key in self.tracks.keys():
            plt.plot(self.epochs, self.means_over_epochs[key], label=key)

        plt.xlabel('Epoch')
        plt.ylabel('Loss')

        plt.legend(loc=4)
        plt.grid(True)
        plt.tight_layout()

        plt.savefig(os.path.join(self.output_folder, 'plot.png'))
        plt.close()
