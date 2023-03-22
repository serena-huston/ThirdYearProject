import sys 
sys.path.append("/Users/serenahuston/GitRepos/ThirdYearProject/src/")

from Utilities.constants import * 
import matplotlib.pyplot as plt
import numpy as np
import math 
import wave

import seaborn as sn
import pandas as pd

class DataPresentation:

    def __init__(self):
        self.colour_scheme = ["#611d91", "#a260d1", "#e4cbf5"]
        self.fig_width = 18.5
        self.fig_row_height = 4
        self.title_size = 14
        self.subtitle_size = 12
        self.ax_size = 10

    def plot_patient_audio_file(self, patient_num, wav_files):
        num_rows = math.ceil(len(wav_files)/2)
        fig, axs = plt.subplots(nrows=num_rows, ncols=2, constrained_layout = True)

        fig.suptitle('Audio recordings for patient ' + str(patient_num), fontsize=self.title_size)
        fig.set_size_inches(self.fig_width, num_rows*self.fig_row_height)

        row_count = 0
        col_count = 0 
        print(wav_files)
        for i in range(len(wav_files)):
            spf = wave.open(wav_files[i], "r")
            # Extract Raw Audio from Wav File
            signal = spf.readframes(-1)
            signal = np.frombuffer(signal, "int16")
            fs = spf.getframerate()

            # If Stereo
            if spf.getnchannels() == 2:
                print("Just mono files")
                sys.exit(0)

            time = np.linspace(0, len(signal) / fs, num=len(signal))

            if len(np.array(axs).shape) == 1:
                ax_list = axs[col_count]
            else:
                ax_list = axs[row_count, col_count]

            ax_list.set_title(wav_files[i], fontsize=self.subtitle_size)
            ax_list.plot(time, signal, color=self.colour_scheme[0])
            ax_list.grid()
            ax_list.set_ylabel("Amplitude", fontsize=self.ax_size)
            ax_list.set_xlabel("Time (Seconds)", fontsize=self.ax_size)
            ax_list.tick_params(axis='x', labelsize=self.ax_size)
            ax_list.tick_params(axis='y', labelsize=self.ax_size)
            ax_list.set_xlim(left=0, right=35)
            ax_list.set_ylim(bottom=-35000, top=35000)
            
            col_count = (col_count + 1) % 2 
            if (col_count == 0):
                row_count += 1

        if len(wav_files) % 2 == 1:
            if len(np.array(axs).shape) == 1:
                fig.delaxes(axs[-1])
            if len(np.array(axs).shape) > 1:
                fig.delaxes(axs[-1][-1])
        plt.savefig(DATA_PRESENTATION_PATH + str(patient_num) + "_audio_plots")

    def plot_patient_audio_file_with_fhs_locs(self, patient_num, wav_file, fhs_locs):
        fig, ax = plt.subplots()
        fig.suptitle('Audio recordings for patient ' + str(patient_num), fontsize=self.title_size)
        fig.set_size_inches(self.fig_width, self.fig_row_height)

        spf = wave.open(wav_file, "r")
        # Extract Raw Audio from Wav File
        signal = spf.readframes(-1)
        signal = np.frombuffer(signal, "int16")
        fs = spf.getframerate()

        # If Stereo
        if spf.getnchannels() == 2:
            print("Just mono files")
            sys.exit(0)

        time = np.linspace(0, len(signal) / fs, num=len(signal))

        ax.set_title(wav_file, fontsize=self.subtitle_size)
        ax.plot(time, signal, color=self.colour_scheme[0])
        ax.vlines(fhs_locs, color=self.colour_scheme[2], ymin=-35000, ymax=35000)
        ax.grid()
        ax.set_ylabel("Amplitude", fontsize=self.ax_size)
        ax.set_xlabel("Time (Seconds)", fontsize=self.ax_size)
        ax.tick_params(axis='x', labelsize=self.ax_size)
        ax.tick_params(axis='y', labelsize=self.ax_size)
        ax.set_xlim(left=0, right=35)
        ax.set_ylim(bottom=-35000, top=35000)
        
        plt.savefig(DATA_PRESENTATION_PATH + str(patient_num) + "_audio_plot_with_FHS")

    def plot_multi_bar_chart(self, x_labels, x_label_title, y_label_title, data, errors, bar_labels, title):
        plt.title(title, fontsize=self.title_size)
        x_ticks = np.arange(len(x_labels))
        bar_spacing = np.linspace(-0.2, 0.2, num=len(bar_labels))
        for i in range(len(bar_labels)):
            plt.bar(x_ticks+bar_spacing[i], data[i], yerr=errors[i], capsize=10, width=0.4, 
                    label=bar_labels[i], color=self.colour_scheme[i], zorder=3)


        plt.xticks(x_ticks, x_labels, fontsize=self.ax_size)
        plt.xlabel(x_label_title, fontsize=self.ax_size)
        plt.ylabel(y_label_title, fontsize=self.ax_size)
        plt.grid(zorder=0)
        plt.legend(loc='lower right')    
        plt.savefig(DATA_PRESENTATION_PATH + title.replace(" ", "_"))

    def plot_confusion_matrix(self, confusion_matrix, title, xlabel, ylabel, xticks, yticks):
        rows = len(confusion_matrix)
        cols = len(confusion_matrix[0])
        df_cm = pd.DataFrame(confusion_matrix, range(rows), range(cols))
        plt.figure(figsize = (max(rows,cols)*2.5,max(rows,cols)*2.5))
        ax= sn.heatmap(df_cm, annot=True, xticklabels=xticks, yticklabels=yticks)
        ax.set_yticklabels(labels=ax.get_yticklabels(), va='center')
        bottom, top = ax.get_ylim()
        ax.set_ylim(bottom + 0.5, top - 0.5)
        plt.title(title, fontsize=self.title_size, wrap=True)
        plt.xlabel(xlabel, fontsize=self.ax_size, labelpad=10)
        plt.ylabel(ylabel, fontsize=self.ax_size, labelpad=10)
        plt.savefig(DATA_PRESENTATION_PATH + title.replace(" ", "_"))

    def plot_boxplot(self, data_dict, title, ylabel):
        fig, ax = plt.subplots()
        ax.boxplot(data_dict.values(),
                    boxprops=dict( color="black"),
                    capprops=dict(color=self.colour_scheme[1]),
                    whiskerprops=dict(color="black"),
                    flierprops=dict(color="black", markeredgecolor=self.colour_scheme[1]),
                    medianprops=dict(color=self.colour_scheme[1]))
        ax.set_xticklabels(data_dict.keys(), fontsize=self.ax_size)
        ax.set_ylabel(ylabel, fontsize=self.ax_size)
        ax.set_title(title, fontsize=self.title_size, wrap=True)
        ax.grid()
        plt.savefig(DATA_PRESENTATION_PATH + title.replace(" ", "_"))

    def plot_model_comp_box_plots(self, cnn_accuracies, hmm_accuracies, fold_num):
        fig, ax = plt.subplots()
        ax.set_title('Distribution of the Model Accuracies in Fold ' + str(fold_num))
        ax.boxplot([cnn_accuracies, hmm_accuracies])
        ax.set_ylabel("Accuracy")
        ax.set_xlabel("Model")

        ax.set_ylim(-0.1, 1)

        ax.boxplot([cnn_accuracies, hmm_accuracies],
                        boxprops=dict( color="black"),
                        capprops=dict(color=self.colour_scheme[1]),
                        whiskerprops=dict(color="black"),
                        flierprops=dict(markeredgecolor=self.colour_scheme[1], markersize=3),
                        medianprops=dict(color=self.colour_scheme[1]))
        ax.grid()
        plt.savefig(DATA_PRESENTATION_PATH + "model_comp_accs_" + str(fold_num))

    def plot_loss_and_accuracy(self, train_loss, valid_loss, accuracy, data_pres_folder, fold_num):
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3)
        fig.set_size_inches(18, 10)
        fig.suptitle('Model Loss VS Accuracy Across Epochs', fontsize=self.title_size)
        ax1.plot(train_loss, color=self.colour_scheme[0])
        ax2.plot(valid_loss, self.colour_scheme[0])
        ax3.plot(accuracy, self.colour_scheme[1])
        ax1.set_ylabel("Training Loss")
        ax2.set_ylabel("Validation Loss")
        ax3.set_ylabel("Accuracy")
        ax1.set_xlabel("Epochs")
        ax2.set_xlabel("Epochs")
        ax3.set_xlabel("Epochs")
        ax1.grid()
        ax2.grid()
        ax3.grid()

        plt.savefig(data_pres_folder + "Loss VS Accuracy"  + str(fold_num))


