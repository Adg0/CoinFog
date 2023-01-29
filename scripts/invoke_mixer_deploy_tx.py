import os
import sys
import json
import base64
from dotenv import load_dotenv
from algosdk import account, mnemonic, logic
from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk.future.transaction import *
from pyteal import compileTeal, Mode
from utils import *

load_dotenv("./.env")
p = os.environ.get("PROJECT_PATH")
sys.path.insert(0,p)

from assets.mixer import approval_program, clear_state_program

# helper function to compile program source
def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response["result"])

# create new application
def create_app(
    client,
    private_key,
    approval_program,
    clear_program,
    global_schema,
    local_schema,
    app_args,
):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = ApplicationCreateTxn(
        sender,
        params,
        on_complete,
        approval_program,
        clear_program,
        global_schema,
        local_schema,
        app_args,
    )

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

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response["application-index"]
    print("Created new app-id:", app_id)

    return app_id

def fund_app(client, private_key, index, amount):
    # define sender as creator
    sender = account.address_from_private_key(private_key)
    # get application address
    app_addr = logic.get_application_address(index)

    # get node suggested parameters
    params = client.suggested_params()

    txn = PaymentTxn(sender, params, app_addr, amount)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    return tx_id

def update_mixer(client, private_key, index, approval_program, clear_program):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = ApplicationUpdateTxn(
        sender=sender,
        sp=params,
        index=index,
        approval_program=approval_program,
        clear_program=clear_program
    )

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

    local_ints = 0
    local_bytes = 0
    global_ints = 2
    global_bytes = 2
    global_schema = StateSchema(global_ints, global_bytes)
    local_schema = StateSchema(local_ints, local_bytes)

    # get PyTeal approval program
    approval_program_ast = approval_program()
    # compile program to TEAL assembly
    approval_program_teal = compileTeal(
        approval_program_ast, mode=Mode.Application, version=8
    )
    # compile program to binary
    approval_program_compiled = compile_program(algod_client, approval_program_teal)

    # get PyTeal clear state program
    clear_state_program_ast = clear_state_program()
    # compile program to TEAL assembly
    clear_state_program_teal = compileTeal(
        clear_state_program_ast, mode=Mode.Application, version=8
    )
    # compile program to binary
    clear_state_program_compiled = compile_program(
        algod_client, clear_state_program_teal
    )

    # create list of bytes for app args
    app_args = []

    """
    app_id = create_app(
        algod_client,
        sk,
        approval_program_compiled,
        clear_state_program_compiled,
        global_schema,
        local_schema,
        app_args,
    )

    print(app_id)

    tx_id = fund_app(algod_client, sk, app_id, 2000000)
    print("confirmed: {}".format(tx_id))
    """

    # update application 
    update_mixer(algod_client, sk, app_id, approval_program_compiled, clear_state_program_compiled)


if __name__ == "__main__":
    main()
