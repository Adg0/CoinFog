import base64
from algosdk import account, mnemonic, logic, constants
from algosdk.v2client import algod
from algosdk.future.transaction import *
from utils import *

# take profit function
def take_profit(client, private_key, index, app_args):
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()
    params.fee = 2 * constants.min_txn_fee

    # create unsigned transaction
    txn = ApplicationNoOpTxn(sender=sender, sp=params, index=index, app_args=app_args)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    drr = create_dryrun(client, [signed_txn])
    filename = "dryrun.msgp"
    with open(filename, "wb") as f:
        f.write(base64.b64decode(encoding.msgpack_encode(drr)))

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

def main():
    # Initialize an algod client
    algod_client = algod.AlgodClient(algod_token=algod_token, algod_address=algod_address)
    take_profit(algod_client, sk, app_id, [b"profit"])
    print("Successfully withdrew profit")

if __name__ == "__main__":
    main()
