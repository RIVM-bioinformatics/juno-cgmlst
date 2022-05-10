import os
import pathlib
from sys import path
import unittest

main_script_path = str(pathlib.Path(pathlib.Path(__file__).parent.absolute()).parent.absolute())
path.insert(0, main_script_path)
from bin import download_cgmlst_scheme


class TestDownloadcgMLSTSchemes(unittest.TestCase):

    def setUpClass():
        os.system('mkdir -p test_output')

    def tearDownClass():
        os.system('rm -rf test_output')

    def test_output_dir_is_removed_if_download_is_false(self):
        """Testing there is no error if output dir does not exist and that
        it is created then
        """

        os.system('rm -rf test_output')
        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['salmonella'],
                                                        output_dir='test_output',
                                                        threads=2,
                                                        download_loci=False)
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'salmonella')
        self.assertFalse(dir_with_downloaded_scheme.is_dir())
        self.assertFalse(pathlib.Path('test_output').is_dir())
        

    def test_output_dir_is_not_removed_if_not_empty(self):
        """Testing there is no error if output dir does not exist and that
        it is created then
        """

        os.system('touch test_output/file.txt')
        os.mkdir('test_output/salmonella')
        os.system('touch test_output/salmonella/file.txt')
        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['salmonella'],
                                                        output_dir='test_output',
                                                        threads=2,
                                                        download_loci=False)
        self.assertTrue(pathlib.Path('test_output').is_dir())
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'salmonella')
        self.assertTrue(dir_with_downloaded_scheme.is_dir())

    def test_salmonella_and_shigella_cgMLSTschemes(self):
        """The Salmonella and Shigella schemes should be properly
        found from Enterobase
        """

        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['salmonella', 'shigella'],
                                                        output_dir='test_output',
                                                        threads=2,
                                                        download_loci=False)
        expected_result = {'salmonella': \
                            {'source': 'enterobase',
                            'url': 'http://enterobase.warwick.ac.uk/schemes/Salmonella.cgMLSTv2/',
                            'locus_count': 3002,
                            'scheme_description': None},
                        'shigella': \
                            {'source': 'enterobase',
                            'url': 'http://enterobase.warwick.ac.uk/schemes/Escherichia.cgMLSTv1/',
                            'locus_count': 2513,
                            'scheme_description': None}}
        self.assertEqual(len(cgMLSTschemes_result.schemes), 2)
        self.assertTrue('salmonella' in cgMLSTschemes_result.schemes)
        self.assertTrue('shigella' in cgMLSTschemes_result.schemes)
        self.assertEqual(cgMLSTschemes_result.schemes, expected_result)
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'salmonella')
        self.assertFalse(dir_with_downloaded_scheme.is_dir())
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'shigella')
        self.assertFalse(dir_with_downloaded_scheme.is_dir())

    def test_escherichia_cgMLSTschemes(self):
        """Escherichia should download 2 schemes: the default seqsphere and 
        the optional enterobase one (shared with shigella)
        """

        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['escherichia'],
                                                        output_dir='test_output',
                                                        threads=2,
                                                        download_loci=False)
        expected_result = {'escherichia': \
                            {'source': 'seqsphere',
                            'url': 'https://www.cgmlst.org/ncs/schema/5064703/locus/',
                            'locus_count': 2513,
                            'scheme_description': None},
                        'shigella': \
                            {'source': 'enterobase',
                            'url': 'http://enterobase.warwick.ac.uk/schemes/Escherichia.cgMLSTv1/',
                            'locus_count': 2513,
                            'scheme_description': None}}
        self.assertEqual(len(cgMLSTschemes_result.schemes), 2)
        self.assertTrue('escherichia' in cgMLSTschemes_result.schemes)
        self.assertTrue('shigella' in cgMLSTschemes_result.schemes)
        self.assertEqual(cgMLSTschemes_result.schemes, expected_result)
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'escherichia')
        self.assertFalse(dir_with_downloaded_scheme.is_dir())
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'shigella')
        self.assertFalse(dir_with_downloaded_scheme.is_dir())

    def test_listeria_cgMLSTschemes(self):
        """Listeria should download 2 schemes: the default seqsphere and 
        the optional from BigsDB Pasteur.
        """

        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['listeria'],
                                                        output_dir='test_output',
                                                        threads=2,
                                                        download_loci=False)
        expected_result = {'listeria': \
                            {'source': 'seqsphere',
                            'url': 'https://www.cgmlst.org/ncs/schema/690488/locus/',
                            'locus_count': 1701,
                            'scheme_description': None},
                        'listeria_optional': \
                            {'source': 'bigsdb_pasteur',
                            'url': 'https://bigsdb.pasteur.fr/api/db/pubmlst_listeria_seqdef/schemes/3',
                            'locus_count': 1748,
                            'scheme_description': 'cgMLST1748'}}
        self.assertEqual(len(cgMLSTschemes_result.schemes), 2)
        self.assertTrue('listeria' in cgMLSTschemes_result.schemes)
        self.assertTrue('listeria_optional' in cgMLSTschemes_result.schemes)
        self.assertEqual(cgMLSTschemes_result.schemes, expected_result)
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'listeria')
        self.assertFalse(dir_with_downloaded_scheme.is_dir())
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'listeria_optional')
        self.assertFalse(dir_with_downloaded_scheme.is_dir())

    def test_warning_when_some_species_not_supported_for_cgMLST(self):
        """If at least one of the species/genera provided for downloading the
        cgMLST scheme is not supported (not on the list of downloadable
        schemes) then a warning should be thrown
        """

        self.assertWarnsRegex(UserWarning, 'not supported', 
                                download_cgmlst_scheme.cgMLSTSchemes, 
                                ['salmonella', 'no_real_species'], 
                                output_dir='output', threads=2,
                                download_loci=False)
    
    def test_error_when_none_of_listed_species_are_supported(self):
        """If none of the species/genera provided for downloading the 
        cgMLST scheme is supported (none of them is on the list of 
        downloadable schemes) then an error should be thrown
        """

        self.assertRaisesRegex(ValueError, 
                                'None of the provided genera is supported for cgMLST', 
                                download_cgmlst_scheme.cgMLSTSchemes, 
                                ['no_real_species'], 
                                output_dir='output', threads=2,
                                download_loci=False)

    def test_genus_given_in_capital_letters(self):
        """The Salmonella scheme should be found even if the genus name
        is given in small letters (no first capital)
        """

        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['SALMONELLA'],
                                                        output_dir='test_output',
                                                        threads=2,
                                                        download_loci=False)
        expected_result = {'salmonella': \
                            {'source': 'enterobase',
                            'url': 'http://enterobase.warwick.ac.uk/schemes/Salmonella.cgMLSTv2/',
                            'locus_count': 3002,
                            'scheme_description': None}}
        self.assertEqual(len(cgMLSTschemes_result.schemes), 1)
        self.assertTrue('salmonella' in cgMLSTschemes_result.schemes)
        self.assertEqual(cgMLSTschemes_result.schemes, expected_result)

    def test_genus_given_in_firstcapital_letter(self):
        """The Salmonella scheme should be found even if the genus name
        is given in all capital letters (no first capital and other small)
        """

        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['Salmonella'],
                                                        output_dir='test_output',
                                                        threads=2,
                                                        download_loci=False)
        expected_result = {'salmonella': \
                            {'source': 'enterobase',
                            'url': 'http://enterobase.warwick.ac.uk/schemes/Salmonella.cgMLSTv2/',
                            'locus_count': 3002,
                            'scheme_description': None}}
        self.assertTrue(len(cgMLSTschemes_result.schemes) == 1)
        self.assertTrue('salmonella' in cgMLSTschemes_result.schemes)
        self.assertEqual(cgMLSTschemes_result.schemes, expected_result)

    def test_pubmlst_scheme_is_properly_downloaded(self):
        """A test subfolder should be created and a fasta files per locus
        should be downloaded
        """

        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['test_pubmlst'],
                                                        output_dir='test_output',
                                                        threads=1,
                                                        download_loci=True)
        expected_result = {'test_pubmlst': \
                            {'source': 'pubmlst',
                            'url': 'https://rest.pubmlst.org/db/pubmlst_salmonella_seqdef/schemes/2',
                            'locus_count': 7,
                            'scheme_description': 'MLST'}}
        self.assertTrue(len(cgMLSTschemes_result.schemes) == 1)
        self.assertTrue('test_pubmlst' in cgMLSTschemes_result.schemes)
        self.assertEqual(cgMLSTschemes_result.schemes, expected_result)
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'test_pubmlst')
        self.assertTrue(dir_with_downloaded_scheme.is_dir())
        files_in_downloaded_scheme = os.listdir(dir_with_downloaded_scheme)
        fasta_files_in_downloaded_scheme = [file_ for file_ in files_in_downloaded_scheme if str(file_).endswith('.fasta')]
        len(fasta_files_in_downloaded_scheme)
        self.assertEqual(len(fasta_files_in_downloaded_scheme), expected_result['test_pubmlst']['locus_count'])

    def test_bigsdb_pasteur_scheme_is_properly_downloaded(self):
        """A test subfolder should be created and a fasta files per locus
        should be downloaded
        """

        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['test_bigsdb_pasteur'],
                                                        output_dir='test_output',
                                                        threads=1,
                                                        download_loci=True)
        expected_result = {'test_bigsdb_pasteur': \
                            {'source': 'bigsdb_pasteur',
                            'url': 'https://bigsdb.pasteur.fr/api/db/pubmlst_listeria_seqdef/schemes/2',
                            'locus_count': 7,
                            'scheme_description': 'MLST'}}
        self.assertTrue(len(cgMLSTschemes_result.schemes) == 1)
        self.assertTrue('test_bigsdb_pasteur' in cgMLSTschemes_result.schemes)
        self.assertEqual(cgMLSTschemes_result.schemes, expected_result)
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'test_bigsdb_pasteur')
        self.assertTrue(dir_with_downloaded_scheme.is_dir())
        files_in_downloaded_scheme = os.listdir(dir_with_downloaded_scheme)
        fasta_files_in_downloaded_scheme = [file_ for file_ in files_in_downloaded_scheme if str(file_).endswith('.fasta')]
        len(fasta_files_in_downloaded_scheme)
        self.assertEqual(len(fasta_files_in_downloaded_scheme), expected_result['test_bigsdb_pasteur']['locus_count'])

    def test_enterobase_scheme_is_properly_downloaded(self):
        """A test subfolder should be created and a fasta files per locus
        should be downloaded
        """

        cgMLSTschemes_result = download_cgmlst_scheme.cgMLSTSchemes(['test_enterobase'],
                                                        output_dir='test_output',
                                                        threads=1,
                                                        download_loci=True)
        expected_result = {'test_enterobase': \
                            {'source': 'enterobase',
                            'url': 'https://enterobase.warwick.ac.uk/schemes/Yersinia.Achtman7GeneMLST/',
                            'locus_count': 7,
                            'scheme_description': None}}
        self.assertTrue(len(cgMLSTschemes_result.schemes) == 1)
        self.assertTrue('test_enterobase' in cgMLSTschemes_result.schemes)
        self.assertEqual(cgMLSTschemes_result.schemes, expected_result)
        dir_with_downloaded_scheme = pathlib.Path('test_output', 'test_enterobase')
        self.assertTrue(dir_with_downloaded_scheme.is_dir())
        files_in_downloaded_scheme = os.listdir(dir_with_downloaded_scheme)
        fasta_files_in_downloaded_scheme = [file_ for file_ in files_in_downloaded_scheme if str(file_).endswith('.fasta')]
        len(fasta_files_in_downloaded_scheme)
        self.assertEqual(len(fasta_files_in_downloaded_scheme), expected_result['test_enterobase']['locus_count'])



if __name__ == '__main__':
	unittest.main()