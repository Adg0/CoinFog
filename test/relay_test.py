from assets.relay_lsig import *
from scripts.invoke_relay_tx import *
from algosdk.future import transaction
from algosdk import account, mnemonic
from algosdk.v2client import algod, indexer
from dotenv import load_dotenv
import os
import unittest

# Security(protecting private key)
load_dotenv("./.env")

algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
indexer_address = "http://localhost:8980"

# user declared account mnemonics
funding_mnemonic = os.environ.get("MNEMONIC") # This is YOUR address. Make sure it is funded with atleast 4Algo.

unittest.TestLoader.sortTestMethodsUsing = None

class TestRelay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.algod_client = algod.AlgodClient(algod_token, algod_address)
        cls.algod_indexer = indexer.IndexerClient("", indexer_address)
    def test_relay(self):

