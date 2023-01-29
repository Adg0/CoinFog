from pyteal import *

""" 
Relay Delegation: for anonymising mixer deposit withdrawal

    This contract allows anyone to sign an application call.
    Provide Arg(0) with an application, thus to restrict random app call.

"""

def relay_auth():
    safety_cond  = Txn.rekey_to() == Global.zero_address()
    fee_cond = Txn.fee() <= Global.min_txn_fee()
    app_cond = And(Txn.type_enum() == TxnType.ApplicationCall, Txn.on_completion() == OnComplete.NoOp)
    restrict_app = Txn.application_id() == Btoi(Arg(0))

    program = And(safety_cond, fee_cond, app_cond, restrict_app)

    return program

if __name__ == "__main__":
    with open("./artifacts/relay_auth.teal", "w") as f:
        compiled = compileTeal(relay_auth(), Mode.Signature, version=6)
        f.write(compiled)
