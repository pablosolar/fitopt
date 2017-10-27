# -----------------------------------------------------------------------------
# Class to register the FitOpt plugin in Chimera.
# The plugin will be located in EM Fitting/Volume Data menu
#
import chimera.extension

# -----------------------------------------------------------------------------
#
class FitOpt_EMO(chimera.extension.EMO):

    def name(self):
        return 'FitOpt'
    def description(self):
        return 'Multi-fitting optimization based in ADP Method'
    def categories(self):
        return ['EM Fitting']
    def icon(self):
        return None
    def activate(self):
        self.module('fitoptgui').show_fitopt_dialog()
        return None

chimera.extension.manager.registerExtension(FitOpt_EMO(__file__))
