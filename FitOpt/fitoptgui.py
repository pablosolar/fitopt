# ---------------------------------------------------------------------------------
# Dialog to perform flexible fitting optimization through FitOpt algorithm.
#

import chimera
from chimera.baseDialog import ModelessDialog
import FitOpt


# ---------------------------------------------------------------------------------
# FitOpt Plugin Dialog
#
class FitOpt_Dialog(ModelessDialog):
    # Title of FitOpt plugin
    title = 'FitOpt Flexible Fitting'
    # Name of FitOpt plugin
    name = 'FitOpt'
    # Buttons of FitOpt GUI
    buttons = ('Fit', 'Results', 'Close')
    # Path of help guide of FitOpt plugin
    help = ('fitopt.html', FitOpt)
    # Name of the folder where FitOpt plugin is located
    plugin_folder = 'FitOpt/'
    # Path of the process of FitOpt
    fitopt = plugin_folder + 'fitopt'
    # Variable to keep the workspace
    cwd = None
    # Name of the fitted pdb generated after FitOpt process
    fitted_molecule = "fitopt_fitted.pdb"
    # Name of the trajectory movie
    imovie = plugin_folder + "fitopt_movie.pdb"

    # ---------------------------
    # FitOpt Chimera Commands

    # FitOpt in Chimera indicator
    fitopt_chimera_opt = "--chimera"

    # More PDBs
    fitopt_chimera_morepdbs = "--morepdbs"

    # PDB Reference
    fitopt_chimera_pdb_ref = "--pdb_ref"
    fitopt_chimera_pdb_ref_val = None

    # Trajectory (movie)
    fitopt_chimera_t = "-t"

    # Fixing diagonalization
    fitopt_chimera_r = "-r"
    fitopt_chimera_r_val = "0"

    # Rediagonalization
    fitopt_chimera_re = "--rediag"
    fitopt_chimera_re_val = "0"

    # Coarse-grained model
    fitopt_chimera_m = "-m"
    fitopt_chimera_m_val = "2"

    # Modes range
    fitopt_chimera_n = "-n"
    fitopt_chimera_n_val = "0.05"

    # Advanced commands
    fitopt_chimera_adv_commands = []

    import tkFont
    arialF = tkFont.Font(family='Arial', size=8)
    arialBondF = tkFont.Font(family='Arial', size=7, weight=tkFont.BOLD)

    # -------------------------------------------------
    # Master function for dialog contents
    #
    def fillInUI(self, parent):
        t = parent.winfo_toplevel()
        self.toplevel_widget = t
        t.withdraw()

        parent.columnconfigure(0, weight=1)
        row = 0

        import Tkinter
        from CGLtk import Hybrid
        from VolumeViewer import Volume_Menu

        ff = Tkinter.Frame(parent)
        ff.grid(row=row, column=0, sticky='w')
        row = row + 1

        # Map selection (only Volumes)
        fm = Volume_Menu(ff, 'Map: ')
        fm.frame.grid(row=0, column=0, sticky='w')
        self.map_menu = fm

        # Resolution
        rs = Hybrid.Entry(ff, 'Resolution ', 5)
        rs.frame.grid(row=0, column=1, sticky='w')
        self.resolution = rs.variable

        # Cut-off
        co = Hybrid.Entry(ff, 'Cut-off level ', 10)
        co.frame.grid(row=0, column=2, sticky='w')
        self.cutoff = co.variable

        self.save_button = Tkinter.Button(ff, text="From Volume Viewer",  font=self.arialBondF, height=1, command=self.get_cutoff)
        self.save_button.grid(row=0, column=3, sticky='w')

        hf = Tkinter.Frame(parent)
        hf.grid(row=row, column=0, sticky='w')
        row += 1

        # Space
        msg = Tkinter.Label(hf, anchor='w', justify='left')
        msg.grid(row=2, column=0, sticky='ew')
        row = row + 1
        self.message_label = msg

        # PDB's panel
        self.pdbs = Tkinter.Frame(parent)
        self.pdbs.grid(row=3, column=0, sticky='ew')
        self.pdbs.columnconfigure(1, weight=1)

        from chimera.widgets import MoleculeScrolledListBox, \
            ModelOptionMenu
        self.modelList = MoleculeScrolledListBox(self.pdbs, labelpos='nw', label_text="Target PDBs to be fitted:",
                                                 listbox_selectmode='extended', listbox_height=11)
        self.modelList.grid(row=row, column=0, sticky='nsew')
        self.pdbs.rowconfigure(row, weight=1)
        self.pdbs.columnconfigure(0, weight=1)


        self.modelList1 = MoleculeScrolledListBox(self.pdbs, labelpos='nw', label_text="Target PDBs to be fixed:",
                                                 listbox_selectmode='extended', listbox_height=11)
        self.modelList1.grid(row=row, column=1, sticky='nsew')
        self.pdbs.rowconfigure(row, weight=1)
        self.pdbs.columnconfigure(0, weight=1)
        row += 1

        # Disable Results panel at first
        self.results_button = self.buttonWidgets['Results']
        self.results_button['state'] = 'disabled'

    # ---------------------------------------------------------------------------
    # Shows a message in FitOpt Plugin
    #
    def message(self, text):

        self.message_label['text'] = text
        self.message_label.update_idletasks()

    # ---------------------------------------------------------------------------
    # Map chosen to fit into base map.
    #
    def fit_map(self):

        m = self.object_menu.getvalue()
        from VolumeViewer import Volume
        if isinstance(m, Volume):
            return m

        return None

    # ---------------------------------------------------------------------------
    # Atoms chosen in dialog for fitting.
    #
    def fit_atoms(self):

        m = self.object_menu.getvalue()
        if m == 'selected atoms':
            from chimera import selection
            atoms = selection.currentAtoms()
            return atoms

        from chimera import Molecule
        if isinstance(m, Molecule):
            return m.atoms

        return []

    # ---------------------------------------------------------------------------
    # Gets the parameter values introduced by the user
    #
    def get_options_chimera(self):

        # Model type
        if 'atom' in self.model_type.get():
            self.fitopt_chimera_m_val = "2"
        elif '3BB2R' in self.model_type.get():
            self.fitopt_chimera_m_val = "1"
        else:
            self.fitopt_chimera_m_val = "0"

        # Number of models
        if len(self.number_models.get()) > 0:
            if self.mode_percentage.get() == 1:
                mode = float(self.number_models.get()) / 100
                if mode >= 0 and mode <= 1:
                    self.fitopt_chimera_n_val = str(mode)
            else:
                self.fitopt_chimera_n_val = str(self.number_models.get())

        # Fix DoF
        if '50' in self.fixing.variable.get():
            self.fitopt_chimera_r_val = "0.5"
        elif '75' in self.fixing.variable.get():
            self.fitopt_chimera_r_val = "0.75"
        elif '90' in self.fixing.variable.get():
            self.fitopt_chimera_r_val = "0.9"

        # Rediagonalization
        if '0.1' in self.rediag.variable.get():
            self.fitopt_chimera_re_val = "0.1"
        elif '0.5' in self.rediag.variable.get():
            self.fitopt_chimera_re_val = "0.5"
        elif '1' in self.rediag.variable.get():
            self.fitopt_chimera_re_val = "0.9"

        # Advanced commands
        if len(self.adv_commands.get()) > 0:
            self.fitopt_chimera_adv_commands = self.adv_commands.get().split()

    # ---------------------------------------------------------------------------
    # Performs the FitOpt process
    #
    def Fit(self):

        from chimera.replyobj import info

        models = self.modelList.getvalue()
        models1 = self.modelList1.getvalue()
        if not models or not models1:
            info('\n')
            replyobj.error("No models chosen to save.\n")
            return
        else:
            info('\n')
            info('PDBs seleccionados a ajustar')
            for m in models:
                info('\n')
                info('    - ' + m.name)
            info('\n')
            info('\n')
            info('PDBs seleccionados a fijar')
            for m in models1:
                info('\n')
                info('    - ' + m.name)
            info('\n')
        # # If a fitting is performed when Results panel is active, close it
        # for widget in self.mmf.winfo_children():
        #     widget.destroy()
        # self.results_panel.set(False)
        #
        # # Validation of the parameters introduced by the user
        # if self.check_models() is False:
        #     return
        #
        # # Disable Fit, and Close buttons when FitOpt process is performed
        # self.disable_process_buttons()
        #
        # # Retrieve the full plugin path
        # self.plugin_path = __file__[:__file__.index(self.plugin_folder)]
        #
        # # -----------------------
        # # Calling FitOpt process
        # # -----------------------
        # from subprocess import STDOUT, PIPE, Popen
        # import os, sys
        #
        # # Get the full path of FitOpt process
        # command = self.plugin_path + self.fitopt
        # # Set the workspace
        # self.cwd = self.plugin_path + self.plugin_folder
        #
        # # PDB selected in the menu
        # pdbSelected = self.object_menu.getvalue()
        # # Map selected in the menu
        # mapSelected = self.map_menu.volume()
        #
        # # Get options values
        # self.get_options_chimera()
        #
        # # Retrieve the full command to perform the fitting: fitopt + arguments
        # cmd = [command, pdbSelected.openedAs[0], mapSelected.openedAs[0], self.resolution.get(), self.cutoff.get(),
        #        self.fitopt_chimera_m, self.fitopt_chimera_m_val,
        #        self.fitopt_chimera_t,
        #        self.fitopt_chimera_r, self.fitopt_chimera_r_val,
        #        self.fitopt_chimera_re, self.fitopt_chimera_re_val,
        #        self.fitopt_chimera_morepdbs,
        #        self.fitopt_chimera_n, self.fitopt_chimera_n_val] + self.fitopt_chimera_adv_commands
        #
        # # Execute the command with the respective arguments creating pipes between the process and Chimera
        # # Pipes will be associated to the standard output and standard error required to show the process log
        # # in the window
        # from chimera.replyobj import info
        # info('\n')
        # info('Executing the FitOpt command:')
        # info('\n')
        # info(' '.join(cmd))
        # fitopt_process = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=self.cwd, universal_newlines=True)
        #
        # # Text widget for process log that will showthe standard output of the process
        # from Tkinter import *
        # root = Tk()
        # root.wm_title("FitOpt Process Log")
        # S = Scrollbar(root)
        # T = Text(root, height=30, width=85)
        # S.pack(side=RIGHT, fill=Y)
        # T.pack(side=LEFT, fill=Y)
        # S.config(command=T.yview)
        # T.config(yscrollcommand=S.set)
        #
        # # Read first line
        # line = fitopt_process.stdout.readline()
        # # Variables to check the process status and show its output in a friendly format to the user
        # iter = False
        # model_iter = False
        # index_before_last_print = None
        # first_ite_sec = True
        #
        # # Continue reading the standard output until FitOpt is finished
        # # If the current line is an iteration for a model, replace in the widget the last showed
        # # If it is a new model or is part of the FitOpt process, inserts the line at the end of the widget
        # while line:
        #     if len(line.strip()) == 0:
        #         line = fitopt_process.stdout.readline()
        #         continue
        #     if iter is False or (iter is True and 'NMA' in line):
        #         T.insert(END, line)
        #         model_iter = True
        #     elif iter is True and 'sec' in line:
        #         if first_ite_sec is True:
        #             T.insert(END, line)
        #             model_iter = True
        #         else:
        #             T.delete(index_before_last_print + "-1c linestart", index_before_last_print)
        #             T.insert(END, line)
        #             first_ite_sec = False
        #     elif model_iter is True:
        #         index_before_last_print = T.index(END)
        #         T.insert(END, line)
        #         model_iter = False
        #     elif iter is True and 'sec' not in line:
        #         T.delete(index_before_last_print + "-1c linestart", index_before_last_print)
        #         T.insert(END, line)
        #     T.update()
        #     T.yview(END)
        #     line = fitopt_process.stdout.readline()
        #     if ('NMA_time' in line and 'Score' in line):
        #         iter = True
        #     if 'sec' in line and iter is True:
        #         first_ite_sec = True
        #         model_iter = True
        #         if index_before_last_print is not None:
        #             T.delete(index_before_last_print + "-1c linestart", index_before_last_print)
        #         index_before_last_print = T.index(END)
        #     if 'Convergence' in line:
        #         iter = False
        #
        # T.insert(END, "\n\n --> FitOpt Process has finished. Check 'Results' button to visualize solution. <--\n")
        # T.update()
        # T.yview(END)
        #
        # # When FitOpt process is finished, the results are set into the Results panel...
        # self.fill_results()
        # # and the plugin buttons are enabled again
        # self.enable_process_buttons()

    # ---------------------------------------------------------------------------
    # Fill the Results panel with the corresponding components
    #
    def fill_results(self):

        # Button to switch between the original molecule and the fitted one with FitOpt
        import Tkinter
        self.save_button = Tkinter.Button(self.mmf, text="Show fitted molecule", command=self.switch_original_fitted)
        self.save_button.grid(row=0, column=0, sticky='w')

        # Button to copy to the Model Panel the fitted molecule
        self.save_fitted = Tkinter.Button(self.mmf, text="Copy fitted molecule", command=self.save_fitted_molecule)
        self.save_fitted.grid(row=0, column=1, sticky='w')
        self.save_fitted['state'] = 'disabled'

        # Button to open the MD Movie created by iMODTFIT with the model trajectories
        self.open_md_movie = Tkinter.Button(self.mmf, text="Open movie", command=self.open_movie)
        self.open_md_movie.grid(row=1, column=0, sticky='w')

    # ---------------------------------------------------------------------------
    # Switchs between the original molecule and the fitted one with FitOpt
    #
    def switch_original_fitted(self):

        if self.save_button["text"] == "Show fitted molecule":
            # Show fitted molecule
            self.show_fitted_molecule(True)
            self.save_button["text"] = "Show original molecule"
            self.save_fitted['state'] = 'normal'
        else:
            # Show original molecule
            self.show_fitted_molecule(False)
            self.save_button["text"] = "Show fitted molecule"
            self.save_fitted['state'] = 'disabled'

    # ---------------------------------------------------------------------------
    # Reads the coordinates of the fitted molecule and updates the original
    # molecule position to show the fitting made by FitOpt
    #
    def show_fitted_molecule(self, pdb_name):

        from chimera.replyobj import info
        info('\n')
        info('Showing fitted ' + pdb_name + ' molecule')

    # ---------------------------------------------------------------------------
    # Makes a copy to the Model Panel of the fitted molecule
    #
    def save_fitted_molecule(self):

        # Get opened molecule (the one selected in the menu)
        m = self.object_menu.getvalue()

        # Make copy using the copy_molecule native functionality from Chimera
        from Molecule import copy_molecule
        mc = copy_molecule(m)

        # Set copy name
        mc.name = m.name.split('.')[0] + '_fitopt.pdb'

        # Add copy to list of open models
        chimera.openModels.add([mc])

    # ---------------------------------------------------------------------------
    # Opens the MD movie created by iMODTFIT with the model trajectories
    #
    def open_movie(self):

        # Import the native dialog MovieDialog from Chimera
        from Movie.gui import MovieDialog
        # import the loadEnsemble native functionality from Chimera to load the movie
        from Trajectory.formats.Pdb import loadEnsemble

        # Load the movie created by FitOpt
        movie = self.plugin_path + self.imovie
        loadEnsemble(("single", movie), None, None, MovieDialog)

    # ---------------------------------------------------------------------------
    # Disables the the FitOpt GUI Fit, Close and Results buttons
    #
    def disable_process_buttons(self):

        self.fit_button = self.buttonWidgets['Fit']
        self.fit_button['state'] = 'disabled'
        self.options_button['state'] = 'disabled'
        self.close_ch_button = self.buttonWidgets['Close']
        self.close_ch_button['state'] = 'disabled'
        self.results_button['state'] = 'disabled'

    # ---------------------------------------------------------------------------
    # Enables the the FitOpt GUI Fit, Close and Results buttons
    #
    def enable_process_buttons(self):

        self.fit_button = self.buttonWidgets['Fit']
        self.fit_button['state'] = 'normal'
        self.options_button['state'] = 'normal'
        self.close_ch_button = self.buttonWidgets['Close']
        self.close_ch_button['state'] = 'normal'
        self.results_button['state'] = 'normal'

    # ---------------------------------------------------------------------------
    #  Results button is pressed
    #
    def Results(self):
        self.results_panel.set(not self.results_panel.get())

    # -----------------------------------------------------------------------------
    # Gets the cut-off level value from the Volume Viewer dialog
    # Useful when the user does not know an appropiate resolution and plays
    # with the map density in this dialog.
    #
    def get_cutoff(self):

        # validate if the map is loaded/choosed
        bmap = self.map_menu.data_region()
        if bmap is None:
            self.message('Choose map.')
            return

        # Import the native dialog Volume Viewer from Chimera
        from chimera import dialogs
        vdlg = dialogs.find("volume viewer")

        # Get the cut-off level from the Volume Viewer dialog
        cutoff_panel = vdlg.thresholds_panel.threshold.get()

        # Set the cut-off value in FitOpt with the previous value
        self.cutoff.set(cutoff_panel)
        self.message("")

    # -----------------------------------------------------------------------------
    # Validates the values of the parameteres introduced by the users.
    # Moreover, check if molecule and maps are loaded
    #
    def check_models(self):

        fatoms = self.fit_atoms()
        fmap = self.fit_map()
        bmap = self.map_menu.data_region()
        if (len(fatoms) == 0 and fmap is None) or bmap is None:
            self.message('Choose model and map.')
            return False
        if fmap == bmap:
            self.message('Chosen maps are the same.')
            return False
        if len(self.cutoff.get()) == 0:
            self.message('Cutoff must be defined.')
            return False
        if len(self.resolution.get()) == 0:
            self.message('Resolution must be defined.')
            return False
        if float(self.resolution.get()) < 0 or float(self.resolution.get()) >= 60:
            self.message('Resolution must be less than 100.')
            return False
        self.message("")
        return True

    # ----------------------------------------------
    # Validates if a string represents an integer
    #
    def representsInt(self, number):

        try:
            int(number)
            return True
        except ValueError:
            return False

    # ----------------------------------------------
    # Validates if a string represents an integer
    #
    def representsFloat(self, number):

        try:
            float(number)
            return True
        except ValueError:
            return False


# -----------------------------------------------------------------------------
# Returns a list of molecules from the models opened in Chimera
# to be selectables for the fitting
#
def fit_object_models():
    from chimera import openModels as om, Molecule
    mlist = om.list(modelTypes=[Molecule])
    folist = ['selected atoms'] + mlist
    return folist


# -----------------------------------------------------------------------------
# Puts 'selected atoms' first, then all molecules, then all volumes.
#
def compare_fit_objects(a, b):
    if a == 'selected atoms':
        return -1
    if b == 'selected atoms':
        return 1
    from VolumeViewer import Volume
    from chimera import Molecule
    if isinstance(a, Molecule) and isinstance(b, Volume):
        return -1
    if isinstance(a, Volume) and isinstance(b, Molecule):
        return 1
    return cmp((a.id, a.subid), (b.id, b.subid))


# -----------------------------------------------------------------------------
# Shows the FitOpt Dialog in Chimera when it is registered
#
def show_fitopt_dialog():
    from chimera import dialogs
    return dialogs.display(FitOpt_Dialog.name)


# -----------------------------------------------------------------------------
# Registers the FitOpt Dialog in Chimera
#
from chimera import dialogs

dialogs.register(FitOpt_Dialog.name, FitOpt_Dialog, replace=True)
