import matplotlib.pyplot as plt
import seaborn as sns

class CapabilityPlotter:
    def __init__(self, data, lsl=None, usl=None):
        self.data = data
        self.lsl = lsl
        self.usl = usl

    def plot_histogram(self):
        sns.histplot(self.data, kde=True)
        if self.lsl: plt.axvline(self.lsl, color='red', linestyle='--')
        if self.usl: plt.axvline(self.usl, color='green', linestyle='--')
        plt.title("Histograma amb LSL/USL")
        plt.xlabel("Mesura")
        plt.ylabel("Freqüència")
        plt.show()
