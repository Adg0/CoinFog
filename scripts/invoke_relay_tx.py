import os
import sys
import base64
import pickle
from dotenv import load_dotenv
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.future.transaction import *
from pyteal import compileTeal, Mode
from utils import *

load_dotenv("./.env")
p = os.environ.get("PROJECT_PATH")
sys.path.insert(0,p)

from assets.relay_lsig import *

# create delegation
def create_lsig(algod_client, private_key, app_index):
    with open("./artifacts/relay_auth.lsig", "wb") as f:
        compiled = compileTeal(relay_auth(), Mode.Signature, version=6)
        response = algod_client.compile(compiled)

        # Create logic sig
        programstr = response['result']
        t = programstr.encode("ascii")
        program = base64.decodebytes(t)

        arg1 = (app_index).to_bytes(8, 'big')
        lsig = LogicSigAccount(program, args=[arg1])
        lsig.sign(private_key)

        pickle.dump(lsig, f, pickle.HIGHEST_PROTOCOL)

def withdraw_with_lsig(client, lsig, index, app_args, boxes, accounts):
    # declare sender
    sender = lsig.address()
    print("Call from account:", sender)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = ApplicationNoOpTxn(sender=sender, sp=params, index=index, accounts=accounts, app_args=app_args, boxes=boxes)

    # sign transaction
    lstx = LogicSigTransaction(txn, lsig)

    drr = create_dryrun(client, [lstx])
    filename = "dryrun.msgp"
    with open(filename, "wb") as f:
        f.write(base64.b64decode(encoding.msgpack_encode(drr)))

    # send transaction
    tx_id = client.send_transaction(lstx)

    # await confirmation
    wait_for_confirmation(client, tx_id)

def main():
    # Initialize an algod client
    algod_client = algod.AlgodClient(algod_token=algod_token, algod_address=algod_address)
    accounts = generate_accounts(1)
    #accounts_ = generate_accounts(1)
    #fund_accounts(algod_client, sk, accounts_, 1000000)
    #create_lsig(algod_client, accounts_[1]['sk'], app_id)

    amount = 5000000
    nullifier = "30405060"
    secret = "passKeys"
    with open('./artifacts/relay_auth.lsig', 'rb') as f:
        lsig = pickle.load(f)
        withdraw_with_lsig(algod_client, lsig, app_id, [b"withdraw",secret.encode('utf-8'),nullifier.encode('utf-8'),accounts[1]['pk'].encode('utf-8')],[[0,"5algo"],[0,"NF"],[0,""]], [accounts[1]['pk']])


if __name__ == "__main__":
    main()
