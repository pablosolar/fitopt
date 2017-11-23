# ---------------------------------------------------------------------------------
# Dialog to perform flexible fitting optimization through FitOpt algorithm.
# ---------------------------------------------------------------------------------

import chimera
from chimera.baseDialog import ModelessDialog
import FitOpt

# ---------------------------------------------------------------------------------
# FitOpt Plugin Dialog
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
	# Array to store the solutions generated by FitOpt
	solutions_chimera = []

    # FitOpt Commands: Chimera.bin indicator
    fitopt_chimera_opt = "-C"
	
    # FitOpt Commands: Fix PDBs
    fitopt_chimera_fix = "--fixing"
	is_fixed = False
	
	# Fonts styles
    import tkFont
    arial_f = tkFont.Font(family='Arial', size=8)
    arial_bond_f = tkFont.Font(family='Arial', size=7, weight=tkFont.BOLD)

	
    # -------------------------------------------------
    # Master function for dialog contents
    def fillInUI(self, parent):
	
		# Basic widget configuration
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
		
		# Retrieve cut-off from volume viewer
        self.save_button = Tkinter.Button(ff, text="From Volume Viewer",  font=self.arial_bond_f, height=1, command=self.get_cutoff)
        self.save_button.grid(row=0, column=3, sticky='w')
		
		# Space
        hf = Tkinter.Frame(parent)
        hf.grid(row=row, column=0, sticky='w')
        row += 1
        msg = Tkinter.Label(hf, anchor='w', justify='left')
        msg.grid(row=2, column=0, sticky='ew')
        row = row + 1
        self.message_label = msg

        # Frame for PDBs
        self.pdbs = Tkinter.Frame(parent)
        self.pdbs.grid(row=3, column=0, sticky='ew')
        self.pdbs.columnconfigure(1, weight=1)
	
		# Target PDBs to be fitted scrolled panel
        from chimera.widgets import MoleculeScrolledListBox, ModelOptionMenu
        self.fitting_list = MoleculeScrolledListBox(self.pdbs, labelpos='nw', label_text="Target PDBs to be fitted:",
                                                 listbox_selectmode='extended', listbox_height=11)
        self.fitting_list.grid(row=row, column=0, sticky='nsew')
        #self.pdbs.rowconfigure(row, weight=1)
        #self.pdbs.columnconfigure(0, weight=1)

		# Target PDBs to be fixed scrolled panel
        self.fixing_list = MoleculeScrolledListBox(self.pdbs, labelpos='nw', label_text="Target PDBs to be fixed (optional):",
                                                 listbox_selectmode='extended', listbox_height=11)
        self.fixing_list.grid(row=row, column=1, sticky='nsew')
        #self.pdbs.rowconfigure(row, weight=1)
        #self.pdbs.columnconfigure(0, weight=1)
        row += 1

        # Disable Results panel at first
        self.results_button = self.buttonWidgets['Results']
        self.results_button['state'] = 'disabled'

		
    # ---------------------------------------------------------------------------
    # Shows a message in FitOpt Plugin
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
    # Performs the FitOpt process
    def Fit(self):

        # If a fitting is performed when Results panel is active, close it
        for widget in self.mmf.winfo_children():
			widget.destroy()
			# and clean the array which store the solutions (previous fitting)
			self.solutions_chimera = []
        self.results_panel.set(False)
        
        # Validations
        if self.check_models() is False:
			return

        # Disable Fit, and Close buttons when FitOpt process is performed
        self.disable_process_buttons()
        
        # Retrieve the full plugin path
        self.plugin_path = __file__[:__file__.index(self.plugin_folder)]
		# Get the full path of FitOpt process
        command = self.plugin_path + self.fitopt
        # Set the workspace
        self.cwd = self.plugin_path + self.plugin_folder
		
		# Complete list of target PDBs to be fitted
        full_fitted_pdbs = self.get_full_fitted_pdbs()
		# Complete list of target PDBs to be fixed
        full_fixed_pdbs = self.get_full_fixed_pdbs()
        # Map selected in the menu
        map_selected = self.map_menu.volume()
		
        # #-#-#-#-#-#-#-#-#-#-# #
        # Calling FitOpt process
        # #-#-#-#-#-#-#-#-#-#-# #
		
		from subprocess import STDOUT, PIPE, Popen
        import os, sys

        # Retrieve the full command to perform the fitting: fitopt + arguments
        cmd = [command, mapSelected.openedAs[0], self.cutoff.get(), self.resolution.get(), full_fitted_pdbs, self.fitopt_chimera_opt]
		
		# Check if there are target pdbs to be fixed and append them to the command
		if self.is_fixed:
			fixing_option = [self.fitopt_chimera_fix, full_fixed_pdbs]
			cmd.extend(fixing_option)
			# cmd.insert(4, cmd.pop(cmd.index(fixing_option[0])))
			# cmd.insert(5, cmd.pop(cmd.index(fixing_option[1])))
        
        # Execute the command with the respective arguments creating pipes between the process and Chimera
        # Pipes will be associated to the standard output and standard error required to show the process log
        # in the window
        from chimera.replyobj import info
        info('\n')
        info('Executing the FitOpt command:')
        info('\n')
        info(' '.join(cmd))
        #fitopt_process = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=self.cwd, universal_newlines=True)
        
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
        # T.insert(END, "\n\n --&gt; FitOpt Process has finished. Check 'Results' button to visualize solution. &lt;--\n")
        # T.update()
        # T.yview(END)
        #
        # # When FitOpt process is finished, the results are set into the Results panel...
        # self.fill_results()
        # # and the plugin buttons are enabled again
        # self.enable_process_buttons()
		
    
	# -----------------------------------------------------------------------------
    # Validates the values of the parameteres introduced by the users.
    # Moreover, check if molecule and maps are loaded
    #
    def check_models(self):

        fatoms = self.fit_atoms()
        fmap = self.fit_map()
        bmap = self.map_menu.data_region()
		
		# Retrieve selected PDBs to fit
		self.fit_pdbs = self.fitting_list.getvalue()	
		# Retrieve selected PDBs to fix
		self.fix_pdbs = self.fixing_list.getvalue()
		
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
        if float(self.resolution.get()) &lt; 0 or float(self.resolution.get()) &gt;= 60:
            self.message('Resolution must be less than 100.')
            return False
		if not self.fit_pdbs:
			self.message('Target PDBs to be fitted are required.')
            return False
		if self.fix_pdbs:
			self.is_fixed = True
        self.message("")
        return True
	

	# ---------------------------------------------------------------------------
    # Returns a list of the target pdbs to be fitted with the full path
    def get_full_fitted_pdbs(self):

        full_fitted_pdbs = []
		for pdb in self.fit_pdbs:
			full_fitted_pdbs.append(pdb.openedAs[0])
		return ' '.join(full_fitted_pdbs)

		
	# ---------------------------------------------------------------------------
    # Returns a string of the target pdbs to be fixed with the full path
    def get_full_fixed_pdbs(self):

        full_fixed_pdbs = []
		if self.is_fixed:
			for pdb in self.fix_pdbs:
				full_fixed_pdbs.append(pdb.openedAs[0])
		
		return ','.join(full_fixed_pdbs)
		
	
	
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
		
		# Reading solutions for the first time and allocate them in memory
		if len(self.solutions_chimera) == 0:
			self.read_solutions_chimera()

			
	# ---------------------------------------------------------------------------
	# Reads all the solutions parameters from the file that will be generated
	# by FitOpt, chimera.bin (center of mass, Euler Angles and traslations)
	#
	def read_solutions_chimera(self):

		import struct
		import os
		# Get the file size
		f = open(self.filename_chimera, "rb")
		size = self.get_size_chimera_bin(f)
		n = (size / 4) - 3;

		# PDB Center of mass
		self.com = struct.unpack('f' * 3, f.read(4 * 3))
		# Data: Traslation(xyz), 3 Ruler Angles (ZXZ convention)
		num = struct.unpack('f' * n, f.read(4 * n))

		solution = []
		for x in range(0, n):
		  if x % 6 == 0 and x > 0 and len(solution) > 0:
			self.solutions_chimera.append(solution)
			solution = []
		  data = "{:10.6f}".format(num[x])
		  solution.append(data.strip())

		# Store all the solutions data intro the main array
		self.solutions_chimera.append(solution)

		# Remove the temporal chimera.bin file generated
		# os.remove(self.filename_chimera)
			

	# ---------------------------------------------------------------------------
	# Gets the size of the file that will be generated by ADP EM
	# with all the solutions parameters (chimera.bin)
	#
	def get_size_chimera_bin(self, fileobject):

		# Move the cursor to the end of the file
		fileobject.seek(0, 2)
		size = fileobject.tell()
		# Move the cursor back to the begin of the file
		fileobject.seek(0, 0)
		return size

			
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