import unittest
import log_analyzer
import unittest.mock as mock

class LogAnalyzer(unittest.TestCase):

    def testParseLogMessage(self):
        testurl, testtime, testerrors = log_analyzer.parse_log_massage(
            '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390')
        self.assertEqual(testurl,
                        '/api/v2/banner/25019354')
        self.assertEqual(testtime,
                        0.390)
        self.assertFalse(testerrors)
    
    def testGetConfig(self):
        testconfig = log_analyzer.get_config("tests/config")
        self.assertEqual(testconfig['REPORT_SIZE'],
                         '1000')
        self.assertEqual(testconfig['LOG_DIR'],
                        './log')
    
    def testGetLogFiles(self):
        test_files = []
        os_listdir=mock.MagicMock(return_value=[
                                 'test',
                                 'nginx-access-ui.log-20170630.gz',
                                 'nginx-access-ui.log-20170629'
                                 ])
        os_path_isfile=mock.MagicMock(return_value=True)
        with mock.patch("os.listdir", os_listdir):
             with mock.patch("os.path.isfile", os_path_isfile):
                 for i in log_analyzer.get_log_files("."):
                    test_files.append(i)
        self.assertEqual(len(test_files),
                         2)
    
            

if __name__ == '__main__':
    unittest.main()