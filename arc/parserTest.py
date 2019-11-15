#!/usr/bin/env python3
# encoding: utf-8

"""
This module contains unit tests for the parser functions
"""

import numpy as np
import os
import unittest

import arc.parser as parser
from arc.settings import arc_path
from arc.species import ARCSpecies
from arc.species.converter import xyz_to_str


class TestParser(unittest.TestCase):
    """
    Contains unit tests for the parser functions
    """
    @classmethod
    def setUpClass(cls):
        """
        A method that is run before all unit tests in this class.
        """
        cls.maxDiff = None

    def test_parse_frequencies(self):
        """Test frequency parsing"""
        no3_path = os.path.join(arc_path, 'arc', 'testing', 'NO3_freq_QChem_fails_on_cclib.out')
        c2h6_path = os.path.join(arc_path, 'arc', 'testing', 'C2H6_freq_QChem.out')
        so2oo_path = os.path.join(arc_path, 'arc', 'testing', 'SO2OO_CBS-QB3.log')
        ch2o_path = os.path.join(arc_path, 'arc', 'testing', 'CH2O_freq_molpro.out')
        orca_path = os.path.join(arc_path, 'arc', 'testing', 'orca_example_freq.log')
        no3_freqs = parser.parse_frequencies(path=no3_path, software='QChem')
        c2h6_freqs = parser.parse_frequencies(path=c2h6_path, software='QChem')
        so2oo_freqs = parser.parse_frequencies(path=so2oo_path, software='Gaussian')
        ch2o_freqs = parser.parse_frequencies(path=ch2o_path, software='Molpro')
        orca_freqs = parser.parse_frequencies(path=orca_path, software='orca')
        self.assertTrue(np.array_equal(orca_freqs,
                                       np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1151.03, 1250.19, 1526.12, 1846.4,
                                                 3010.49, 3070.82], np.float64)))
        self.assertTrue(np.array_equal(no3_freqs,
                                       np.array([-390.08, -389.96, 822.75, 1113.23, 1115.24, 1195.35], np.float64)))
        self.assertTrue(np.array_equal(c2h6_freqs,
                                       np.array([352.37, 847.01, 861.68, 1023.23, 1232.66, 1235.04, 1425.48, 1455.31,
                                                 1513.67, 1518.02, 1526.18, 1526.56, 3049.78, 3053.32, 3111.61, 3114.2,
                                                 3134.14, 3136.8], np.float64)))
        self.assertTrue(np.array_equal(so2oo_freqs,
                                       np.array([302.51, 468.1488, 469.024, 484.198, 641.0067, 658.6316,
                                                 902.2888, 1236.9268, 1419.0826], np.float64)))
        self.assertTrue(np.array_equal(ch2o_freqs,
                                       np.array([1181.01, 1261.34, 1529.25, 1764.47, 2932.15, 3000.10], np.float64)))

    def test_parse_xyz_from_file(self):
        """Test parsing xyz from a file"""
        path1 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'CH3C(O)O.gjf')
        path2 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'CH3C(O)O.xyz')
        path3 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'AIBN.gjf')
        path4 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'molpro.in')
        path5 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'qchem.in')
        path6 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'qchem_output.out')
        path7 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'TS.gjf')
        path8 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'optim_traj_terachem.xyz')
        path9 = os.path.join(arc_path, 'arc', 'testing', 'orca_example_opt.log')

        xyz1 = parser.parse_xyz_from_file(path1)
        xyz2 = parser.parse_xyz_from_file(path2)
        xyz3 = parser.parse_xyz_from_file(path3)
        xyz4 = parser.parse_xyz_from_file(path4)
        xyz5 = parser.parse_xyz_from_file(path5)
        xyz6 = parser.parse_xyz_from_file(path6)
        xyz7 = parser.parse_xyz_from_file(path7)
        xyz8 = parser.parse_xyz_from_file(path8)
        xyz9 = parser.parse_xyz_from_file(path9)

        self.assertEqual(xyz1, xyz2)
        xyz1_str = xyz_to_str(xyz1)
        xyz2_str = xyz_to_str(xyz2)
        xyz3_str = xyz_to_str(xyz3)
        xyz4_str = xyz_to_str(xyz4)
        xyz5_str = xyz_to_str(xyz5)
        xyz6_str = xyz_to_str(xyz6)
        xyz8_str = xyz_to_str(xyz8)
        xyz9_str = xyz_to_str(xyz9)
        self.assertTrue('C       1.40511900    0.21728200    0.07675200' in xyz1_str)
        self.assertTrue('O      -0.79314200    1.04818800    0.18134200' in xyz1_str)
        self.assertTrue('H      -0.43701200   -1.34990600    0.92900600' in xyz2_str)
        self.assertTrue('C       2.12217963   -0.66843078    1.04808732' in xyz3_str)
        self.assertTrue('N       2.41731872   -1.07916417    2.08039935' in xyz3_str)
        spc3 = ARCSpecies(label='AIBN', xyz=xyz3)
        self.assertEqual(len(spc3.mol.atoms), 24)
        self.assertTrue('S      -0.42046822   -0.39099498    0.02453521' in xyz4_str)
        self.assertTrue('N      -1.99742564    0.38106573    0.09139807' in xyz5_str)
        self.assertTrue('N      -1.17538406    0.34366165    0.03265021' in xyz6_str)
        self.assertEqual(len(xyz7['symbols']), 34)
        expected_xyz_8 = """N      -0.67665958    0.74524340   -0.41319355
H      -1.26179357    1.52577220   -0.13687665
H       0.28392722    1.06723640   -0.44163375
N      -0.75345799   -0.33268278    0.51180786
H      -0.97153041   -0.02416219    1.45398654
H      -1.48669570   -0.95874053    0.20627423
N       2.28178508   -0.42455356    0.14404399
H       1.32677989   -0.80557411    0.33156013"""
        self.assertEqual(xyz8_str, expected_xyz_8)
        expected_xyz_9 = """C       0.00917900   -0.00000000   -0.00000000
O       1.20814900   -0.00000000    0.00000000
H      -0.59436200    0.94730400    0.00000000
H      -0.59436200   -0.94730400    0.00000000"""
        self.assertEqual(xyz9_str, expected_xyz_9)

    def test_parse_t1(self):
        """Test T1 diagnostic parsing"""
        path = os.path.join(arc_path, 'arc', 'testing', 'mehylamine_CCSD(T).out')
        t1 = parser.parse_t1(path)
        self.assertEqual(t1, 0.0086766)

    def test_parse_e_elect(self):
        """Test parsing E0 from an sp job output file"""
        path1 = os.path.join(arc_path, 'arc', 'testing', 'mehylamine_CCSD(T).out')
        e_elect = parser.parse_e_elect(path1)
        self.assertEqual(e_elect, -251377.49160993524)

        path2 = os.path.join(arc_path, 'arc', 'testing', 'SO2OO_CBS-QB3.log')
        e_elect = parser.parse_e_elect(path2, zpe_scale_factor=0.99)
        self.assertEqual(e_elect, -1833127.0939478774)

    def test_parse_zpe(self):
        """Test the parse_zpe() function for parsing zero point energies"""
        path1 = os.path.join(arc_path, 'arc', 'testing', 'C2H6_freq_QChem.out')
        path2 = os.path.join(arc_path, 'arc', 'testing', 'CH2O_freq_molpro.out')
        path3 = os.path.join(arc_path, 'arc', 'testing', 'NO3_freq_QChem_fails_on_cclib.out')
        path4 = os.path.join(arc_path, 'arc', 'testing', 'SO2OO_CBS-QB3.log')
        zpe1, zpe2, zpe3, zpe4 = parser.parse_zpe(path1), parser.parse_zpe(path2), parser.parse_zpe(path3), \
            parser.parse_zpe(path4)
        self.assertAlmostEqual(zpe1, 198.08311200000, 5)
        self.assertAlmostEqual(zpe2, 69.793662734869, 5)
        self.assertAlmostEqual(zpe3, 25.401064000000, 5)
        self.assertAlmostEqual(zpe4, 39.368057626223, 5)

    def test_parse_dipole_moment(self):
        """Test parsing the dipole moment from an opt job output file"""
        path1 = os.path.join(arc_path, 'arc', 'testing', 'SO2OO_CBS-QB3.log')
        dm1 = parser.parse_dipole_moment(path1)
        self.assertEqual(dm1, 0.63)

        path2 = os.path.join(arc_path, 'arc', 'testing', 'N2H4_opt_QChem.out')
        dm2 = parser.parse_dipole_moment(path2)
        self.assertEqual(dm2, 2.0664)

        path3 = os.path.join(arc_path, 'arc', 'testing', 'CH2O_freq_molpro.out')
        dm3 = parser.parse_dipole_moment(path3)
        self.assertAlmostEqual(dm3, 2.8840, 4)

        path4 = os.path.join(arc_path, 'arc', 'testing', 'orca_example_opt.log')
        dm1 = parser.parse_dipole_moment(path4)
        self.assertEqual(dm1, 2.11328)

    def test_parse_polarizability(self):
        """Test parsing the polarizability moment from a freq job output file"""
        path1 = os.path.join(arc_path, 'arc', 'testing', 'SO2OO_CBS-QB3.log')
        polar1 = parser.parse_polarizability(path1)
        self.assertAlmostEqual(polar1, 3.99506, 4)

    def test_process_conformers_file(self):
        """Test processing ARC conformer files"""
        path1 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'conformers_before_optimization.txt')
        path2 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'conformers_after_optimization.txt')
        path3 = os.path.join(arc_path, 'arc', 'testing', 'xyz', 'conformers_file.txt')

        xyzs, energies = parser.process_conformers_file(path1)
        self.assertEqual(len(xyzs), 3)
        self.assertEqual(len(energies), 3)
        self.assertTrue(all([e is None for e in energies]))

        spc1 = ARCSpecies(label='tst1', xyz=xyzs[0])
        self.assertEqual(len(spc1.conformers), 1)

        xyzs, energies = parser.process_conformers_file(path2)
        self.assertEqual(len(xyzs), 3)
        self.assertEqual(len(energies), 3)
        self.assertEqual(energies, [0.0, 10.271, 10.288])

        spc2 = ARCSpecies(label='tst2', xyz=xyzs[:2])
        self.assertEqual(len(spc2.conformers), 2)
        self.assertEqual(len(spc2.conformer_energies), 2)

        xyzs, energies = parser.process_conformers_file(path3)
        self.assertEqual(len(xyzs), 4)
        self.assertEqual(len(energies), 4)
        self.assertEqual(energies, [0.0, 0.005, None, 0.005])

        spc3 = ARCSpecies(label='tst3', xyz=xyzs)
        self.assertEqual(len(spc3.conformers), 4)
        self.assertEqual(len(spc3.conformer_energies), 4)

        spc4 = ARCSpecies(label='tst4', xyz=path1)
        self.assertEqual(len(spc4.conformers), 3)
        self.assertTrue(all([e is None for e in spc4.conformer_energies]))
        spc5 = ARCSpecies(label='tst5', xyz=path2)
        self.assertEqual(len(spc5.conformers), 3)
        self.assertTrue(all([e is not None for e in spc5.conformer_energies]))
        spc6 = ARCSpecies(label='tst6', xyz=path3)
        self.assertEqual(len(spc6.conformers), 4)


if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
