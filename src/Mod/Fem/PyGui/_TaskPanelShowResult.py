# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__title__ = "Result Control Task Panel"
__author__ = "Juergen Riegel, Michael Hindley"
__url__ = "http://www.freecadweb.org"

## @package TaskPanelShowResult
#  \ingroup FEM

import FreeCAD
import numpy as np

import FreeCADGui
import FemGui
from PySide import QtCore, QtGui
from PySide.QtCore import Qt
from PySide.QtGui import QApplication


class _TaskPanelShowResult:
    '''The task panel for the post-processing'''
    def __init__(self, obj):
        self.result_obj = obj
        self.mesh_obj = self.result_obj.Mesh
        # task panel should be started by use of setEdit of view provider
        # in view provider checks: Mesh, active analysis and if Mesh and result are in active analysis

        self.form = FreeCADGui.PySideUic.loadUi(FreeCAD.getHomePath() + "Mod/Fem/PyGui/TaskPanelShowResult.ui")
        self.fem_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/General")
        self.restore_result_settings_in_dialog = self.fem_prefs.GetBool("RestoreResultDialog", True)

        # Connect Signals and Slots
        # result type radio buttons
        QtCore.QObject.connect(self.form.rb_none, QtCore.SIGNAL("toggled(bool)"), self.none_selected)
        QtCore.QObject.connect(self.form.rb_abs_displacement, QtCore.SIGNAL("toggled(bool)"), self.abs_displacement_selected)
        QtCore.QObject.connect(self.form.rb_x_displacement, QtCore.SIGNAL("toggled(bool)"), self.x_displacement_selected)
        QtCore.QObject.connect(self.form.rb_y_displacement, QtCore.SIGNAL("toggled(bool)"), self.y_displacement_selected)
        QtCore.QObject.connect(self.form.rb_z_displacement, QtCore.SIGNAL("toggled(bool)"), self.z_displacement_selected)
        QtCore.QObject.connect(self.form.rb_temperature, QtCore.SIGNAL("toggled(bool)"), self.temperature_selected)
        QtCore.QObject.connect(self.form.rb_vm_stress, QtCore.SIGNAL("toggled(bool)"), self.vm_stress_selected)
        QtCore.QObject.connect(self.form.rb_maxprin, QtCore.SIGNAL("toggled(bool)"), self.max_prin_selected)
        QtCore.QObject.connect(self.form.rb_minprin, QtCore.SIGNAL("toggled(bool)"), self.min_prin_selected)
        QtCore.QObject.connect(self.form.rb_max_shear_stress, QtCore.SIGNAL("toggled(bool)"), self.max_shear_selected)

        # displacement
        QtCore.QObject.connect(self.form.cb_show_displacement, QtCore.SIGNAL("clicked(bool)"), self.show_displacement)
        QtCore.QObject.connect(self.form.hsb_displacement_factor, QtCore.SIGNAL("valueChanged(int)"), self.hsb_disp_factor_changed)
        QtCore.QObject.connect(self.form.sb_displacement_factor, QtCore.SIGNAL("valueChanged(int)"), self.sb_disp_factor_changed)
        QtCore.QObject.connect(self.form.sb_displacement_factor_max, QtCore.SIGNAL("valueChanged(int)"), self.sb_disp_factor_max_changed)

        # user defined equation
        QtCore.QObject.connect(self.form.user_def_eq, QtCore.SIGNAL("textchanged()"), self.user_defined_text)
        QtCore.QObject.connect(self.form.calculate, QtCore.SIGNAL("clicked()"), self.calculate)

        self.update()
        if self.restore_result_settings_in_dialog:
            self.restore_result_dialog()
        else:
            self.restore_initial_result_dialog()

    def restore_result_dialog(self):
        try:
            rt = FreeCAD.FEM_dialog["results_type"]
            if rt == "None":
                self.form.rb_none.setChecked(True)
                self.none_selected(True)
            elif rt == "Uabs":
                self.form.rb_abs_displacement.setChecked(True)
                self.abs_displacement_selected(True)
            elif rt == "U1":
                self.form.rb_x_displacement.setChecked(True)
                self.x_displacement_selected(True)
            elif rt == "U2":
                self.form.rb_y_displacement.setChecked(True)
                self.y_displacement_selected(True)
            elif rt == "U3":
                self.form.rb_z_displacement.setChecked(True)
                self.z_displacement_selected(True)
            elif rt == "Temp":
                self.form.rb_temperature.setChecked(True)
                self.temperature_selected(True)
            elif rt == "Sabs":
                self.form.rb_vm_stress.setChecked(True)
                self.vm_stress_selected(True)
            elif rt == "MaxPrin":
                self.form.rb_maxprin.setChecked(True)
                self.max_prin_selected(True)
            elif rt == "MinPrin":
                self.form.rb_minprin.setChecked(True)
                self.min_prin_selected(True)
            elif rt == "MaxShear":
                self.form.rb_max_shear_stress.setChecked(True)
                self.max_shear_selected(True)

            sd = FreeCAD.FEM_dialog["show_disp"]
            self.form.cb_show_displacement.setChecked(sd)
            self.show_displacement(sd)

            df = FreeCAD.FEM_dialog["disp_factor"]
            dfm = FreeCAD.FEM_dialog["disp_factor_max"]
            self.form.hsb_displacement_factor.setMaximum(dfm)
            self.form.hsb_displacement_factor.setValue(df)
            self.form.sb_displacement_factor_max.setValue(dfm)
            self.form.sb_displacement_factor.setValue(df)
        except:
            self.restore_initial_result_dialog()

    def restore_initial_result_dialog(self):
        FreeCAD.FEM_dialog = {"results_type": "None", "show_disp": False,
                              "disp_factor": 0, "disp_factor_max": 100}
        self.reset_mesh_deformation()
        self.reset_mesh_color()

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)

    def get_result_stats(self, type_name, analysis=None):
        if "Stats" in self.result_obj.PropertiesList:
                Stats = self.result_obj.Stats
                match_table = {"U1": (Stats[0], Stats[1], Stats[2]),
                               "U2": (Stats[3], Stats[4], Stats[5]),
                               "U3": (Stats[6], Stats[7], Stats[8]),
                               "Uabs": (Stats[9], Stats[10], Stats[11]),
                               "Sabs": (Stats[12], Stats[13], Stats[14]),
                               "MaxPrin": (Stats[15], Stats[16], Stats[17]),
                               "MidPrin": (Stats[18], Stats[19], Stats[20]),
                               "MinPrin": (Stats[21], Stats[22], Stats[23]),
                               "MaxShear": (Stats[24], Stats[25], Stats[26]),
                               "None": (0.0, 0.0, 0.0)}
                return match_table[type_name]
        return (0.0, 0.0, 0.0)

    def none_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "None"
        self.set_result_stats("mm", 0.0, 0.0, 0.0)
        self.reset_mesh_color()

    def abs_displacement_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "Uabs"
        self.select_displacement_type("Uabs")

    def x_displacement_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "U1"
        self.select_displacement_type("U1")

    def y_displacement_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "U2"
        self.select_displacement_type("U2")

    def z_displacement_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "U3"
        self.select_displacement_type("U3")

    def vm_stress_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "Sabs"
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.suitable_results:
            self.mesh_obj.ViewObject.setNodeColorByScalars(self.result_obj.NodeNumbers, self.result_obj.StressValues)
        (minm, avg, maxm) = self.get_result_stats("Sabs")
        self.set_result_stats("MPa", minm, avg, maxm)
        QtGui.qApp.restoreOverrideCursor()

    def max_shear_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "MaxShear"
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.suitable_results:
            self.mesh_obj.ViewObject.setNodeColorByScalars(self.result_obj.NodeNumbers, self.result_obj.MaxShear)
        (minm, avg, maxm) = self.get_result_stats("MaxShear")
        self.set_result_stats("MPa", minm, avg, maxm)
        QtGui.qApp.restoreOverrideCursor()

    def max_prin_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "MaxPrin"
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.suitable_results:
            self.mesh_obj.ViewObject.setNodeColorByScalars(self.result_obj.NodeNumbers, self.result_obj.PrincipalMax)
        (minm, avg, maxm) = self.get_result_stats("MaxPrin")
        self.set_result_stats("MPa", minm, avg, maxm)
        QtGui.qApp.restoreOverrideCursor()

    def temperature_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "Temp"
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.suitable_results:
            self.mesh_obj.ViewObject.setNodeColorByScalars(self.result_obj.NodeNumbers, self.result_obj.Temperature)
        minm = min(self.result_obj.Temperature)
        avg = sum(self.result_obj.Temperature) / len(self.result_obj.Temperature)
        maxm = max(self.result_obj.Temperature)
        self.set_result_stats("K", minm, avg, maxm)
        QtGui.qApp.restoreOverrideCursor()

    def min_prin_selected(self, state):
        FreeCAD.FEM_dialog["results_type"] = "MinPrin"
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.suitable_results:
            self.mesh_obj.ViewObject.setNodeColorByScalars(self.result_obj.NodeNumbers, self.result_obj.PrincipalMin)
        (minm, avg, maxm) = self.get_result_stats("MinPrin")
        self.set_result_stats("MPa", minm, avg, maxm)
        QtGui.qApp.restoreOverrideCursor()

    def user_defined_text(self, equation):
        FreeCAD.FEM_dialog["results_type"] = "user"
        self.form.user_def_eq.toPlainText()

    def calculate(self):
        FreeCAD.FEM_dialog["results_type"] = "None"
        self.update()
        self.restore_result_dialog()
        # Convert existing values to numpy array
        P1 = np.array(self.result_obj.PrincipalMax)
        P2 = np.array(self.result_obj.PrincipalMed)
        P3 = np.array(self.result_obj.PrincipalMin)
        Von = np.array(self.result_obj.StressValues)
        T = np.array(self.result_obj.Temperature)
        dispvectors = np.array(self.result_obj.DisplacementVectors)
        x = np.array(dispvectors[:, 0])
        y = np.array(dispvectors[:, 1])
        z = np.array(dispvectors[:, 2])
        stressvectors = np.array(self.result_obj.StressVectors)
        sx = np.array(stressvectors[:, 0])
        sy = np.array(stressvectors[:, 1])
        sz = np.array(stressvectors[:, 2])
        strainvectors = np.array(self.result_obj.StrainVectors)
        ex = np.array(strainvectors[:, 0])
        ey = np.array(strainvectors[:, 1])
        ez = np.array(strainvectors[:, 2])
        userdefined_eq = self.form.user_def_eq.toPlainText()  # Get equation to be used
        UserDefinedFormula = eval(userdefined_eq).tolist()
        self.result_obj.UserDefined = UserDefinedFormula
        minm = min(UserDefinedFormula)
        avg = sum(UserDefinedFormula) / len(UserDefinedFormula)
        maxm = max(UserDefinedFormula)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.suitable_results:
            self.mesh_obj.ViewObject.setNodeColorByScalars(self.result_obj.NodeNumbers, UserDefinedFormula)
        self.set_result_stats("", minm, avg, maxm)
        QtGui.qApp.restoreOverrideCursor()
        del x, y, z, T, Von, P1, P2, P3, sx, sy, sz, ex, ey, ez  # Dummy use to get around flake8, varibles not being used

    def select_displacement_type(self, disp_type):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if disp_type == "Uabs":
            if self.suitable_results:
                self.mesh_obj.ViewObject.setNodeColorByScalars(self.result_obj.NodeNumbers, self.result_obj.DisplacementLengths)
        else:
            match = {"U1": 0, "U2": 1, "U3": 2}
            d = zip(*self.result_obj.DisplacementVectors)
            displacements = list(d[match[disp_type]])
            if self.suitable_results:
                self.mesh_obj.ViewObject.setNodeColorByScalars(self.result_obj.NodeNumbers, displacements)
        (minm, avg, maxm) = self.get_result_stats(disp_type)
        self.set_result_stats("mm", minm, avg, maxm)
        QtGui.qApp.restoreOverrideCursor()

    def set_result_stats(self, unit, minm, avg, maxm):
        self.form.le_min.setProperty("unit", unit)
        self.form.le_min.setText("{:.6} {}".format(minm, unit))
        self.form.le_avg.setProperty("unit", unit)
        self.form.le_avg.setText("{:.6} {}".format(avg, unit))
        self.form.le_max.setProperty("unit", unit)
        self.form.le_max.setText("{:.6} {}".format(maxm, unit))

    def update_displacement(self, factor=None):
        if factor is None:
            if FreeCAD.FEM_dialog["show_disp"]:
                factor = self.form.hsb_displacement_factor.value()
            else:
                factor = 0.0
        self.mesh_obj.ViewObject.applyDisplacement(factor)

    def show_displacement(self, checked):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        FreeCAD.FEM_dialog["show_disp"] = checked
        if "result_obj" in FreeCAD.FEM_dialog:
            if FreeCAD.FEM_dialog["result_obj"] != self.result_obj:
                self.update_displacement()
        FreeCAD.FEM_dialog["result_obj"] = self.result_obj
        if self.suitable_results:
            self.mesh_obj.ViewObject.setNodeDisplacementByVectors(self.result_obj.NodeNumbers, self.result_obj.DisplacementVectors)
        self.update_displacement()
        QtGui.qApp.restoreOverrideCursor()

    def hsb_disp_factor_changed(self, value):
        self.form.sb_displacement_factor.setValue(value)
        self.update_displacement()

    def sb_disp_factor_max_changed(self, value):
        FreeCAD.FEM_dialog["disp_factor_max"] = value
        self.form.hsb_displacement_factor.setMaximum(value)

    def sb_disp_factor_changed(self, value):
        FreeCAD.FEM_dialog["disp_factor"] = value
        self.form.hsb_displacement_factor.setValue(value)

    def disable_empty_result_buttons(self):
        ''' disable radio buttons if result does not exists in result object'''
        '''assignments
        DisplacementLengths --> rb_abs_displacement
        DisplacementVectors --> rb_x_displacement, rb_y_displacement, rb_z_displacement
        Temperature         --> rb_temperature
        StressValues        --> rb_vm_stress
        PrincipalMax        --> rb_maxprin
        PrincipalMin        --> rb_minprin
        MaxShear            --> rb_max_shear_stress'''
        if len(self.result_obj.DisplacementLengths) == 0:
            self.form.rb_abs_displacement.setEnabled(0)
        if len(self.result_obj.DisplacementVectors) == 0:
            self.form.rb_x_displacement.setEnabled(0)
            self.form.rb_y_displacement.setEnabled(0)
            self.form.rb_z_displacement.setEnabled(0)
        if len(self.result_obj.Temperature) == 0:
            self.form.rb_temperature.setEnabled(0)
        if len(self.result_obj.StressValues) == 0:
            self.form.rb_vm_stress.setEnabled(0)
        if len(self.result_obj.PrincipalMax) == 0:
            self.form.rb_maxprin.setEnabled(0)
        if len(self.result_obj.PrincipalMin) == 0:
            self.form.rb_minprin.setEnabled(0)
        if len(self.result_obj.MaxShear) == 0:
            self.form.rb_max_shear_stress.setEnabled(0)

    def update(self):
        self.suitable_results = False
        if (self.mesh_obj.FemMesh.NodeCount == len(self.result_obj.NodeNumbers)):
            self.suitable_results = True
            self.disable_empty_result_buttons()
            self.mesh_obj.ViewObject.Visibility = True
            hide_parts_constraints()
        else:
            if not self.mesh_obj.FemMesh.VolumeCount:
                error_message = 'FEM: Graphical bending stress output for beam or shell FEM Meshes not yet supported.\n'
                FreeCAD.Console.PrintError(error_message)
                QtGui.QMessageBox.critical(None, 'No result object', error_message)
            else:
                error_message = 'FEM: Result node numbers are not equal to FEM Mesh NodeCount.\n'
                FreeCAD.Console.PrintError(error_message)
                QtGui.QMessageBox.critical(None, 'No result object', error_message)

    def reset_mesh_deformation(self):
        self.mesh_obj.ViewObject.applyDisplacement(0.0)

    def reset_mesh_color(self):
        self.mesh_obj.ViewObject.NodeColor = {}
        self.mesh_obj.ViewObject.ElementColor = {}
        self.mesh_obj.ViewObject.setNodeColorByScalars()

    def reject(self):
        FreeCADGui.Control.closeDialog()  # if the taks panell is called from Command obj is not in edit mode thus reset edit does not cleses the dialog, may be do not call but set in edit instead
        FreeCADGui.ActiveDocument.resetEdit()


# helper
def hide_parts_constraints():
    fem_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/General")
    hide_constraints = fem_prefs.GetBool("HideConstraint", False)
    if hide_constraints:
        for acnstrmesh in FemGui.getActiveAnalysis().Member:
            if "Constraint" in acnstrmesh.TypeId:
                acnstrmesh.ViewObject.Visibility = False
            if "Mesh" in acnstrmesh.TypeId:
                aparttoshow = acnstrmesh.Name.replace("_Mesh", "")
                for apart in FreeCAD.activeDocument().Objects:
                    if aparttoshow == apart.Name:
                        apart.ViewObject.Visibility = False
