#!/usr/bin/env python3
# encoding: utf-8

"""
This module contains unit tests of the arc.job.trsh module
"""

import os
import unittest

import arc.job.trsh as trsh
from arc.exceptions import SpeciesError
from arc.settings import arc_path, supported_ess


class TestTrsh(unittest.TestCase):
    """
    Contains unit tests for the job.trsh module
    """

    @classmethod
    def setUpClass(cls):
        """
        A method that is run before all unit tests in this class.
        """
        cls.maxDiff = None
        path = os.path.join(arc_path, 'arc', 'testing', 'trsh')
        cls.base_path = {ess: os.path.join(path, ess) for ess in supported_ess}

    def test_determine_ess_status(self):
        """Test the determine_ess_status() function"""

        # Gaussian

        path = os.path.join(self.base_path['gaussian'], 'converged.out')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='OH', job_type='opt')
        self.assertEqual(status, 'done')
        self.assertEqual(keywords, list())
        self.assertEqual(error, '')
        self.assertEqual(line, '')

        path = os.path.join(self.base_path['gaussian'], 'l913.out')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='tst', job_type='composite')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['MaxOptCycles', 'GL913'])
        self.assertEqual(error, 'Maximum optimization cycles reached.')
        self.assertIn('Error termination via Lnk1e', line)
        self.assertIn('g09/l913.exe', line)

        path = os.path.join(self.base_path['gaussian'], 'l301.out')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='Zr2O4H', job_type='opt')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['GL301', 'BasisSet'])
        self.assertEqual(error, 'The basis set 6-311G is not appropriate for the this chemistry.')
        self.assertIn('Error termination via Lnk1e', line)
        self.assertIn('g16/l301.exe', line)

        path = os.path.join(self.base_path['gaussian'], 'l9999.out')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='Zr2O4H', job_type='opt')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['Unconverged', 'GL9999'])
        self.assertEqual(error, 'Unconverged')
        self.assertIn('Error termination via Lnk1e', line)
        self.assertIn('g16/l9999.exe', line)

        path = os.path.join(self.base_path['gaussian'], 'syntax.out')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='Zr2O4H', job_type='opt')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['Syntax'])
        self.assertEqual(error, 'There was a syntax error in the Gaussian input file. Check your Gaussian input '
                                'file template under arc/job/inputs.py. Alternatively, perhaps the level of theory '
                                'is not supported by Gaussian in the format it was given.')
        self.assertFalse(line)

        # QChem

        path = os.path.join(self.base_path['qchem'], 'H2_opt.out')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='H2', job_type='opt')
        self.assertEqual(status, 'done')
        self.assertEqual(keywords, list())
        self.assertEqual(error, '')
        self.assertEqual(line, '')

        # Molpro

        path = os.path.join(self.base_path['molpro'], 'unrecognized_basis_set.out')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='I', job_type='sp')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['BasisSet'])
        self.assertEqual(error, 'Unrecognized basis set 6-311G**')
        self.assertIn(' ? Basis library exhausted', line)  # line includes '\n'

        # Orca

        # test detection of a successful job
        path = os.path.join(self.base_path['orca'], 'orca_successful_sp.log')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='test', job_type='sp', software='orca')
        self.assertEqual(status, 'done')
        self.assertEqual(keywords, list())
        self.assertEqual(error, '')
        self.assertEqual(line, '')

        # test detection of SCF energy diverge issue
        path = os.path.join(self.base_path['orca'], 'orca_scf_blow_up_error.log')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='test', job_type='sp', software='orca')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['SCF'])
        expected_error_msg = 'The SCF energy seems diverged during iterations. ' \
                             'SCF energy after initial iteration is -1076.6615662471. ' \
                             'SCF energy after final iteration is -20006124.677208535. ' \
                             'The ratio between final and initial SCF energy is 18581.627973350558. ' \
                             'This ratio is greater than the default threshold of 2. ' \
                             'Please consider using alternative methods or largerbasis sets.'
        self.assertEqual(error, expected_error_msg)
        self.assertIn('', line)

        # test detection of insufficient memory causes SCF failure
        path = os.path.join(self.base_path['orca'], 'orca_scf_memory_error.log')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='test', job_type='sp', software='orca')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['SCF', 'Memory'])
        expected_error_msg = 'Orca suggests to increase per cpu core memory to 289 MB.'
        self.assertEqual(error, expected_error_msg)
        self.assertEqual(' Error  (ORCA_SCF): Not enough memory available!', line)

        # test detection of insufficient memory causes MDCI failure
        path = os.path.join(self.base_path['orca'], 'orca_mdci_memory_error.log')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='test', job_type='sp', software='orca')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['MDCI', 'Memory'])
        expected_error_msg = 'Orca suggests to increase per cpu core memory to 9718 MB.'
        self.assertEqual(error, expected_error_msg)
        self.assertIn('Please increase MaxCore', line)

        # test detection of too many cpu cores causes MDCI failure
        path = os.path.join(self.base_path['orca'], 'orca_too_many_cores.log')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='test', job_type='sp', software='orca')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['MDCI', 'cpu'])
        expected_error_msg = 'Orca cannot utilize cpu cores more than electron pairs in a molecule. ' \
                             'The maximum number of cpu cores can be used for this job is 10.'
        self.assertEqual(error, expected_error_msg)
        self.assertIn('parallel calculation exceeds', line)

        # test detection of generic MDCI failure
        path = os.path.join(self.base_path['orca'], 'orca_mdci_error.log')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='test', job_type='sp', software='orca')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['MDCI'])
        expected_error_msg = 'MDCI error in Orca.'
        self.assertEqual(error, expected_error_msg)
        self.assertIn('ORCA finished by error termination in MDCI', line)

        # test detection of multiplicty and charge combination error
        path = os.path.join(self.base_path['orca'], 'orca_multiplicity_error.log')
        with self.assertRaises(SpeciesError):
            trsh.determine_ess_status(output_path=path, species_label='test', job_type='sp', software='orca')

        # test detection of input keyword error
        path = os.path.join(self.base_path['orca'], 'orca_input_error.log')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='test', job_type='sp', software='orca')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['Syntax'])
        expected_error_msg = 'There was keyword syntax error in the Orca input file. In particular, keywords ' \
                             'XTB1 can either be duplicated or illegal. Please check your Orca ' \
                             'input file template under arc/job/inputs.py. Alternatively, perhaps the level of ' \
                             'theory or the job option is not supported by Orca in the format it was given.'
        self.assertEqual(error, expected_error_msg)
        self.assertIn('XTB1', line)

        # test detection of basis set error (e.g., input contains elements not supported by specified basis)
        path = os.path.join(self.base_path['orca'], 'orca_basis_error.log')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='test', job_type='sp', software='orca')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['Basis'])
        expected_error_msg = 'There was a basis set error in the Orca input file. In particular, basis for atom type ' \
                             'Br is missing. Please check if specified basis set supports this atom.'
        self.assertEqual(error, expected_error_msg)
        self.assertIn('There are no CABS', line)

        # test detection of wavefunction convergence failure
        path = os.path.join(self.base_path['orca'], 'orca_wavefunction_not_converge_error.log')
        status, keywords, error, line = trsh.determine_ess_status(
            output_path=path, species_label='test', job_type='sp', software='orca')
        self.assertEqual(status, 'errored')
        self.assertEqual(keywords, ['Convergence'])
        expected_error_msg = 'Specified wavefunction method is not converged. Please restart calculation with larger' \
                             'max iterations or with different convergence flags.'
        self.assertEqual(error, expected_error_msg)
        self.assertIn('This wavefunction IS NOT FULLY CONVERGED!', line)

    def test_trsh_ess_job(self):
        """Test the trsh_ess_job() function"""

        #### test gaussian ####
        label = 'ethanol'
        level_of_theory = 'ccsd/vdz'
        server = 'server1'
        job_type = 'opt'
        software = 'gaussian'
        fine = False
        memory_gb = 16
        num_heavy_atoms = 2
        ess_trsh_methods = ['change_node', 'int=(Acc2E=14)']
        cpus = 8

        ## gaussian: test 1 ##
        job_status = {'keywords': ['CheckFile']}
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)

        self.assertTrue(remove_checkfile)
        self.assertEqual(software, 'gaussian')
        self.assertEqual(memory, 16)
        self.assertFalse(couldnt_trsh)

        ## gaussian: test 2 ##
        job_status = {'keywords': ['InternalCoordinateError']}
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)

        self.assertFalse(remove_checkfile)
        self.assertEqual(trsh_keyword, 'opt=(cartesian,nosymm)')

        ## gaussian: test 3 ##
        job_status = {'keywords': ['tmp']}
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)

        self.assertIn('cbs-qb3', ess_trsh_methods)
        self.assertEqual(level_of_theory, 'cbs-qb3')
        self.assertEqual(job_type, 'composite')

        #### test qchem ####
        software = 'qchem'
        ess_trsh_methods = ['change_node']
        job_status = {'keywords': ['MaxOptCycles', 'Unconverged']}
        ## qchem: test 1 ##
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)
        self.assertIn('max_cycles', ess_trsh_methods)

        ## qchem: test 2 ##
        job_status = {'keywords': ['SCF']}
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)
        self.assertIn('DIIS_GDM', ess_trsh_methods)

        #### test molpro ####
        software = 'molpro'

        ## molpro: test ##
        path = os.path.join(self.base_path['molpro'], 'insufficient_memory.out')
        label = 'TS'
        level_of_theory = 'mrci/aug-cc-pV(T+d)Z'
        server = 'server1'
        status, keywords, error, line = trsh.determine_ess_status(output_path=path, species_label='TS', job_type='sp')
        job_status = {'keywords': keywords, 'error': error}
        job_type = 'sp'
        fine = True
        memory_gb = 32.0
        ess_trsh_methods = ['change_node']
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)

        self.assertIn('memory', ess_trsh_methods)
        self.assertAlmostEqual(memory, 222.15625)

        #### test orca ####
        ## orca: test 1 ##
        # Test troubleshooting insufficient memory issue
        # Automatically increase memory provided not exceeding maximum available memory
        label = 'test'
        level_of_theory = 'DLPNO ccsd(T)'
        server = 'server1'
        job_type = 'sp'
        software = 'orca'
        fine = True
        memory_gb = 250
        cpus = 32
        num_heavy_atoms = 20
        ess_trsh_methods = ['memory']
        path = os.path.join(self.base_path['orca'], 'orca_mdci_memory_error.log')
        status, keywords, error, line = trsh.determine_ess_status(output_path=path, species_label='TS', job_type='sp',
                                                                  software=software)
        job_status = {'keywords': keywords, 'error': error}
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)
        self.assertIn('memory', ess_trsh_methods)
        self.assertEqual(cpus, 32)
        self.assertAlmostEqual(memory, 312)

        ## orca: test 2 ##
        # Test troubleshooting insufficient memory issue
        # Automatically reduce cpu cores to ensure enough memory per core when maximum available memory is limited
        label = 'test'
        level_of_theory = 'DLPNO ccsd(T)'
        server = 'server1'
        job_type = 'sp'
        software = 'orca'
        fine = True
        memory_gb = 250
        cpus = 32
        num_heavy_atoms = 20
        ess_trsh_methods = ['memory']
        path = os.path.join(self.base_path['orca'], 'orca_mdci_memory_error.log')
        status, keywords, error, line = trsh.determine_ess_status(output_path=path, species_label='TS', job_type='sp',
                                                                  software=software)
        keywords.append('max_total_job_memory')
        job_status = {'keywords': keywords, 'error': error}
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)
        self.assertIn('memory', ess_trsh_methods)
        self.assertEqual(cpus, 25)
        self.assertAlmostEqual(memory, 245)

        ## orca: test 3 ##
        # Test troubleshooting insufficient memory issue
        # Stop troubleshooting when ARC determined there is not enough computational resource to accomplish the job
        label = 'test'
        level_of_theory = 'DLPNO ccsd(T)'
        server = 'server1'
        job_type = 'sp'
        software = 'orca'
        fine = True
        memory_gb = 1
        cpus = 32
        num_heavy_atoms = 20
        ess_trsh_methods = ['memory']
        path = os.path.join(self.base_path['orca'], 'orca_mdci_memory_error.log')
        status, keywords, error, line = trsh.determine_ess_status(output_path=path, species_label='TS', job_type='sp',
                                                                  software=software)
        keywords.append('max_total_job_memory')
        job_status = {'keywords': keywords, 'error': error}
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)
        self.assertIn('memory', ess_trsh_methods)
        self.assertEqual(couldnt_trsh, True)
        self.assertLess(cpus, 1)    # can't really run job with less than 1 cpu ^o^

        ## orca: test 4 ##
        # Test troubleshooting too many cpu cores
        # Automatically reduce cpu cores
        label = 'test'
        level_of_theory = 'DLPNO ccsd(T)'
        server = 'server1'
        job_type = 'sp'
        software = 'orca'
        fine = True
        memory_gb = 16
        cpus = 16
        num_heavy_atoms = 1
        ess_trsh_methods = ['cpu']
        path = os.path.join(self.base_path['orca'], 'orca_too_many_cores.log')
        status, keywords, error, line = trsh.determine_ess_status(output_path=path, species_label='TS', job_type='sp',
                                                                  software=software)
        job_status = {'keywords': keywords, 'error': error}
        output_errors, ess_trsh_methods, remove_checkfile, level_of_theory, software, job_type, fine, trsh_keyword, \
        memory, shift, cpus, couldnt_trsh = trsh.trsh_ess_job(label, level_of_theory, server, job_status, job_type,
                                                              software, fine, memory_gb, num_heavy_atoms, cpus,
                                                              ess_trsh_methods)
        self.assertIn('cpu', ess_trsh_methods)
        self.assertEqual(cpus, 10)



if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
