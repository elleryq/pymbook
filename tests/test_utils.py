from nose.tools import *
from pymbooklib import utils

def test_utils_find_pdbs():
    assert_true( len(utils.find_pdbs( "." ))>=0 )
