import os
import base64
from dotenv import load_dotenv
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.future.transaction import *
from pyteal import compileTeal, Mode

load_dotenv("./.env")

m = os.environ.get("MNEMONIC") # This is YOUR address. Make sure it is funded with atleast 4Algo.
sk = mnemonic.to_private_key(m)
pk = account.address_from_private_key(sk)
app_id = 156345278 #395

# Node address and token.
algod_address = "https://testnet-api.algonode.cloud" #"http://localhost:4001" 
algod_token = "" #"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

# Generating testing accounts
def generate_accounts(number_of_accounts):
    mn = []
    for i in range(number_of_accounts):
        acct = account.generate_account()
        mn.append(mnemonic.from_private_key(acct[0]))

    accounts = {}
    counter = 1
    for m in mn:
        accounts[counter] = {}
        accounts[counter]['sk'] = mnemonic.to_private_key(m)
        accounts[counter]['pk'] = account.address_from_private_key(accounts[counter]['sk'])
        print("Account {} address: {}".format(counter, accounts[counter]['pk']))
        counter += 1

    return accounts

# Funding the Test adresses
def fund_accounts(algod_client, private_key, accounts, amount):
    params = algod_client.suggested_params()
    sender = account.address_from_private_key(private_key)

    # create transactions
    txns = []
    stxn = []
    for i in accounts:
        txns.append(PaymentTxn(sender, params, accounts[i]['pk'], amount))

    # compute group id and put it into each transaction
    group_id = calculate_group_id(txns)

    for i in accounts:
        txns[i-1].group = group_id
        # sign transactions
        stxn.append(txns[i-1].sign(private_key))

    # send transactions
    txid = algod_client.send_transactions(stxn)

    # wait for confirmation	
    wait_for_confirmation(algod_client, txid)

    for i in accounts:
        # get balance
        account_info = algod_client.account_info(accounts[i]['pk'])
        print("{}: {} microAlgos".format(accounts[i]['pk'], account_info.get('amount')))

